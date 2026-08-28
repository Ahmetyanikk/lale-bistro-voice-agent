from datetime import datetime, timedelta

from app.timeutil import TZ

from .timehelpers import next_monday_datetime, next_open_datetime


def test_check_availability_success(client, headers):
    dt = next_open_datetime(hour=19)
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-1", "party_size": 2, "requested_time": dt.isoformat()},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert body["table_label"] is not None


def test_closed_monday(client, headers):
    dt = next_monday_datetime(hour=19)
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-2", "party_size": 2, "requested_time": dt.isoformat()},
        headers=headers,
    )
    body = r.json()
    assert body["available"] is False
    assert body["reason"] == "closed_monday"


def test_outside_opening_hours(client, headers):
    dt = next_open_datetime(hour=8)
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-3", "party_size": 2, "requested_time": dt.isoformat()},
        headers=headers,
    )
    body = r.json()
    assert body["available"] is False
    assert body["reason"] == "outside_opening_hours"


def test_past_time(client, headers):
    dt = (datetime.now(TZ) - timedelta(days=1)).replace(
        hour=19, minute=0, second=0, microsecond=0
    )
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-4", "party_size": 2, "requested_time": dt.isoformat()},
        headers=headers,
    )
    body = r.json()
    assert body["available"] is False
    assert body["reason"] == "past_time"


def test_party_too_large_rejected_by_validation(client, headers):
    dt = next_open_datetime(hour=19)
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-5", "party_size": 9, "requested_time": dt.isoformat()},
        headers=headers,
    )
    assert r.status_code == 422


def test_alternative_slots_when_full(client, headers):
    dt = next_open_datetime(hour=19)
    client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "avail-6-book",
            "customer_name": "Ali",
            "phone": "05321234567",
            "party_size": 8,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    )
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "avail-6", "party_size": 8, "requested_time": dt.isoformat()},
        headers=headers,
    )
    body = r.json()
    assert body["available"] is False
    assert body["reason"] == "no_availability"
    assert 1 <= len(body["alternatives"]) <= 3
