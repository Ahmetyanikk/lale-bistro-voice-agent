from app.config import settings


def test_missing_tool_secret(client):
    r = client.post("/api/tools/search-menu", json={"tool_call_id": "auth-1"})
    assert r.status_code == 401


def test_invalid_tool_secret(client):
    r = client.post(
        "/api/tools/search-menu",
        json={"tool_call_id": "auth-2"},
        headers={"X-Tool-Secret": "wrong-secret"},
    )
    assert r.status_code == 401


def test_health_needs_no_secret(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_query_token_is_disabled_when_not_configured(client):
    r = client.post(
        "/api/tools/search-menu?tool_token=some-token",
        json={"tool_call_id": "auth-query-disabled"},
    )
    assert r.status_code == 401


def test_valid_olovoice_query_token(client, monkeypatch):
    monkeypatch.setattr(settings, "olovoice_tool_token", "olovoice-test-token")
    r = client.post(
        "/api/tools/search-menu?tool_token=olovoice-test-token",
        json={"tool_call_id": "auth-query-valid"},
    )
    assert r.status_code == 200


def test_invalid_olovoice_query_token(client, monkeypatch):
    monkeypatch.setattr(settings, "olovoice_tool_token", "olovoice-test-token")
    r = client.post(
        "/api/tools/search-menu?tool_token=wrong-token",
        json={"tool_call_id": "auth-query-invalid"},
    )
    assert r.status_code == 401
