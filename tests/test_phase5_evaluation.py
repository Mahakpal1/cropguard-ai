"""Tests for Phase 5: Leave-One-Dataset-Out (LODO) & Cross-Domain Benchmarks.

Verifies:
1. PerformanceEvaluator metrics: crop accuracy, conditional disease accuracy, joint accuracy, macro-F1.
2. Physiological grounding percentage calculation and markdown report formatting.
3. LODO cross-validation loop across multi-source cached features.
4. JSON benchmark report serialization and schema compliance.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from eval.leave_one_dataset_out import LODOEvaluator
from eval.metrics import EvaluationReport, PerformanceEvaluator
from src.train import HeadTrainer

ROOT = Path(__file__).resolve().parents[1]


# ── 1. Performance Evaluator Metric Tests ────────────────────────────────────

def test_performance_evaluator_metrics():
    # 5 samples:
    # 0: Correct crop, correct disease
    # 1: Correct crop, wrong disease
    # 2: Wrong crop, wrong disease
    # 3: Correct crop, correct disease
    # 4: Rejected (unsupported)
    true_crops = ["Tomato", "Tomato", "Potato", "Rice", "Wheat"]
    pred_crops = ["Tomato", "Tomato", "Tomato", "Rice", "Unsupported"]
    true_diseases = ["Early_Blight", "Late_Blight", "Early_Blight", "Blast", "Rust"]
    pred_diseases = ["Early_Blight", "Early_Blight", "Early_Blight", "Blast", "Rust"]
    is_supported = [True, True, True, True, False]
    overlaps = [0.80, 0.75, 0.40, 0.90, 0.0]

    report = PerformanceEvaluator.evaluate_predictions(
        y_true_crops=true_crops,
        y_pred_crops=pred_crops,
        y_true_diseases=true_diseases,
        y_pred_diseases=pred_diseases,
        is_supported_flags=is_supported,
        overlap_scores=overlaps,
        dataset_name="TestDataset",
    )

    assert isinstance(report, EvaluationReport)
    assert report.total_samples == 5
    assert report.evaluated_samples == 4
    assert report.rejected_samples == 1
    assert report.rejection_rate == 0.20

    # Evaluated samples: indices 0, 1, 2, 3
    # Crop matches: index 0 (Tomato), index 1 (Tomato), index 3 (Rice) -> 3/4 = 75%
    assert np.isclose(report.crop_accuracy, 0.75)

    # Correct crops are indices 0, 1, 3.
    # Among these, disease matches are index 0, index 3 -> 2/3 = 66.67%
    assert np.isclose(report.disease_accuracy, 2.0 / 3.0)

    # Joint matches: index 0, index 3 -> 2/4 = 50%
    assert np.isclose(report.joint_accuracy, 0.50)

    # Macro F1 should be > 0.0
    assert report.macro_f1 > 0.0

    # Overlaps for evaluated: [0.80, 0.75, 0.40, 0.90] -> mean = 0.7125
    assert np.isclose(report.mean_leaf_overlap, 0.7125)

    # Grounded (>= 0.65): 0.80, 0.75, 0.90 -> 3/4 = 75%
    assert np.isclose(report.grounded_ratio, 0.75)

    # Markdown representation
    md = report.to_markdown()
    assert "Benchmark: TestDataset" in md
    assert "75.00%" in md


# ── 2. LODO Cross-Domain Benchmark Tests ─────────────────────────────────────

def test_lodo_benchmark_synthetic(tmp_path):
    in_dim = 32
    n_per_source = 20

    # Source A (Lab): 20 samples
    feats_a = np.random.randn(n_per_source, in_dim).astype(np.float32)
    # Source B (Field): 20 samples
    feats_b = np.random.randn(n_per_source, in_dim).astype(np.float32)

    features = np.vstack([feats_a, feats_b])
    crop_labels = np.array([0] * 10 + [1] * 10 + [0] * 10 + [1] * 10, dtype=np.int64)
    disease_labels = np.array([0] * 10 + [1] * 10 + [0] * 10 + [1] * 10, dtype=np.int64)
    source_ids = np.array(["source_lab"] * n_per_source + ["source_field"] * n_per_source)

    cache_data = {
        "features": features,
        "crop_labels": crop_labels,
        "disease_labels": disease_labels,
        "source_ids": source_ids,
        "crop_to_idx": {"Tomato": 0, "Potato": 1},
        "disease_to_idx": {"Early_Blight": 0, "Late_Blight": 1},
        "crop_disease_map": {
            "Tomato": ["Early_Blight"],
            "Potato": ["Late_Blight"],
        },
    }

    trainer = HeadTrainer(epochs=2, batch_size=16)
    lodo = LODOEvaluator(trainer=trainer)

    report_path = tmp_path / "lodo_report.json"
    results = lodo.run_lodo(
        cache_data=cache_data,
        min_samples_per_source=15,
        out_report_path=str(report_path),
    )

    assert "source_lab" in results
    assert "source_field" in results
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert "source_lab" in saved_data
    assert "source_field" in saved_data
    assert "crop_accuracy" in saved_data["source_lab"]
