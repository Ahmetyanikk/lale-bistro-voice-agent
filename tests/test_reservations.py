from datetime import timedelta

from app.services.codes import CODE_ALPHABET

from .timehelpers import next_open_datetime


def test_successful_reservation(client, headers):
    dt = next_open_datetime(hour=19, minute=30)
    r = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-1",
            "customer_name": "Ayse Yilmaz",
            "phone": "0532 123 45 67",
            "party_size": 4,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "confirmed"
    assert len(body["confirmation_code"]) == 4
    assert all(character in CODE_ALPHABET for character in body["confirmation_code"])
    assert body["table_label"] is not None


def test_double_booking_prevention(client, headers):
    dt = next_open_datetime(hour=20)
    r1 = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-2a",
            "customer_name": "Person A",
            "phone": "05320000001",
            "party_size": 8,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    )
    assert r1.json()["status"] == "confirmed"

    dt2 = dt + timedelta(minutes=30)  # overlaps the 90-minute window
    r2 = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-2b",
            "customer_name": "Person B",
            "phone": "05320000002",
            "party_size": 8,
            "requested_time": dt2.isoformat(),
        },
        headers=headers,
    )
    body2 = r2.json()
    assert body2["status"] == "rejected"
    assert body2["reason"] == "no_availability"


def test_lookup_matching_identity(client, headers):
    dt = next_open_datetime(hour=13)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-3",
            "customer_name": "Mert",
            "phone": "05451112233",
            "party_size": 2,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    r = client.post(
        "/api/tools/get-reservation",
        json={
            "tool_call_id": "res-3-get",
            "confirmation_code": create["confirmation_code"],
            "phone": "05451112233",
        },
        headers=headers,
    )
    body = r.json()
    assert body["found"] is True
    assert body["confirmation_code"] == create["confirmation_code"]


def test_lookup_accepts_legacy_lbl_prefix(client, headers):
    dt = next_open_datetime(hour=13, minute=30)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-prefix-get",
            "customer_name": "Selin",
            "phone": "05321112244",
            "party_size": 2,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    response = client.post(
        "/api/tools/get-reservation",
        json={
            "tool_call_id": "res-prefix-get-lookup",
            "confirmation_code": f"LBL-{create['confirmation_code'].lower()}",
            "phone": "05321112244",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["found"] is True
    assert response.json()["confirmation_code"] == create["confirmation_code"]


def test_lookup_wrong_phone_rejected(client, headers):
    dt = next_open_datetime(hour=14)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "res-4",
            "customer_name": "Deniz",
            "phone": "05451112244",
            "party_size": 2,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    r = client.post(
        "/api/tools/get-reservation",
        json={
            "tool_call_id": "res-4-get",
            "confirmation_code": create["confirmation_code"],
            "phone": "05329999999",
        },
        headers=headers,
    )
    assert r.json()["found"] is False
