import json
import os
import subprocess
import sys

import numpy as np

from tests.conftest import BLUE, ROOT, leaf_image


def run_tool(args, model_dir, tmp_path):
    env = dict(os.environ, MODEL_DIR=str(model_dir), DB_PATH=str(tmp_path / "x.db"), PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env, cwd=ROOT)


def test_diagnose_explains_a_photo(toy_dir, tmp_path):
    f = tmp_path / "p.png"; leaf_image(0.3).save(f)
    out = run_tool(["ml/diagnose.py", str(f)], toy_dir, tmp_path)
    assert out.returncode == 0, out.stderr
    assert "top-5 over ALL model outputs" in out.stdout and "Tomato___Early_blight" in out.stdout and "views agree" in out.stdout


def test_diagnose_flags_other_crops(toy_dir, tmp_path):
    f = tmp_path / "b.png"; leaf_image(0.0, base=BLUE).save(f)
    out = run_tool(["ml/diagnose.py", str(f)], toy_dir, tmp_path)
    assert "Apple___Apple_scab" in out.stdout and "NOT one of our classes" in out.stdout and "OTHER crops" in out.stdout


def test_calibrate_gates_writes_thresholds(toy_dir, tmp_path):
    for cls, frac in [("Tomato___healthy", 0.0), ("Tomato___Early_blight", 0.3)]:
        (tmp_path / "id" / cls).mkdir(parents=True)
        for i in range(25):
            leaf_image(frac).save(tmp_path / "id" / cls / f"{i}.png")
    (tmp_path / "ood").mkdir()
    for i in range(10):
        # a colour the toy model has no strong opinion about (all logits near 0 = unfamiliar = high energy)
        leaf_image(0.0, base=(65, 130, 50)).save(tmp_path / "ood" / f"{i}.png")
    out = run_tool(["ml/calibrate_gates.py", "--id-dir", str(tmp_path / "id"), "--ood-dir", str(tmp_path / "ood"), "--write"], toy_dir, tmp_path)
    assert out.returncode == 0, out.stderr
    cfg = json.load(open(toy_dir / "model_config.json"))
    assert "energy_threshold" in cfg and cfg["confidence_threshold"] >= 0.3
    assert "AUROC 1.000" in out.stdout
