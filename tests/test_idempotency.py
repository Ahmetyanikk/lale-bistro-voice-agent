from .timehelpers import next_open_datetime


def test_idempotent_create_returns_same_reservation(client, headers):
    dt = next_open_datetime(hour=15)
    payload = {
        "tool_call_id": "idem-1",
        "customer_name": "Zeynep",
        "phone": "05336667788",
        "party_size": 2,
        "requested_time": dt.isoformat(),
    }
    r1 = client.post("/api/tools/create-reservation", json=payload, headers=headers).json()
    r2 = client.post("/api/tools/create-reservation", json=payload, headers=headers).json()
    assert r1["confirmation_code"] == r2["confirmation_code"]
    assert r1["status"] == r2["status"] == "confirmed"


def test_idempotent_create_does_not_duplicate_the_reservation(client, headers):
    # party_size=8 only fits the single 8-top: if the repeat call created a
    # second real reservation, a third distinct tool_call_id for the same
    # slot would still find the table "free" — it must not.
    dt = next_open_datetime(hour=16)
    payload = {
        "tool_call_id": "idem-2",
        "customer_name": "Cem",
        "phone": "05334445566",
        "party_size": 8,
        "requested_time": dt.isoformat(),
    }
    r1 = client.post("/api/tools/create-reservation", json=payload, headers=headers).json()
    r2 = client.post("/api/tools/create-reservation", json=payload, headers=headers).json()
    assert r1["confirmation_code"] == r2["confirmation_code"]
    assert r1["table_label"] == r2["table_label"]

    r3 = client.post(
        "/api/tools/create-reservation",
        json={**payload, "tool_call_id": "idem-2-other"},
        headers=headers,
    ).json()
    assert r3["status"] == "rejected"
    assert r3["reason"] == "no_availability"
