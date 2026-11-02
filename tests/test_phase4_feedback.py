"""Phase 4: Feedback, Active Learning & Field Readiness Tests.

Covers:
- SQLite feedback schema, insertion, retrieval, and statistics
- FastAPI feedback endpoints: POST /api/v1/feedback, GET /api/v1/feedback, GET /api/v1/feedback/stats
- Validation of corrected_class_id against known classes
- CLI feedback triage and export tool (ml/triage_feedback.py)
- Integration of advice tiers, crop ID, and scan_id linking
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


# ── 4.1 Database Layer ───────────────────────────────────────────────────────

def test_feedback_db_operations(tmp_path):
    from backend.app.db import History

    db_file = tmp_path / "test_scans.db"
    h = History(db_file)

    # 1. Add scan
    sid = h.add({
        "class_id": "Apple___Cedar_apple_rust",
        "display_en": "Apple - Cedar Rust",
        "confidence": 0.95,
        "status": "ok",
        "severity_level": "Moderate",
        "affected_pct": 14.5,
        "thumb": "data:image/jpeg;base64,abc"
    })
    assert sid == 1

    # 2. Add correct feedback
    f1 = h.add_feedback({
        "scan_id": sid,
        "is_correct": True,
        "notes": "Verified by agronomist"
    })
    assert f1 == 1

    # 3. Add incorrect feedback (correction)
    f2 = h.add_feedback({
        "scan_id": sid,
        "is_correct": False,
        "corrected_class_id": "Apple___Apple_scab",
        "notes": "Actually scab on early leaves",
        "expert_verified": True
    })
    assert f2 == 2

    # 4. List feedback
    items = h.list_feedback()
    assert len(items) == 2
    assert items[0]["id"] == 2
    assert items[0]["is_correct"] is False
    assert items[0]["expert_verified"] is True
    assert items[0]["predicted_class_id"] == "Apple___Cedar_apple_rust"
    assert items[1]["is_correct"] is True

    # 5. Check stats
    stats = h.get_feedback_stats()
    assert stats["total_feedback"] == 2
    assert stats["confirmed_correct"] == 1
    assert stats["corrections_reported"] == 1
    assert stats["accuracy_rate"] == 0.5


# ── 4.2 API Endpoints ────────────────────────────────────────────────────────

def test_api_feedback_endpoints():
    from backend.app.main import app

    with TestClient(app) as client:
        # First verify health shows healthy
        r_health = client.get("/api/v1/health")
        assert r_health.status_code == 200

        # Submit valid positive feedback
        payload_ok = {
            "is_correct": True,
            "notes": "Farmer confirmed"
        }
        res1 = client.post("/api/v1/feedback", json=payload_ok)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["is_correct"] is True
        assert data1["id"] is not None

        # Submit valid correction feedback
        payload_corr = {
            "is_correct": False,
            "corrected_class_id": "Apple___Black_rot",
            "notes": "Consulted local KVK",
            "expert_verified": True
        }
        res2 = client.post("/api/v1/feedback", json=payload_corr)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["is_correct"] is False
        assert data2["corrected_class_id"] == "Apple___Black_rot"
        assert data2["expert_verified"] is True

        # Submit invalid correction with non-existent class
        payload_bad = {
            "is_correct": False,
            "corrected_class_id": "Invalid_Fake_Class_123"
        }
        res3 = client.post("/api/v1/feedback", json=payload_bad)
        assert res3.status_code == 400
        assert "Unknown corrected_class_id" in res3.json()["detail"]

        # Fetch feedback list
        res_list = client.get("/api/v1/feedback")
        assert res_list.status_code == 200
        items = res_list.json()["items"]
        assert len(items) >= 2

        # Fetch feedback stats
        res_stats = client.get("/api/v1/feedback/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total_feedback"] >= 2
        assert stats["confirmed_correct"] >= 1
        assert stats["corrections_reported"] >= 1


# ── 4.3 Live Pipeline Metadata & Scan Linking ────────────────────────────────

def test_live_prediction_linking():
    from backend.app.main import app

    img_path = ROOT / "data" / "test" / "test" / "AppleCedarRust1.JPG"
    if not img_path.exists():
        pytest.skip("Test image AppleCedarRust1.JPG not available")

    with TestClient(app) as client:
        with open(img_path, "rb") as f:
            res = client.post("/api/v1/predict?explain=false", files={"file": ("leaf.jpg", f, "image/jpeg")})
        assert res.status_code == 200
        body = res.json()

        # Check prediction metadata
        assert body["id"] is not None, "Scan ID should be returned to allow feedback attachment"
        assert body["advice_tier"] in ("reviewed", "draft", "none")
        if body["crop_id"]:
            assert body["crop_id"]["name"] == "Apple"

        # Attach feedback to this specific scan
        fb_res = client.post("/api/v1/feedback", json={
            "scan_id": body["id"],
            "is_correct": True,
            "notes": "Verified against real orchard sample"
        })
        assert fb_res.status_code == 200
        fb_data = fb_res.json()
        assert fb_data["scan_id"] == body["id"]
        assert fb_data["predicted_class_id"] == body["class_id"]


# ── 4.4 Triage CLI Tool ──────────────────────────────────────────────────────

def test_triage_feedback_cli(tmp_path):
    from backend.app.db import History

    db_path = tmp_path / "cli_test.db"
    manifest_path = tmp_path / "manifest.csv"

    h = History(db_path)
    sid = h.add({"class_id": "Apple___Cedar_apple_rust", "display_en": "Apple - Cedar Rust"})
    h.add_feedback({"scan_id": sid, "is_correct": True})
    h.add_feedback({"scan_id": sid, "is_correct": False, "corrected_class_id": "Apple___Apple_scab", "notes": "Leaf spot"})

    # Run CLI
    cmd = [
        sys.executable,
        str(ROOT / "ml" / "triage_feedback.py"),
        "--db", str(db_path),
        "--export-manifest", str(manifest_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    assert res.returncode == 0
    assert "Total Feedback Submissions : 2" in res.stdout
    assert "Confirmed Correct          : 1 (50.0%)" in res.stdout
    assert "Apple___Cedar_apple_rust  -->  Apple___Apple_scab" in res.stdout

    # Verify exported manifest
    assert manifest_path.exists()
    content = manifest_path.read_text(encoding="utf-8")
    assert "Apple___Apple_scab" in content
