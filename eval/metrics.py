"""Evaluation Metrics and Reporting Engine for CropGuard.

Computes:
1. Crop Accuracy & Disease Accuracy (isolated and joint).
2. Macro-F1 across all classes to penalize class imbalance.
3. Physiological Grounding Ratio (leaf overlap >= 65%).
4. OOD & Low Confidence Rejection Rate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score


@dataclass
class EvaluationReport:
    """Standardized performance benchmark report."""
    dataset_name: str
    total_samples: int
    evaluated_samples: int
    rejected_samples: int
    rejection_rate: float
    crop_accuracy: float
    disease_accuracy: float
    joint_accuracy: float
    macro_f1: float
    per_crop_accuracy: Dict[str, float]
    mean_leaf_overlap: Optional[float] = None
    grounded_ratio: Optional[float] = None

    def to_markdown(self) -> str:
        """Render report as a formatted Markdown summary table."""
        lines = [
            f"### Benchmark: {self.dataset_name}",
            f"- **Total Samples**: {self.total_samples}",
            f"- **Evaluated / Accepted**: {self.evaluated_samples} (Rejection Rate: {self.rejection_rate:.1%})",
            f"- **Crop Accuracy**: {self.crop_accuracy:.2%}",
            f"- **Disease Accuracy**: {self.disease_accuracy:.2%}",
            f"- **Joint Accuracy**: {self.joint_accuracy:.2%}",
            f"- **Macro-F1 Score**: {self.macro_f1:.4f}",
        ]
        if self.mean_leaf_overlap is not None:
            lines.append(f"- **Mean Leaf Overlap**: {self.mean_leaf_overlap:.1%}")
        if self.grounded_ratio is not None:
            lines.append(f"- **Physiologically Grounded Ratio**: {self.grounded_ratio:.1%}")

        lines.append("\n**Per-Crop Performance:**")
        lines.append("| Crop | Accuracy |")
        lines.append("|---|---|")
        for crop, acc in sorted(self.per_crop_accuracy.items()):
            lines.append(f"| {crop} | {acc:.1%} |")

        return "\n".join(lines)


class PerformanceEvaluator:
    """Computes multidimensional classification and explainability metrics."""

    @staticmethod
    def evaluate_predictions(
        y_true_crops: List[str],
        y_pred_crops: List[str],
        y_true_diseases: List[str],
        y_pred_diseases: List[str],
        is_supported_flags: List[bool],
        overlap_scores: Optional[List[float]] = None,
        dataset_name: str = "Benchmark",
    ) -> EvaluationReport:
        """
        Compute standard benchmark metrics across prediction lists.
        """
        total = len(y_true_crops)
        if total == 0:
            return EvaluationReport(
                dataset_name=dataset_name,
                total_samples=0,
                evaluated_samples=0,
                rejected_samples=0,
                rejection_rate=0.0,
                crop_accuracy=0.0,
                disease_accuracy=0.0,
                joint_accuracy=0.0,
                macro_f1=0.0,
                per_crop_accuracy={},
            )

        n_rejected = sum(1 for sup in is_supported_flags if not sup)
        rejection_rate = float(n_rejected / total)

        # Filter to accepted / evaluated samples for accuracy metrics
        valid_indices = [i for i, sup in enumerate(is_supported_flags) if sup]
        n_eval = len(valid_indices)

        if n_eval == 0:
            return EvaluationReport(
                dataset_name=dataset_name,
                total_samples=total,
                evaluated_samples=0,
                rejected_samples=n_rejected,
                rejection_rate=1.0,
                crop_accuracy=0.0,
                disease_accuracy=0.0,
                joint_accuracy=0.0,
                macro_f1=0.0,
                per_crop_accuracy={},
            )

        eval_true_crops = [y_true_crops[i] for i in valid_indices]
        eval_pred_crops = [y_pred_crops[i] for i in valid_indices]
        eval_true_dis = [y_true_diseases[i] for i in valid_indices]
        eval_pred_dis = [y_pred_diseases[i] for i in valid_indices]

        # 1. Crop Accuracy
        crop_correct = sum(1 for tc, pc in zip(eval_true_crops, eval_pred_crops) if tc == pc)
        crop_accuracy = float(crop_correct / n_eval)

        # 2. Disease Accuracy (given correct crop)
        correct_crop_indices = [i for i, (tc, pc) in enumerate(zip(eval_true_crops, eval_pred_crops)) if tc == pc]
        if correct_crop_indices:
            dis_correct = sum(
                1 for i in correct_crop_indices if eval_true_dis[i] == eval_pred_dis[i]
            )
            disease_accuracy = float(dis_correct / len(correct_crop_indices))
        else:
            disease_accuracy = 0.0

        # 3. Joint Accuracy (both crop and disease match)
        joint_correct = sum(
            1 for tc, pc, td, pd in zip(eval_true_crops, eval_pred_crops, eval_true_dis, eval_pred_dis)
            if tc == pc and td == pd
        )
        joint_accuracy = float(joint_correct / n_eval)

        # 4. Macro-F1 across joint canonical keys
        true_keys = [f"{c}___{d}" for c, d in zip(eval_true_crops, eval_true_dis)]
        pred_keys = [f"{c}___{d}" for c, d in zip(eval_pred_crops, eval_pred_dis)]
        macro_f1 = float(f1_score(true_keys, pred_keys, average="macro", zero_division=0))

        # 5. Per-Crop Accuracy
        by_crop_total: Dict[str, int] = {}
        by_crop_correct: Dict[str, int] = {}
        for tc, pc in zip(eval_true_crops, eval_pred_crops):
            by_crop_total[tc] = by_crop_total.get(tc, 0) + 1
            if tc == pc:
                by_crop_correct[tc] = by_crop_correct.get(tc, 0) + 1

        per_crop_acc = {
            c: float(by_crop_correct.get(c, 0) / by_crop_total[c])
            for c in by_crop_total
        }

        # 6. Physiological Grounding Metrics
        mean_overlap = None
        grounded_ratio = None
        if overlap_scores is not None and len(overlap_scores) > 0:
            valid_overlaps = [overlap_scores[i] for i in valid_indices if overlap_scores[i] is not None]
            if valid_overlaps:
                mean_overlap = float(np.mean(valid_overlaps))
                grounded_ratio = float(np.mean([s >= 0.65 for s in valid_overlaps]))

        return EvaluationReport(
            dataset_name=dataset_name,
            total_samples=total,
            evaluated_samples=n_eval,
            rejected_samples=n_rejected,
            rejection_rate=rejection_rate,
            crop_accuracy=crop_accuracy,
            disease_accuracy=disease_accuracy,
            joint_accuracy=joint_accuracy,
            macro_f1=macro_f1,
            per_crop_accuracy=per_crop_acc,
            mean_leaf_overlap=mean_overlap,
            grounded_ratio=grounded_ratio,
        )
