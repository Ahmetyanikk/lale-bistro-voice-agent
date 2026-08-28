from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import WebhookEvent

# Official OloVoice end-of-call-report shape:
#
# {
#   "message": {
#     "type": "end-of-call-report",
#     "timestamp": 1712345678901,
#     "idempotencyKey": "...",
#     "endedReason": "call.ended",
#     "call": {
#       "id": "call_abc123",
#       "status": "completed",
#       "startedAt": "2026-07-07T10:00:00Z",
#       "endedAt": "2026-07-07T10:02:14Z",
#       "structuredOutputs": [{"name": ..., "status": "success"|..., "result": {...}}] | null
#     },
#     "analysis": {"summary": "..."},
#     "analysisStatus": "completed",
#     "structuredOutputs": [...] | null   # defensive fallback location only
#   }
# }
#
# This handler is analytics-only and non-authoritative: nothing it stores is
# verified against OloVoice. A privileged production action (e.g. touching a
# reservation) would first re-fetch and verify message.call.id through the
# OloVoice Call Logs API — never act on webhook content directly. OloVoice's
# docs don't define a webhook signature scheme, so none is assumed or
# invented here.


def _get_dict(source: dict, key: str) -> dict:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def _safe_str(value: Any, max_len: int) -> str | None:
    return value[:max_len] if isinstance(value, str) else None


def _safe_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _successful_structured_outputs(message: dict, call: dict) -> list:
    # call mirrors the call-log record, so it's the preferred location;
    # message.structuredOutputs is a defensive fallback only.
    raw = call.get("structuredOutputs")
    if raw is None:
        raw = message.get("structuredOutputs")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict) and item.get("status") == "success"]


def _find_existing(db: Session, call_id: str | None, idempotency_key: str | None):
    if call_id is None and idempotency_key is None:
        return None
    return db.execute(
        select(WebhookEvent.id).where(
            WebhookEvent.call_id == call_id,
            WebhookEvent.idempotency_key == idempotency_key,
        )
    ).first()


def record_end_of_call(db: Session, payload: dict) -> bool:
    """Store an end-of-call event defensively — every field extraction
    tolerates the wrong type or a missing key instead of raising, since the
    payload comes from an external platform we don't control.

    Returns True when this (call_id, idempotency_key) pair was already
    seen (duplicate, nothing re-stored), False when a new row was written.

    The pre-insert lookup is a fast path, not the correctness guarantee —
    two concurrent deliveries of the same pair can both pass it before
    either commits. The DB's compound unique constraint is what actually
    prevents the duplicate row; IntegrityError from that race is caught
    below and turned into the same duplicate=True response, never a 500.
    """
    message = _get_dict(payload, "message")
    call = _get_dict(message, "call")
    analysis = _get_dict(message, "analysis")

    call_id = _safe_str(call.get("id"), 100)
    idempotency_key = _safe_str(message.get("idempotencyKey"), 100)

    if _find_existing(db, call_id, idempotency_key) is not None:
        return True

    event = WebhookEvent(
        idempotency_key=idempotency_key,
        call_id=call_id,
        status=_safe_str(call.get("status"), 40),
        ended_reason=_safe_str(message.get("endedReason"), 100),
        started_at=_safe_datetime(call.get("startedAt")),
        ended_at=_safe_datetime(call.get("endedAt")),
        analysis_status=_safe_str(message.get("analysisStatus"), 40),
        summary=_safe_str(analysis.get("summary"), 2000),
        structured_outputs=_successful_structured_outputs(message, call),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if _find_existing(db, call_id, idempotency_key) is not None:
            return True
        raise
    return False
