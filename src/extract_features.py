"""DINOv2 Frozen Feature Extractor and Dataset Feature Caching Engine.

Extracts normalized 384-d (ViT-S/14), 768-d (ViT-B/14), or 1024-d (ViT-L/14)
self-supervised features from leaf images at high resolutions (518×518px or higher),
applying optional field-adaptation augmentations and optional SigLIP-Large late fusion.
Caches features directly to disk as compressed .npz archives, enabling
instant laptop training of downstream heads in minutes.
"""
from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch
import torchvision.transforms as T
from PIL import Image
from tqdm import tqdm

from src.augment import BackgroundRandomizer, PhotometricFieldAugmenter
from src.localize import LeafLocalizer

logger = logging.getLogger("cropguard.features")


class DINOv2FeatureExtractor:
    """Extracts high-level semantic embeddings from a frozen DINOv2 Vision Transformer,
    with support for high resolutions (518px, 560px, 644px) and optional late fusion (SigLIP-Large).
    """

    def __init__(
        self,
        model_name: str = "dinov2_vitl14",
        device: Optional[str] = None,
        img_size: int = 518,
        late_fusion_backbone: Optional[str] = None,
    ):
        """
        Args:
            model_name: 'dinov2_vits14' (384-d), 'dinov2_vitb14' (768-d), or 'dinov2_vitl14' (1024-d).
            device: 'cuda', 'cpu', or None (auto-detect).
            img_size: Input spatial resolution (default 518, multiple of 14).
            late_fusion_backbone: Optional second backbone (e.g. 'siglip_large' for late fusion).
        """
        self.model_name = model_name
        self.img_size = img_size
        self.late_fusion_backbone = late_fusion_backbone

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()

        # DINOv2 standard preprocessing
        self.transform = T.Compose([
            T.Resize((self.img_size, self.img_size), interpolation=T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Primary feature dimension
        if "vitl14" in model_name or "large" in model_name:
            self.dino_dim = 1024
        elif "vits14" in model_name or "small" in model_name:
            self.dino_dim = 384
        else:
            self.dino_dim = 768

        # Optional second backbone for late fusion
        self.fusion_model = None
        self.fusion_transform = None
        self.fusion_dim = 0
        if late_fusion_backbone:
            self.fusion_model, self.fusion_transform, self.fusion_dim = self._load_fusion_backbone()

        self.feature_dim = self.dino_dim + self.fusion_dim

    def _load_model(self) -> torch.nn.Module:
        """Load frozen DINOv2 model via HuggingFace, torch.hub, or timm fallback."""
        if "vitl14" in self.model_name or "large" in self.model_name:
            try:
                from transformers import AutoModel
                logger.info("Loading facebook/dinov2-large via transformers...")
                return AutoModel.from_pretrained("facebook/dinov2-large")
            except Exception as e:
                logger.warning(f"transformers load failed: {e}. Trying torch.hub...")
        try:
            logger.info(f"Loading {self.model_name} via torch.hub...")
            model = torch.hub.load("facebookresearch/dinov2", self.model_name, trust_repo=True)
            return model
        except Exception as e:
            logger.warning(f"torch.hub failed: {e}. Falling back to timm...")
            import timm
            if "vitl14" in self.model_name or "large" in self.model_name:
                timm_name = "vit_large_patch14_dinov2"
            elif "vits14" in self.model_name or "small" in self.model_name:
                timm_name = "vit_small_patch14_dinov2"
            else:
                timm_name = "vit_base_patch14_dinov2"
            return timm.create_model(timm_name, pretrained=True, num_classes=0, img_size=self.img_size)

    def _load_fusion_backbone(self) -> Tuple[torch.nn.Module, Any, int]:
        """Load SigLIP-Large vision model for late fusion."""
        from transformers import AutoModel
        logger.info(f"Loading late fusion backbone: {self.late_fusion_backbone}...")
        siglip_name = "google/siglip-large-patch16-384"
        siglip = AutoModel.from_pretrained(siglip_name).to(self.device).eval()
        fusion_tf = T.Compose([
            T.Resize((384, 384), interpolation=T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
        return siglip, fusion_tf, 1024

    def _forward_dino(self, tensors: torch.Tensor) -> torch.Tensor:
        """Extract L2-normalized feature representation from DINOv2."""
        out = self.model(tensors)
        if hasattr(out, "last_hidden_state"):
            feat = out.last_hidden_state[:, 0]
        elif isinstance(out, torch.Tensor):
            feat = out
        else:
            feat = out[0]
        return torch.nn.functional.normalize(feat, dim=-1)

    def _forward_fusion(self, tensors: torch.Tensor) -> torch.Tensor:
        """Extract L2-normalized feature representation from SigLIP."""
        if hasattr(self.fusion_model, "vision_model"):
            out = self.fusion_model.vision_model(tensors)
            feat = out.pooler_output
        else:
            out = self.fusion_model(tensors)
            feat = out.pooler_output if hasattr(out, "pooler_output") else out[0]
        return torch.nn.functional.normalize(feat, dim=-1)

    @torch.no_grad()
    def extract_image(self, image: Union[Image.Image, np.ndarray, bytes]) -> np.ndarray:
        """
        Extract feature vector for a single image.
        Returns:
            1D float32 numpy array of shape (feature_dim,).
        """
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        image = image.convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        feat = self._forward_dino(tensor)

        if self.fusion_model is not None and self.fusion_transform is not None:
            f_tensor = self.fusion_transform(image).unsqueeze(0).to(self.device)
            f_feat = self._forward_fusion(f_tensor)
            feat = torch.cat([feat, f_feat], dim=-1)
            feat = torch.nn.functional.normalize(feat, dim=-1)

        return feat.cpu().squeeze(0).numpy().astype(np.float32)

    @torch.no_grad()
    def extract_batch(self, images: List[Image.Image], batch_size: int = 16) -> np.ndarray:
        """
        Extract feature vectors for a list of PIL Images in batches.
        Returns:
            2D float32 numpy array of shape (len(images), feature_dim).
        """
        all_feats = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            tensors = torch.stack([self.transform(img.convert("RGB")) for img in batch]).to(self.device)
            feats = self._forward_dino(tensors)

            if self.fusion_model is not None and self.fusion_transform is not None:
                f_tensors = torch.stack([self.fusion_transform(img.convert("RGB")) for img in batch]).to(self.device)
                f_feats = self._forward_fusion(f_tensors)
                feats = torch.cat([feats, f_feats], dim=-1)
                feats = torch.nn.functional.normalize(feats, dim=-1)

            all_feats.append(feats.cpu().numpy())

        if not all_feats:
            return np.empty((0, self.feature_dim), dtype=np.float32)
        return np.vstack(all_feats).astype(np.float32)


class FeatureCacheEngine:
    """Extracts and stores dataset features into compressed .npz archives."""

    def __init__(
        self,
        extractor: Optional[DINOv2FeatureExtractor] = None,
        localizer: Optional[LeafLocalizer] = None,
        augmenter: Optional[PhotometricFieldAugmenter] = None,
        randomizer: Optional[BackgroundRandomizer] = None,
    ):
        self.extractor = extractor or DINOv2FeatureExtractor()
        self.localizer = localizer or LeafLocalizer()
        self.augmenter = augmenter or PhotometricFieldAugmenter()
        self.randomizer = randomizer or BackgroundRandomizer(background_dir="data/raw/generic_negative")

    def process_and_cache(
        self,
        samples_df: pd.DataFrame,
        out_npz_path: str,
        apply_augmentation: bool = True,
        save_subsets: bool = False,
        batch_size: int = 32,
    ) -> Dict[str, Union[int, str]]:
        """
        Process images: localize -> optional augment -> extract DINOv2 features -> cache to .npz.
        If save_subsets is True, also saves clean and augmented slices separately.
        """
        out_path = Path(out_npz_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Build label indices
        crops = sorted(samples_df["canonical_crop"].unique().tolist())
        crop_to_idx = {c: i for i, c in enumerate(crops)}

        # Build global disease map & per-crop disease maps
        diseases = sorted(samples_df["canonical_disease"].unique().tolist())
        disease_to_idx = {d: i for i, d in enumerate(diseases)}

        crop_disease_map: Dict[str, List[str]] = {}
        for _, row in samples_df.iterrows():
            c, d = row["canonical_crop"], row["canonical_disease"]
            crop_disease_map.setdefault(c, set()).add(d)
        crop_disease_map = {k: sorted(list(v)) for k, v in crop_disease_map.items()}

        features_list: List[np.ndarray] = []
        crop_labels: List[int] = []
        disease_labels: List[int] = []
        canonical_keys: List[str] = []
        is_lab_list: List[bool] = []
        source_ids: List[str] = []
        leaf_group_ids: List[str] = []

        batch_imgs: List[Image.Image] = []
        batch_metadata: List[Tuple] = []

        logger.info(f"Extracting features for {len(samples_df)} samples...")

        for _, row in tqdm(samples_df.iterrows(), total=len(samples_df), desc="Caching features"):
            img_path = Path(row["image_path"])
            if not img_path.exists():
                continue

            try:
                # 1. Localize leaf with 15% margin
                with Image.open(img_path) as raw_img:
                    loc_res = self.localizer.localize(raw_img)
                    leaf_crop = loc_res.cropped_image
                    mask = loc_res.leaf_mask

                # 2. Add raw crop to batch
                batch_imgs.append(leaf_crop)
                batch_metadata.append((
                    crop_to_idx[row["canonical_crop"]],
                    disease_to_idx[row["canonical_disease"]],
                    row["canonical_key"],
                    bool(row.get("is_lab", False)),
                    str(row.get("source", "unknown")),
                    str(row.get("leaf_group_id", "none")),
                ))

                # 3. If lab image and augmentation requested: add augmented field version
                if apply_augmentation and row.get("is_lab", False):
                    aug_img = self.augmenter.augment(
                        leaf_crop,
                        p_randomize_bg=0.75,
                        leaf_mask=mask,
                        randomizer=self.randomizer,
                    )
                    batch_imgs.append(aug_img)
                    batch_metadata.append((
                        crop_to_idx[row["canonical_crop"]],
                        disease_to_idx[row["canonical_disease"]],
                        row["canonical_key"],
                        False,  # Augmented counts as field proxy
                        str(row.get("source", "unknown")) + "_aug",
                        str(row.get("leaf_group_id", "none")),
                    ))

                # Flush batch
                if len(batch_imgs) >= batch_size:
                    feats = self.extractor.extract_batch(batch_imgs, batch_size=batch_size)
                    features_list.append(feats)
                    for m in batch_metadata:
                        crop_labels.append(m[0])
                        disease_labels.append(m[1])
                        canonical_keys.append(m[2])
                        is_lab_list.append(m[3])
                        source_ids.append(m[4])
                        leaf_group_ids.append(m[5])
                    batch_imgs = []
                    batch_metadata = []

            except Exception as e:
                logger.warning(f"Failed processing {img_path}: {e}")

        # Flush remaining
        if batch_imgs:
            feats = self.extractor.extract_batch(batch_imgs, batch_size=batch_size)
            features_list.append(feats)
            for m in batch_metadata:
                crop_labels.append(m[0])
                disease_labels.append(m[1])
                canonical_keys.append(m[2])
                is_lab_list.append(m[3])
                source_ids.append(m[4])
                leaf_group_ids.append(m[5])

        if features_list:
            all_feats = np.vstack(features_list)
        else:
            all_feats = np.empty((0, self.extractor.feature_dim), dtype=np.float32)

        crop_labels_arr = np.array(crop_labels, dtype=np.int64)
        disease_labels_arr = np.array(disease_labels, dtype=np.int64)
        canonical_keys_arr = np.array(canonical_keys, dtype=object)
        is_lab_arr = np.array(is_lab_list, dtype=bool)
        source_ids_arr = np.array(source_ids, dtype=object)
        leaf_group_ids_arr = np.array(leaf_group_ids, dtype=object)

        # Save to compressed .npz archive
        np.savez_compressed(
            out_path,
            features=all_feats,
            crop_labels=crop_labels_arr,
            disease_labels=disease_labels_arr,
            canonical_keys=canonical_keys_arr,
            is_lab=is_lab_arr,
            source_ids=source_ids_arr,
            leaf_group_ids=leaf_group_ids_arr,
            crop_to_idx_json=json.dumps(crop_to_idx),
            disease_to_idx_json=json.dumps(disease_to_idx),
            crop_disease_map_json=json.dumps(crop_disease_map),
        )

        logger.info(f"Successfully cached {len(all_feats)} feature vectors to {out_path}")

        # Also save explicit clean and augmented subsets if requested
        if save_subsets and len(all_feats) > 0:
            is_aug = np.array([str(s).endswith("_aug") for s in source_ids_arr], dtype=bool)
            clean_path = out_path.with_name(f"{out_path.stem}_clean{out_path.suffix}")
            aug_path = out_path.with_name(f"{out_path.stem}_aug{out_path.suffix}")

            # Save clean subset
            np.savez_compressed(
                clean_path,
                features=all_feats[~is_aug],
                crop_labels=crop_labels_arr[~is_aug],
                disease_labels=disease_labels_arr[~is_aug],
                canonical_keys=canonical_keys_arr[~is_aug],
                is_lab=is_lab_arr[~is_aug],
                source_ids=source_ids_arr[~is_aug],
                leaf_group_ids=leaf_group_ids_arr[~is_aug],
                crop_to_idx_json=json.dumps(crop_to_idx),
                disease_to_idx_json=json.dumps(disease_to_idx),
                crop_disease_map_json=json.dumps(crop_disease_map),
            )
            # Save augmented subset
            np.savez_compressed(
                aug_path,
                features=all_feats[is_aug],
                crop_labels=crop_labels_arr[is_aug],
                disease_labels=disease_labels_arr[is_aug],
                canonical_keys=canonical_keys_arr[is_aug],
                is_lab=is_lab_arr[is_aug],
                source_ids=source_ids_arr[is_aug],
                leaf_group_ids=leaf_group_ids_arr[is_aug],
                crop_to_idx_json=json.dumps(crop_to_idx),
                disease_to_idx_json=json.dumps(disease_to_idx),
                crop_disease_map_json=json.dumps(crop_disease_map),
            )
            logger.info(f"Saved subset caches: {clean_path.name} (N={(~is_aug).sum()}) and {aug_path.name} (N={is_aug.sum()})")

        return {
            "cached_samples": int(len(all_feats)),
            "feature_dim": int(self.extractor.feature_dim),
            "output_path": str(out_path),
            "num_crops": len(crops),
            "num_diseases": len(diseases),
        }

    @staticmethod
    def load_cache(npz_path: str) -> Dict[str, Union[np.ndarray, dict]]:
        """Load and unpack a cached .npz feature archive."""
        data = np.load(npz_path, allow_pickle=True)
        return {
            "features": data["features"],
            "crop_labels": data["crop_labels"],
            "disease_labels": data["disease_labels"],
            "canonical_keys": data["canonical_keys"],
            "is_lab": data["is_lab"],
            "source_ids": data["source_ids"],
            "leaf_group_ids": data["leaf_group_ids"],
            "crop_to_idx": json.loads(str(data["crop_to_idx_json"])),
            "disease_to_idx": json.loads(str(data["disease_to_idx_json"])),
            "crop_disease_map": json.loads(str(data["crop_disease_map_json"])),
        }

    @classmethod
    def split_clean_and_augmented(
        cls,
        cache_data: Dict[str, Union[np.ndarray, dict]],
    ) -> Tuple[Dict[str, Union[np.ndarray, dict]], Dict[str, Union[np.ndarray, dict]]]:
        """
        Partition cached feature dictionary into clean (unaugmented) and augmented subsets.
        Augmented samples are identified by '_aug' in source_ids.
        """
        source_ids = cache_data["source_ids"]
        is_aug = np.array([str(s).endswith("_aug") for s in source_ids], dtype=bool)

        def _slice(mask):
            return {
                "features": cache_data["features"][mask],
                "crop_labels": cache_data["crop_labels"][mask],
                "disease_labels": cache_data["disease_labels"][mask],
                "canonical_keys": cache_data["canonical_keys"][mask],
                "is_lab": cache_data["is_lab"][mask],
                "source_ids": cache_data["source_ids"][mask],
                "leaf_group_ids": cache_data["leaf_group_ids"][mask],
                "crop_to_idx": cache_data["crop_to_idx"],
                "disease_to_idx": cache_data["disease_to_idx"],
                "crop_disease_map": cache_data["crop_disease_map"],
            }

        return _slice(~is_aug), _slice(is_aug)

    @classmethod
    def get_unaugmented_subset(
        cls,
        cache_data: Dict[str, Union[np.ndarray, dict]],
    ) -> Dict[str, Union[np.ndarray, dict]]:
        """Return subset containing only clean unaugmented samples."""
        clean, _ = cls.split_clean_and_augmented(cache_data)
        return clean

    @classmethod
    def get_augmented_subset(
        cls,
        cache_data: Dict[str, Union[np.ndarray, dict]],
    ) -> Dict[str, Union[np.ndarray, dict]]:
        """Return subset containing only augmented samples."""
        _, aug = cls.split_clean_and_augmented(cache_data)
        return aug

    @classmethod
    def filter_cache(
        cls,
        cache_data: Dict[str, Union[np.ndarray, dict]],
        mode: str = "both",
    ) -> Dict[str, Union[np.ndarray, dict]]:
        """Filter cache by mode: 'both', 'clean', or 'augmented'."""
        mode = mode.lower()
        if mode == "clean":
            return cls.get_unaugmented_subset(cache_data)
        elif mode == "augmented":
            return cls.get_augmented_subset(cache_data)
        return cache_data
