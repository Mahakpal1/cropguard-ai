"""Install the model you trained (zip from the notebook) into the project.

    1. unzip cropguard_artifacts.zip into  ml/models/cropguard/
    2. python ml/make_model_config.py
    3. restart the server

Writes ml/models/cropguard/model_config.json and makes it the active model.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from switch_model import activate  # noqa: E402

M = Path(__file__).resolve().parent / "models"
D = M / "cropguard"
for need in ("cropguard_effb0.onnx", "class_names.json", "calibration.json"):
    if not (D / need).exists():
        sys.exit(f"Missing {D / need}. Unzip cropguard_artifacts.zip into {D} first.")
names = json.load(open(D / "class_names.json", encoding="utf-8"))
calib = json.load(open(D / "calibration.json"))
cfg = {"name": "cropguard-efficientnet-b0", "onnx": "cropguard_effb0.onnx", "labels": names["classes"],
       "input_size": names["input_size"], "mean": names["mean"], "std": names["std"],
       "temperature": calib["temperature"], "confidence_threshold": calib["confidence_threshold"]}
json.dump(cfg, open(D / "model_config.json", "w", encoding="utf-8"), indent=2)
activate(M, "cropguard")
print("Installed and activated. temperature", cfg["temperature"], "| threshold", cfg["confidence_threshold"], "\nRestart the server.")
