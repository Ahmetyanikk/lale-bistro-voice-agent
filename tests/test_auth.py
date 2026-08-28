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
