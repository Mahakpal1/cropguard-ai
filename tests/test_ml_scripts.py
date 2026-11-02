import json
import sys

from backend.app.config import Settings
from backend.app.services.pipeline import Pipeline
from tests.conftest import PV38, ROOT, build_toy_model, leaf_image, png_bytes

sys.path.insert(0, str(ROOT / "ml"))
from switch_model import activate, available  # noqa: E402


def test_switch_model_points_backend_at_subfolder(tmp_path):
    models = tmp_path / "models"
    (models / "cropguard").mkdir(parents=True)
    build_toy_model(models / "cropguard" / "toy.onnx")
    json.dump({"name": "mine", "onnx": "toy.onnx", "labels": PV38}, open(models / "cropguard" / "model_config.json", "w"))
    assert available(models) == ["cropguard"]
    cfg = activate(models, "cropguard")
    assert cfg["onnx"] == "cropguard/toy.onnx"
    s = Settings(model_dir=models, db_path=tmp_path / "t.db", frontend_dir=tmp_path / "none")
    r = Pipeline(s).predict(png_bytes(leaf_image(0.3)), explain=False)
    assert r["model"]["simulated"] is False and r["model"]["name"] == "mine" and r["class_id"] == "Tomato_Early_blight"
