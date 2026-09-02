from .timehelpers import next_open_datetime


def test_successful_cancellation_frees_the_table(client, headers):
    dt = next_open_datetime(hour=17)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "cancel-1",
            "customer_name": "Ece",
            "phone": "05337778899",
            "party_size": 8,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    cancel = client.post(
        "/api/tools/cancel-reservation",
        json={
            "tool_call_id": "cancel-1-cancel",
            "confirmation_code": create["confirmation_code"],
            "phone": "05337778899",
        },
        headers=headers,
    ).json()
    assert cancel["cancelled"] is True

    rebook = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "cancel-1-rebook",
            "customer_name": "Someone Else",
            "phone": "05339990000",
            "party_size": 8,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()
    assert rebook["status"] == "confirmed"


def test_cancel_wrong_phone_rejected(client, headers):
    dt = next_open_datetime(hour=18)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "cancel-2",
            "customer_name": "Fatih",
            "phone": "05341112200",
            "party_size": 2,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    cancel = client.post(
        "/api/tools/cancel-reservation",
        json={
            "tool_call_id": "cancel-2-cancel",
            "confirmation_code": create["confirmation_code"],
            "phone": "05329999999",
        },
        headers=headers,
    ).json()
    assert cancel["cancelled"] is False
    assert cancel["reason"] == "not_found"


def test_cancel_accepts_legacy_lbl_prefix(client, headers):
    dt = next_open_datetime(hour=18, minute=30)
    create = client.post(
        "/api/tools/create-reservation",
        json={
            "tool_call_id": "cancel-prefix",
            "customer_name": "Can",
            "phone": "05341112255",
            "party_size": 2,
            "requested_time": dt.isoformat(),
        },
        headers=headers,
    ).json()

    response = client.post(
        "/api/tools/cancel-reservation",
        json={
            "tool_call_id": "cancel-prefix-call",
            "confirmation_code": f"LBL-{create['confirmation_code']}",
            "phone": "05341112255",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["cancelled"] is True
    assert response.json()["confirmation_code"] == create["confirmation_code"]
