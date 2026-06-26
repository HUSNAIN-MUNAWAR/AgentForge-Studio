from fastapi.testclient import TestClient
from backend.app.main import app


def test_health_and_packs():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/api/packs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_eval_api_uses_static_pack_checks():
    with TestClient(app) as client:
        packs = client.get("/api/packs").json()
        pack = next(item for item in packs if item["name"] == "Customer Feedback Intelligence Team")
        response = client.post("/api/evals/run", json={"pack_id": pack["id"]})
        assert response.status_code == 200
        result = response.json()
        assert result["summary"]["pass_rate"] == 1.0
        assert result["results"][0]["passed"] is True
