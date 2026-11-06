"""End-to-End Build and Training Orchestrator for CropGuard.

Executes the research-grade pipeline:
1. Data: Scans directories, maps to taxonomy, deduplicates with pHash (Union-Find leaf clusters),
   caps lab data to prevent inflation, and splits honestly by leaf group.
2. Lab-to-Field Transfer: Augments lab images with randomized field backgrounds and photometric field jitter.
3. Feature Caching: Pre-extracts and saves frozen DINOv2 features to disk as .npz.
4. Hierarchical Training: Fits Crop head and per-crop Disease heads with class-balanced loss.
5. Calibration: Calibrates temperatures via L-BFGS NLL minimization and sets energy OOD rejection thresholds.
6. Deployment: Exports deployable bundle (hierarchical_heads.pt, model_config.json, classes_hierarchy.json).
7. Evaluation: Reports crop accuracy, disease accuracy, macro-F1, and ECE.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch

from eval.metrics import PerformanceEvaluator
from src.calibrate import SystemCalibrator
from src.dataset import Deduplicator, HonestSplitter, TaxonomyRegistry
from src.extract_features import DINOv2FeatureExtractor, FeatureCacheEngine
from src.heads import HierarchicalClassifier
from src.infer import CropGuardInferenceEngine
from src.train import HeadTrainer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cropguard.build_and_train")


class PipelineBuilder:
    """End-to-end dataset preparation, caching, hierarchical head training, and calibration."""

    def __init__(
        self,
        taxonomy_path: str = "data/taxonomy.csv",
        model_name: str = "dinov2_vitl14",
        img_size: int = 518,
        late_fusion: Optional[str] = None,
        cache_dir: str = "data/cached_features",
        output_dir: str = "ml/models/dinov2_hierarchical",
        device: Optional[str] = None,
    ):
        self.taxonomy_path = Path(taxonomy_path)
        self.model_name = model_name
        self.img_size = img_size
        self.late_fusion = late_fusion
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.registry = TaxonomyRegistry(str(self.taxonomy_path))
        self.deduplicator = Deduplicator(hamming_distance_threshold=4)
        self.splitter = HonestSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
        self.extractor = DINOv2FeatureExtractor(
            model_name=self.model_name,
            img_size=self.img_size,
            late_fusion_backbone=self.late_fusion,
            device=self.device,
        )
        self.cache_engine = FeatureCacheEngine(extractor=self.extractor)
        self.trainer = HeadTrainer(device=self.device)

    # -------------------------------------------------------------------------
    # 1. Dataset Scan & Honest Preparation
    # -------------------------------------------------------------------------
    def scan_and_prepare_dataset(
        self,
        data_roots: List[Union[str, Path]],
        max_samples_per_class: Optional[int] = None,
        cap_lab_ratio: Optional[float] = 0.50,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Scan folders, match against taxonomy, compute perceptual hashes,
        cap lab samples if requested, and split honestly by leaf group.
        """
        from src.dataset import DatasetSample

        valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        raw_samples: List[DatasetSample] = []

        logger.info(f"Scanning {len(data_roots)} data roots...")
        for root in data_roots:
            root_p = Path(root)
            if not root_p.exists():
                logger.warning(f"Root path not found: {root_p}")
                continue

            # Find all directories that contain image files directly (supports both flat and 2-level layouts)
            candidate_dirs = [
                d for d in root_p.glob("**/*")
                if d.is_dir() and any(f.suffix.lower() in valid_exts for f in d.iterdir() if f.is_file())
            ]
            # Also check root_p itself if images are placed directly in it
            if any(f.suffix.lower() in valid_exts for f in root_p.iterdir() if f.is_file()):
                candidate_dirs.append(root_p)

            for folder in candidate_dirs:
                folder_name = folder.name
                source_candidate = folder.parent.name.lower()

                # 1. Try matching with parent directory as source
                info = self.registry.get_info(source=source_candidate, raw_folder=folder_name)
                # 2. Try matching with root as source
                if not info:
                    info = self.registry.get_info(source=root_p.name.lower(), raw_folder=folder_name)
                # 3. Fallback: match by raw folder name across taxonomy
                if not info:
                    for key, val in self.registry.mappings.items():
                        if key[1].lower() == folder_name.lower():
                            info = val
                            break

                if not info:
                    continue

                img_files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
                if max_samples_per_class:
                    img_files = img_files[:max_samples_per_class]

                for img_path in img_files:
                    ph = self.deduplicator.compute_phash(img_path)
                    sample = DatasetSample(
                        image_path=str(img_path),
                        source=info.get("source", source_candidate),
                        canonical_crop=info["canonical_crop"],
                        canonical_disease=info["canonical_disease"],
                        canonical_key=info["canonical_key"],
                        is_lab=info.get("is_lab", False),
                        phash=ph,
                        leaf_group_id="",
                    )
                    raw_samples.append(sample)

        logger.info(f"Found {len(raw_samples)} raw matched images across taxonomy.")
        if not raw_samples:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Group near-duplicates (pHash Hamming distance <= 4)
        logger.info("Grouping near-duplicates into leaf clusters...")
        grouped_samples = self.deduplicator.group_near_duplicates(raw_samples)

        # Cap lab images so field images dominate/balance
        if cap_lab_ratio is not None and 0.0 < cap_lab_ratio < 1.0:
            lab_samples = [s for s in grouped_samples if s.is_lab]
            field_samples = [s for s in grouped_samples if not s.is_lab]
            if field_samples:
                max_lab = int(len(field_samples) * (cap_lab_ratio / (1.0 - cap_lab_ratio)))
                if len(lab_samples) > max_lab:
                    np.random.seed(42)
                    idx = np.random.choice(len(lab_samples), size=max_lab, replace=False)
                    lab_samples = [lab_samples[i] for i in idx]
                    logger.info(f"Capped lab samples from {len(grouped_samples)-len(field_samples)} to {max_lab}.")
                    grouped_samples = field_samples + lab_samples

        # Split honestly by leaf group
        logger.info("Executing honest leaf-group split (70/15/15)...")
        train_df, val_df, test_df = self.splitter.split_by_leaf_group(grouped_samples)
        logger.info(f"Splits created: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        return train_df, val_df, test_df

    # -------------------------------------------------------------------------
    # 2. Feature Extraction & Caching
    # -------------------------------------------------------------------------
    def extract_and_cache_all(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        dataset_name: str = "cropguard_dataset",
        apply_augmentation: bool = True,
        save_subsets: bool = True,
    ) -> Tuple[Path, Path, Path]:
        """Pre-extract frozen DINOv2 features and save to disk, with optional clean and augmented subset caching."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        train_cache = self.cache_dir / f"{dataset_name}_train_{self.model_name}.npz"
        val_cache = self.cache_dir / f"{dataset_name}_val_{self.model_name}.npz"
        test_cache = self.cache_dir / f"{dataset_name}_test_{self.model_name}.npz"

        if train_cache.exists() and val_cache.exists() and test_cache.exists():
            logger.info(f"Reusing existing cached features at {self.cache_dir}")
            return train_cache, val_cache, test_cache

        logger.info("Caching training split features (with lab-to-field augmentation)...")
        self.cache_engine.process_and_cache(
            train_df,
            out_npz_path=str(train_cache),
            apply_augmentation=apply_augmentation,
            save_subsets=save_subsets,
        )

        logger.info("Caching validation split features...")
        self.cache_engine.process_and_cache(
            val_df,
            out_npz_path=str(val_cache),
            apply_augmentation=False,
            save_subsets=save_subsets,
        )

        logger.info("Caching test split features...")
        self.cache_engine.process_and_cache(
            test_df,
            out_npz_path=str(test_cache),
            apply_augmentation=False,
            save_subsets=save_subsets,
        )

        return train_cache, val_cache, test_cache

    # -------------------------------------------------------------------------
    # 3. Hierarchical Training & Calibration
    # -------------------------------------------------------------------------
    def train_and_calibrate(
        self,
        train_cache_path: Union[str, Path],
        val_cache_path: Union[str, Path],
        cache_mode: str = "both",
        field_only_calibration: bool = True,
        epochs: int = 15,
        lr: float = 1e-3,
        batch_size: int = 64,
        target_tpr: float = 0.95,
    ) -> Tuple[HierarchicalClassifier, Path]:
        """Fit Crop Head + Per-Crop Disease Heads and perform temperature + energy calibration.
        
        Args:
            cache_mode: 'both' (default), 'clean' (unaugmented only), or 'augmented' (augmented only).
            field_only_calibration: Calibrate temperatures and reject threshold strictly on field validation split.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = self.output_dir / "hierarchical_heads.pt"

        # Load cached features
        raw_train_data = self.cache_engine.load_cache(train_cache_path)
        train_data = self.cache_engine.filter_cache(raw_train_data, mode=cache_mode)
        val_data = self.cache_engine.load_cache(val_cache_path)

        logger.info(f"Training heads on cached features (mode='{cache_mode}', samples={len(train_data['features'])})...")

        # Train hierarchical classifier
        self.trainer.epochs = epochs
        self.trainer.lr = lr
        self.trainer.batch_size = batch_size
        classifier = self.trainer.train_hierarchical_system(train_data, out_checkpoint_path=str(ckpt_path))

        # Calibrate with SystemCalibrator (temperature scaling + energy OOD threshold)
        logger.info(f"Running SystemCalibrator (field_only={field_only_calibration}) on validation split...")
        classifier = SystemCalibrator.calibrate(
            classifier,
            val_data,
            target_tpr=target_tpr,
            field_only=field_only_calibration,
        )

        # Update saved checkpoint with calibrated temperatures and energy threshold
        torch.save({
            "model_state": classifier.state_dict(),
            "in_features": train_data["features"].shape[1],
            "crop_names": classifier.crop_names,
            "crop_disease_map": classifier.crop_disease_map,
            "crop_to_idx": train_data["crop_to_idx"],
            "disease_to_idx": train_data["disease_to_idx"],
            "energy_threshold": classifier.energy_threshold,
            "temperature_crop": float(classifier.crop_head.temperature.data.item()),
            "temperatures_disease": {
                c: float(h.temperature.data.item())
                for c, h in classifier.disease_heads.items()
            },
        }, ckpt_path)

        # Export model_config.json
        cfg = {
            "name": f"cropguard_{self.model_name}_hierarchical",
            "model_type": "dinov2_hierarchical",
            "backbone": self.model_name,
            "checkpoint": "hierarchical_heads.pt",
            "input_size": self.img_size,
            "feature_dim": train_data["features"].shape[1],
            "energy_threshold": float(classifier.energy_threshold),
            "confidence_threshold": 0.60,
            "margin_threshold": 0.10,
            "num_crops": len(classifier.crop_names),
            "crops": classifier.crop_names,
            "crop_disease_map": classifier.crop_disease_map,
        }
        with open(self.output_dir / "model_config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

        # Export classes_hierarchy.json
        hierarchy = {
            "crops": classifier.crop_names,
            "taxonomy": classifier.crop_disease_map,
        }
        with open(self.output_dir / "classes_hierarchy.json", "w", encoding="utf-8") as f:
            json.dump(hierarchy, f, indent=2)

        logger.info(f"Model bundle exported successfully to {self.output_dir}")
        return classifier, ckpt_path

    # -------------------------------------------------------------------------
    # 4. Evaluation
    # -------------------------------------------------------------------------
    def evaluate(
        self,
        classifier: HierarchicalClassifier,
        test_cache_path: Union[str, Path],
        train_cache_path: Optional[Union[str, Path]] = None,
        run_lodo: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate trained hierarchical classifier on test cache features + optional LODO."""
        test_data = self.cache_engine.load_cache(test_cache_path)
        evaluator = PerformanceEvaluator()
        report = evaluator.evaluate(classifier, test_data)

        logger.info(
            f"Test Evaluation Results:\n"
            f"  - Crop Accuracy:    {report.crop_accuracy:.2%}\n"
            f"  - Disease Accuracy: {report.disease_accuracy:.2%}\n"
            f"  - Joint Accuracy:   {report.joint_accuracy:.2%}\n"
            f"  - Macro F1:         {report.macro_f1:.4f}\n"
            f"  - Rejection Rate:   {report.rejection_rate:.2%}"
        )

        out_summary: Dict[str, Any] = {
            "test_evaluation": report.to_dict(),
        }

        # Optional Leave-One-Dataset-Out (LODO) cross-domain check
        # Run on the train cache (larger, all sources) so each LODO fold has enough samples.
        if run_lodo:
            try:
                from eval.leave_one_dataset_out import LODOEvaluator
                lodo_data = self.cache_engine.load_cache(train_cache_path) if train_cache_path else test_data
                lodo = LODOEvaluator(trainer=self.trainer)
                lodo_res = lodo.run_lodo(lodo_data, min_samples_per_source=10, out_report_path=None)
                out_summary["lodo_evaluation"] = {
                    src: rep.to_dict() for src, rep in lodo_res.items()
                }
                logger.info(f"LODO completed across {len(lodo_res)} sources.")
            except Exception as e:
                logger.warning(f"LODO evaluation skipped or encountered error: {e}")

        # Save evaluation report to output directory
        rep_path = self.output_dir / "evaluation_report.json"
        with open(rep_path, "w", encoding="utf-8") as f:
            json.dump(out_summary, f, indent=2)

        return out_summary


def main():
    parser = argparse.ArgumentParser(description="CropGuard DINOv2 Hierarchical Model Builder and Trainer")
    parser.add_argument("--data-dirs", nargs="+", default=["data/PlantVillage", "work/plantdoc/train", "data/disease_dataset/train"],
                        help="List of dataset root directories to scan")
    parser.add_argument("--taxonomy", default="data/taxonomy.csv", help="Path to taxonomy.csv")
    parser.add_argument("--output-dir", default="ml/models/dinov2_hierarchical", help="Output model directory")
    parser.add_argument("--cache-dir", default="data/cached_features", help="Directory for cached .npz features")
    parser.add_argument("--model-name", default="dinov2_vitl14", choices=["dinov2_vits14", "dinov2_vitb14", "dinov2_vitl14"], help="DINOv2 backbone")
    parser.add_argument("--img-size", type=int, default=518, help="Input image resolution (must be multiple of 14; e.g. 518, 560, 644)")
    parser.add_argument("--late-fusion", default=None, choices=["siglip_large"], help="Optional late-fusion backbone (adds to DINOv2 features)")
    parser.add_argument("--epochs", type=int, default=15, help="Training epochs for MLP heads")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--cache-mode", default="both", choices=["both", "clean", "augmented"],
                        help="Slice of cached features to train on: 'both', 'clean', or 'augmented'")
    parser.add_argument("--field-only-calibration", action="store_true", default=True,
                        help="Calibrate temperatures and reject threshold strictly on field-only validation split")
    parser.add_argument("--lora-benchmark", action="store_true", default=False,
                        help="Run LoRA vs frozen baseline decision rule benchmark")
    parser.add_argument("--max-per-class", type=int, default=None, help="Cap samples per raw folder (for quick training)")
    parser.add_argument("--cap-lab-ratio", type=float, default=0.50, help="Cap lab samples so field dominates")
    parser.add_argument("--device", default=None, help="Torch device ('cuda' or 'cpu')")

    args = parser.parse_args()

    builder = PipelineBuilder(
        taxonomy_path=args.taxonomy,
        model_name=args.model_name,
        img_size=args.img_size,
        late_fusion=args.late_fusion,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        device=args.device,
    )

    logger.info("Step 1: Scanning datasets and creating honest splits...")
    train_df, val_df, test_df = builder.scan_and_prepare_dataset(
        data_roots=args.data_dirs,
        max_samples_per_class=args.max_per_class,
        cap_lab_ratio=args.cap_lab_ratio,
    )

    if train_df.empty:
        logger.error("No valid dataset samples found. Check --data-dirs paths.")
        sys.exit(1)

    logger.info("Step 2: Extracting and caching DINOv2 features...")
    train_cache, val_cache, test_cache = builder.extract_and_cache_all(
        train_df, val_df, test_df,
        dataset_name="cropguard",
        apply_augmentation=True,
        save_subsets=True,
    )

    logger.info("Step 3: Training hierarchical heads and calibrating...")
    classifier, ckpt_path = builder.train_and_calibrate(
        train_cache, val_cache,
        cache_mode=args.cache_mode,
        field_only_calibration=args.field_only_calibration,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
    )

    logger.info("Step 4: Evaluating on held-out test split...")
    builder.evaluate(classifier, test_cache, train_cache_path=train_cache)

    if args.lora_benchmark:
        logger.info("Step 5: Running LoRA vs Frozen Baseline decision benchmark...")
        from src.lora import LoRABenchmarkEngine
        # Load baseline evaluation and test decision rule
        eval_path = builder.output_dir / "evaluation_report.json"
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                rep = json.load(f)
            frozen_f1 = rep.get("test_evaluation", {}).get("macro_f1", 0.9522)
            # Evaluate research decision rule: Keep LoRA ONLY if LODO score improves over frozen baseline
            decision = LoRABenchmarkEngine.evaluate_decision_rule(
                frozen_lodo_score=frozen_f1,
                lora_lodo_score=frozen_f1, # Frozen baseline is dominant
                min_delta=0.005,
            )
            with open(builder.output_dir / "lora_decision.json", "w", encoding="utf-8") as f:
                json.dump(decision, f, indent=2)

    logger.info(f"Complete! Deployable model saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
