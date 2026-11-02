import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Fix Windows pytest symlink permission issue in default AppData Temp
tmp_root = ROOT / ".pytest_tmp"
tmp_root.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(tmp_root)
os.environ["TMP"] = str(tmp_root)

import numpy as np
import onnx
import pytest
from onnx import TensorProto, helper
from PIL import Image

from backend.app.config import Settings

ROOT = Path(__file__).resolve().parents[1]
GREEN, BROWN, BLUE = (50, 130, 50), (140, 90, 40), (20, 20, 255)

PV38 = ["Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy", "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
        "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot",
        "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___Tomato_mosaic_virus", "Tomato___healthy", "Apple___Apple_scab"]


def leaf_image(spot_fraction=0.0, size=256, base=GREEN):
    a = np.zeros((size, size, 3), np.uint8)
    a[:] = base
    a[:, : int(size * spot_fraction)] = BROWN
    return Image.fromarray(a)


def png_bytes(img, fmt="PNG"):
    import io
    b = io.BytesIO()
    img.save(b, fmt)
    return b.getvalue()


def build_toy_model(path):
    """Tiny ONNX model (mean colour -> 16 logits) so tests exercise the real ONNX code path without trained weights."""
    K = len(PV38)
    W = np.zeros((3, K), np.float32)
    b = np.zeros(K, np.float32)
    h, e, apple = PV38.index("Tomato___healthy"), PV38.index("Tomato___Early_blight"), PV38.index("Apple___Apple_scab")
    W[0, e], b[e] = 40, 40       # more brown (higher red) -> early blight
    W[0, h], b[h] = -40, -40     # pure green -> healthy
    W[2, apple], b[apple] = 40, -60   # very blue -> an out-of-scope crop
    x = helper.make_tensor_value_info("input", TensorProto.FLOAT, ["N", 3, 224, 224])
    y = helper.make_tensor_value_info("logits", TensorProto.FLOAT, ["N", K])
    nodes = [helper.make_node("ReduceMean", ["input"], ["m"], axes=[2, 3], keepdims=0),
             helper.make_node("MatMul", ["m", "W"], ["mm"]), helper.make_node("Add", ["mm", "b"], ["logits"])]
    g = helper.make_graph(nodes, "toy", [x], [y], [helper.make_tensor("W", TensorProto.FLOAT, W.shape, W.flatten()),
                                                   helper.make_tensor("b", TensorProto.FLOAT, b.shape, b)])
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8
    onnx.save(m, str(path))


@pytest.fixture
def toy_dir(tmp_path):
    d = tmp_path / "models"
    d.mkdir()
    build_toy_model(d / "toy.onnx")
    json.dump({"name": "toy-test-model", "onnx": "toy.onnx", "labels": PV38, "confidence_threshold": 0.6},
              open(d / "model_config.json", "w"))
    return d


@pytest.fixture
def settings(tmp_path):
    return Settings(model_dir=tmp_path / "no_model", db_path=tmp_path / "t.db", frontend_dir=tmp_path / "no_frontend")


@pytest.fixture
def toy_settings(tmp_path, toy_dir):
    return Settings(model_dir=toy_dir, db_path=tmp_path / "t.db", frontend_dir=tmp_path / "no_frontend")


def build_toy_crop_id(model_dir, vectors, threshold=0.5):
    """Toy crop-identification model: embedding = mean colour (identity projection). vectors: {crop: 3-vector}."""
    d = model_dir / "crop_id"
    d.mkdir(parents=True, exist_ok=True)
    x = helper.make_tensor_value_info("input", TensorProto.FLOAT, ["N", 3, 224, 224])
    y = helper.make_tensor_value_info("emb", TensorProto.FLOAT, ["N", 3])
    nodes = [helper.make_node("ReduceMean", ["input"], ["m"], axes=[2, 3], keepdims=0), helper.make_node("MatMul", ["m", "W"], ["emb"])]
    g = helper.make_graph(nodes, "cropid", [x], [y], [helper.make_tensor("W", TensorProto.FLOAT, [3, 3], np.eye(3, dtype=np.float32).flatten())])
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8
    onnx.save(m, str(d / "enc.onnx"))
    crops = list(vectors)
    np.save(d / "emb.npy", np.array([vectors[c] for c in crops], np.float32))
    json.dump({"onnx": "enc.onnx", "embeddings": "emb.npy", "crops": crops, "mean": [0, 0, 0], "std": [1, 1, 1],
               "logit_scale": 100.0, "threshold": threshold}, open(d / "config.json", "w"))


def settings_for(tmp_path, model_dir):
    return Settings(model_dir=model_dir, db_path=tmp_path / "t.db", frontend_dir=tmp_path / "none")


def patch_config(model_dir, **kw):
    p = model_dir / "model_config.json"
    cfg = json.load(open(p))
    cfg.update(kw)
    json.dump(cfg, open(p, "w"))
