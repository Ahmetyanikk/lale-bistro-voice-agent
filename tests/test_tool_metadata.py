import pytest

from .timehelpers import next_open_datetime

# a plausible shape for OloVoice's includeMetadata=true call_context; the
# assistant never generates this, and the backend never inspects its
# contents, so its exact shape isn't load-bearing for this backend.
CALL_CONTEXT_EXAMPLE = {
    "callId": "call_abc123",
    "assistantId": "asst_xyz789",
    "customer": {"number": "+905321234567"},
}

TOOL_CASES = [
    ("/api/tools/check-availability", {"party_size": 2}, True),
    (
        "/api/tools/create-reservation",
        {"customer_name": "Ali Veli", "phone": "05321234567", "party_size": 2},
        True,
    ),
    ("/api/tools/get-reservation", {"confirmation_code": "LBL-0000", "phone": "05321234567"}, False),
    ("/api/tools/cancel-reservation", {"confirmation_code": "LBL-0000", "phone": "05321234567"}, False),
    ("/api/tools/search-menu", {"query": "kebap"}, False),
]


def _payload(business_fields: dict, needs_time: bool, tool_call_id: str, hour: int) -> dict:
    fields = dict(business_fields)
    if needs_time:
        fields["requested_time"] = next_open_datetime(hour=hour).isoformat()
    return {
        "tool_call_id": tool_call_id,
        "call_context": CALL_CONTEXT_EXAMPLE,
        **fields,
    }


@pytest.mark.parametrize("path,business_fields,needs_time", TOOL_CASES)
def test_tool_accepts_tool_call_id_and_call_context(client, headers, path, business_fields, needs_time):
    payload = _payload(business_fields, needs_time, f"meta-{path.rsplit('/', 1)[1]}", hour=15)
    r = client.post(path, json=payload, headers=headers)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("path,business_fields,needs_time", TOOL_CASES)
def test_tool_rejects_actually_unknown_field(client, headers, path, business_fields, needs_time):
    payload = _payload(business_fields, needs_time, f"unknown-{path.rsplit('/', 1)[1]}", hour=16)
    payload["this_field_does_not_exist"] = "surprise"
    r = client.post(path, json=payload, headers=headers)
    assert r.status_code == 422


def test_call_context_is_optional(client, headers):
    # omitting call_context entirely must still work — OloVoice only adds it
    # when includeMetadata=true, so it can't be required
    dt = next_open_datetime(hour=17)
    r = client.post(
        "/api/tools/check-availability",
        json={"tool_call_id": "no-call-context", "party_size": 2, "requested_time": dt.isoformat()},
        headers=headers,
    )
    assert r.status_code == 200
