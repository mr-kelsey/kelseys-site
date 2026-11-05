def test_get_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.text == "ok"
