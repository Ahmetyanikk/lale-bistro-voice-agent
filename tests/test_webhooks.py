from app.database import SessionLocal
from app.models import WebhookEvent

URL = "/api/webhooks/olovoice/end-of-call"


def _events(**filters) -> list[WebhookEvent]:
    db = SessionLocal()
    try:
        q = db.query(WebhookEvent)
        for key, value in filters.items():
            q = q.filter(getattr(WebhookEvent, key) == value)
        return q.all()
    finally:
        db.close()


def _official_payload(**message_overrides) -> dict:
    """The officially documented end-of-call-report shape."""
    message = {
        "type": "end-of-call-report",
        "timestamp": 1712345678901,
        "idempotencyKey": "evt-official-1",
        "endedReason": "call.ended",
        "call": {
            "id": "call_abc123",
            "status": "completed",
            "startedAt": "2026-07-07T10:00:00Z",
            "endedAt": "2026-07-07T10:02:14Z",
        },
        "analysis": {"summary": "Guest booked a table for 4."},
        "analysisStatus": "completed",
    }
    message.update(message_overrides)
    return {"message": message}


def test_valid_documented_payload_is_stored_with_correct_field_mapping(client):
    r = client.post(URL, json=_official_payload())
    assert r.status_code == 200
    assert r.json() == {"received": True, "duplicate": False}

    [event] = _events(call_id="call_abc123", idempotency_key="evt-official-1")
    assert event.status == "completed"
    assert event.ended_reason == "call.ended"
    assert event.analysis_status == "completed"
    assert event.summary == "Guest booked a table for 4."
    assert event.started_at is not None
    assert event.ended_at is not None
    assert event.structured_outputs == []


def test_duplicate_delivery_is_not_stored_twice(client):
    payload = _official_payload(idempotencyKey="evt-dup-1")
    payload["message"]["call"]["id"] = "call_dup_1"

    r1 = client.post(URL, json=payload)
    r2 = client.post(URL, json=payload)

    assert r1.json() == {"received": True, "duplicate": False}
    assert r2.json() == {"received": True, "duplicate": True}
    assert len(_events(call_id="call_dup_1", idempotency_key="evt-dup-1")) == 1


def test_null_structured_outputs_normalizes_to_empty_list(client):
    payload = _official_payload(idempotencyKey="evt-null-so")
    payload["message"]["call"]["id"] = "call_null_so"
    payload["message"]["call"]["structuredOutputs"] = None

    r = client.post(URL, json=payload)
    assert r.status_code == 200

    [event] = _events(call_id="call_null_so")
    assert event.structured_outputs == []


def test_successful_structured_output_is_stored(client):
    payload = _official_payload(idempotencyKey="evt-success-so")
    payload["message"]["call"]["id"] = "call_success_so"
    payload["message"]["call"]["structuredOutputs"] = [
        {"name": "reservation_summary", "status": "success", "result": {"party_size": 4}}
    ]

    r = client.post(URL, json=payload)
    assert r.status_code == 200

    [event] = _events(call_id="call_success_so")
    assert event.structured_outputs == [
        {"name": "reservation_summary", "status": "success", "result": {"party_size": 4}}
    ]


def test_failed_structured_output_is_ignored(client):
    payload = _official_payload(idempotencyKey="evt-mixed-so")
    payload["message"]["call"]["id"] = "call_mixed_so"
    payload["message"]["call"]["structuredOutputs"] = [
        {"name": "bad", "status": "failed", "result": {"oops": True}},
        {"name": "good", "status": "success", "result": {"ok": True}},
    ]

    r = client.post(URL, json=payload)
    assert r.status_code == 200

    [event] = _events(call_id="call_mixed_so")
    assert event.structured_outputs == [{"name": "good", "status": "success", "result": {"ok": True}}]


def test_message_level_structured_outputs_fallback_is_used(client):
    payload = _official_payload(idempotencyKey="evt-fallback-so")
    payload["message"]["call"]["id"] = "call_fallback_so"
    # no structuredOutputs under call at all — only the message-level fallback
    payload["message"]["structuredOutputs"] = [{"name": "top_level", "status": "success", "result": {}}]

    r = client.post(URL, json=payload)
    assert r.status_code == 200

    [event] = _events(call_id="call_fallback_so")
    assert event.structured_outputs == [{"name": "top_level", "status": "success", "result": {}}]


def test_unknown_future_fields_do_not_break_parsing(client):
    payload = _official_payload(idempotencyKey="evt-future-fields")
    payload["message"]["call"]["id"] = "call_future_fields"
    payload["message"]["call"]["someNewCallField"] = {"nested": True}
    payload["message"]["someNewMessageField"] = "surprise"
    payload["webhookSchemaVersion"] = 2  # unknown top-level field too

    r = client.post(URL, json=payload)
    assert r.status_code == 200
    assert r.json() == {"received": True, "duplicate": False}


def test_missing_message_and_call_identity_handled_safely(client):
    r = client.post(URL, json={})
    assert r.status_code == 200
    assert r.json()["received"] is True

    r2 = client.post(URL, json={"message": {"analysis": {"summary": "no call object at all"}}})
    assert r2.status_code == 200
    [event] = _events(summary="no call object at all")
    assert event.call_id is None
    assert event.idempotency_key is None
    assert event.structured_outputs == []
