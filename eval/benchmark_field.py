"""PlantDoc & Real-World Field Benchmark Engine for CropGuard.

Evaluates trained CropGuard pipeline against real outdoor farming photos
(noisy natural lighting, complex foliage backgrounds, multiple lesions).
Reports isolated Crop Accuracy, Disease Accuracy, Macro-F1, and Physiological Grounding.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from PIL import Image
from tqdm import tqdm

from eval.metrics import EvaluationReport, PerformanceEvaluator
from src.infer import CropGuardInferenceEngine, EndToEndDiagnosis

logger = logging.getLogger("cropguard.field_bench")


class FieldBenchmark:
    """Evaluates CropGuard pipeline on field test datasets."""

    def __init__(self, inference_engine: CropGuardInferenceEngine):
        self.engine = inference_engine

    def benchmark_directory(
        self,
        test_images_csv_or_dir: str,
        class_mapping: Optional[Dict[str, Tuple[str, str]]] = None,
        out_report_path: Optional[str] = "eval/reports/field_benchmark_report.json",
        max_samples: Optional[int] = 100,
    ) -> EvaluationReport:
        """
        Evaluate inference engine on a collection of field images.
        """
        p = Path(test_images_csv_or_dir)
        samples = []

        if p.is_file() and p.suffix.lower() == ".csv":
            df = pd.read_csv(p)
            for _, r in df.iterrows():
                samples.append((r["path"], r["crop"], r["disease"]))
        elif p.is_dir():
            # Standard directory of subfolders
            for folder in p.iterdir():
                if not folder.is_dir():
                    continue
                crop_name = folder.name.split("_")[0]
                dis_name = folder.name
                if class_mapping and folder.name in class_mapping:
                    crop_name, dis_name = class_mapping[folder.name]
                for img_file in folder.glob("*.*"):
                    if img_file.suffix.lower() in (".jpg", ".jpeg", ".png"):
                        samples.append((str(img_file), crop_name, dis_name))

        if max_samples and len(samples) > max_samples:
            samples = samples[:max_samples]

        logger.info(f"Benchmarking {len(samples)} field images...")

        y_true_crops = []
        y_pred_crops = []
        y_true_dis = []
        y_pred_dis = []
        is_supported_flags = []
        overlap_scores = []

        for img_path, true_crop, true_disease in tqdm(samples, desc="Field Benchmark"):
            try:
                diag: EndToEndDiagnosis = self.engine.diagnose(img_path, explain=True)
                y_true_crops.append(true_crop)
                y_pred_crops.append(diag.crop)
                y_true_dis.append(true_disease)
                y_pred_dis.append(diag.disease)
                is_supported_flags.append(diag.is_supported)
                overlap_scores.append(diag.leaf_overlap_score)
            except Exception as e:
                logger.warning(f"Error evaluating {img_path}: {e}")

        report = PerformanceEvaluator.evaluate_predictions(
            y_true_crops=y_true_crops,
            y_pred_crops=y_pred_crops,
            y_true_diseases=y_true_dis,
            y_pred_diseases=y_pred_dis,
            is_supported_flags=is_supported_flags,
            overlap_scores=overlap_scores,
            dataset_name="PlantDoc_Field_Benchmark",
        )

        if out_report_path:
            p_out = Path(out_report_path)
            p_out.parent.mkdir(parents=True, exist_ok=True)
            with open(p_out, "w", encoding="utf-8") as f:
                json.dump({
                    "dataset_name": report.dataset_name,
                    "total_samples": report.total_samples,
                    "evaluated_samples": report.evaluated_samples,
                    "rejection_rate": report.rejection_rate,
                    "crop_accuracy": report.crop_accuracy,
                    "disease_accuracy": report.disease_accuracy,
                    "joint_accuracy": report.joint_accuracy,
                    "macro_f1": report.macro_f1,
                    "mean_leaf_overlap": report.mean_leaf_overlap,
                    "grounded_ratio": report.grounded_ratio,
                    "per_crop_accuracy": report.per_crop_accuracy,
                }, f, indent=2)

        return report
