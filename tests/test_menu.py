def test_search_menu_all(client, headers):
    r = client.post(
        "/api/tools/search-menu", json={"tool_call_id": "menu-1"}, headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 5


def test_search_menu_query(client, headers):
    r = client.post(
        "/api/tools/search-menu",
        json={"tool_call_id": "menu-2", "query": "Kebap"},
        headers=headers,
    )
    body = r.json()
    assert body["count"] == 1
    assert body["items"][0]["name"] == "Adana Kebap"
