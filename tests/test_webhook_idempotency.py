from sqlalchemy import UniqueConstraint

from app.models import WebhookEvent
from app.services import webhooks as webhooks_service

from .test_webhooks import URL, _events


def test_webhook_event_table_has_compound_unique_constraint():
    constraints = [c for c in WebhookEvent.__table__.constraints if isinstance(c, UniqueConstraint)]
    assert len(constraints) == 1
    constraint = constraints[0]
    assert constraint.name == "uq_webhook_event_call_id_idempotency_key"
    assert {col.name for col in constraint.columns} == {"call_id", "idempotency_key"}


def test_same_call_id_different_idempotency_keys_both_stored(client):
    payload_a = {"message": {"idempotencyKey": "key-a", "call": {"id": "call_shared", "status": "completed"}}}
    payload_b = {"message": {"idempotencyKey": "key-b", "call": {"id": "call_shared", "status": "completed"}}}

    r1 = client.post(URL, json=payload_a)
    r2 = client.post(URL, json=payload_b)

    assert r1.json()["duplicate"] is False
    assert r2.json()["duplicate"] is False
    assert len(_events(call_id="call_shared")) == 2


def test_same_idempotency_key_different_call_ids_both_stored(client):
    payload_x = {"message": {"idempotencyKey": "shared-key", "call": {"id": "call_x", "status": "completed"}}}
    payload_y = {"message": {"idempotencyKey": "shared-key", "call": {"id": "call_y", "status": "completed"}}}

    r1 = client.post(URL, json=payload_x)
    r2 = client.post(URL, json=payload_y)

    assert r1.json()["duplicate"] is False
    assert r2.json()["duplicate"] is False
    assert len(_events(idempotency_key="shared-key")) == 2


def test_identical_pair_stored_only_once(client):
    payload = {"message": {"idempotencyKey": "evt-exact", "call": {"id": "call_exact", "status": "completed"}}}

    r1 = client.post(URL, json=payload)
    r2 = client.post(URL, json=payload)

    assert r1.json()["duplicate"] is False
    assert r2.json()["duplicate"] is True
    assert len(_events(call_id="call_exact", idempotency_key="evt-exact")) == 1


def test_integrity_error_from_concurrent_delivery_returns_duplicate_not_500(client, monkeypatch):
    # simulate the race: an event with this exact pair already exists, but
    # the fast-path lookup is patched to miss on its first call (as if two
    # deliveries both passed the pre-insert check before either committed).
    from app.database import SessionLocal

    setup_db = SessionLocal()
    setup_db.add(WebhookEvent(call_id="call_race", idempotency_key="evt_race", status="completed"))
    setup_db.commit()
    setup_db.close()

    real_find_existing = webhooks_service._find_existing
    calls = {"n": 0}

    def flaky_find_existing(db, call_id, idempotency_key):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return real_find_existing(db, call_id, idempotency_key)

    monkeypatch.setattr(webhooks_service, "_find_existing", flaky_find_existing)

    r = client.post(
        URL,
        json={"message": {"idempotencyKey": "evt_race", "call": {"id": "call_race", "status": "completed"}}},
    )

    assert r.status_code == 200
    assert r.json() == {"received": True, "duplicate": True}
    assert len(_events(call_id="call_race", idempotency_key="evt_race")) == 1
