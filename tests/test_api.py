import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from tests.conftest import leaf_image, png_bytes


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


def post(client, data, ctype="image/png", **params):
    return client.post("/api/v1/predict", files={"file": ("leaf.png", data, ctype)}, params=params)


def test_health_and_classes(client):
    h = client.get("/api/v1/health").json()
    assert h["status"] == "ok" and h["model"]["simulated"] is True and h["knowledge_entries"] >= 15
    assert len(client.get("/api/v1/classes").json()["classes"]) >= 15


def test_knowledge_endpoint(client):
    assert client.get("/api/v1/knowledge/Tomato_Early_blight").json()["scientific_name"] == "Alternaria solani"
    assert client.get("/api/v1/knowledge/nope").status_code == 404


def test_predict_matches_contract_and_is_stored(client):
    r = post(client, png_bytes(leaf_image(0.3)))
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok" and j["severity"]["level"] == "Moderate" and j["id"] >= 1
    items = client.get("/api/v1/history").json()["items"]
    assert items[0]["class_id"] == j["class_id"] and items[0]["thumb"].startswith("data:image/jpeg")
    assert client.delete("/api/v1/history").json()["deleted"] is True
    assert client.get("/api/v1/history").json()["items"] == []


def test_bad_inputs(client, tmp_path):
    assert post(client, b"hello", "text/plain").status_code == 415
    assert post(client, b"not really an image").status_code == 400
    with TestClient(create_app(Settings(max_upload_mb=0, db_path=tmp_path / "x.db", frontend_dir=tmp_path / "none"))) as c:
        assert post(c, png_bytes(leaf_image(0.1))).status_code == 413


def test_explain_flag(client):
    assert post(client, png_bytes(leaf_image(0.3)), explain="false").json()["heatmap"] is None


def test_models_endpoints(client):
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    j = r.json()
    assert "available" in j
    assert "active_info" in j
    # Invalid model switch returns 400
    r_bad = client.post("/api/v1/models/switch?model_name=non_existent_model_xyz")
    assert r_bad.status_code == 400

