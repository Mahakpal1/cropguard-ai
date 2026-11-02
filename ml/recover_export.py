import json
import sys
from pathlib import Path

import torch
import timm

sys.path.insert(0, str(Path("ml").resolve()))
import cg_common as cg

OUT = Path("ml/models/cropguard38_recovered")
CKPT = Path("ml/models/cropguard38_full/_ckpt/best.pt")
DATA = Path("data/disease_dataset")
BACKBONE = "convnext_tiny.fb_in22k_ft_in1k"
IMG = 224
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

if not CKPT.is_file():
    raise SystemExit(f"Checkpoint not found: {CKPT}")

tr_dir, va_dir = cg.find_split_dirs(DATA)
if tr_dir is None:
    raise SystemExit(f"Dataset train/valid folders not found under {DATA}")

import pandas as pd
rows = cg.scan(tr_dir, "train")
if va_dir:
    rows += cg.scan(va_dir, "valid")

raw_classes = sorted({row[1] for row in rows})
classes, healthy_only = cg.build_meta(raw_classes)

OUT.mkdir(parents=True, exist_ok=True)
print(f"Classes found: {len(raw_classes)}")
print(f"Checkpoint: {CKPT}")
print(f"Output: {OUT.resolve()}")

model = timm.create_model(
    BACKBONE, pretrained=False, num_classes=len(raw_classes)
)

state = torch.load(CKPT, map_location="cpu", weights_only=True)
model.load_state_dict(state, strict=True)
model.eval()

onnx_path = OUT / "model.onnx"
dummy = torch.randn(1, 3, IMG, IMG)

torch.onnx.export(
    model,
    dummy,
    str(onnx_path),
    input_names=["input"],
    output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    opset_version=17,
    dynamo=False,
)

import onnx
import onnxruntime as ort
onnx.checker.check_model(onnx.load(str(onnx_path)))

session = ort.InferenceSession(
    str(onnx_path), providers=["CPUExecutionProvider"]
)
x = torch.randn(2, 3, IMG, IMG)
with torch.no_grad():
    expected = model(x).numpy()
actual = session.run(None, {"input": x.numpy()})[0]
difference = float(abs(expected - actual).max())
print(f"ONNX verification passed. Maximum output difference: {difference:.8g}")

json.dump(
    {
        "name": f"cropguard-convnext_tiny-{len(raw_classes)}class",
        "onnx": "model.onnx",
        "labels": [c["id"] for c in classes],
        "classes_file": "class_names.json",
        "input_size": IMG,
        "mean": MEAN,
        "std": STD,
        "temperature": 1.0,
        "confidence_threshold": 0.6,
        "tta": True,
        "healthy_only_crops": healthy_only,
    },
    open(OUT / "model_config.json", "w", encoding="utf-8"),
    indent=2,
)

json.dump(
    {"version": 3, "input_size": IMG, "mean": MEAN, "std": STD, "classes": classes},
    open(OUT / "class_names.json", "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2,
)

print(f"Recovered model exported successfully to: {OUT.resolve()}")
print("Note: calibration and held-out test metrics were not regenerated.")
