"""End-to-End Inference Engine for CropGuard.

Executes the complete 5-layer pipeline:
Photo -> [0] Leaf Localizer (15% margin)
      -> [1] Frozen DINOv2 Feature Extractor
      -> [2] Crop Head (softmax over crops + unsupported)
      -> [3] Disease Head per crop
      -> [4] Calibration & Energy Gate
      -> [5] Grad-CAM++ with Leaf Overlap Quality Check
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

from src.extract_features import DINOv2FeatureExtractor
from src.gradcam import DINOv2GradCAM, ExplainabilityResult, LeafOverlapVerifier
from src.heads import HierarchicalClassifier, HierarchicalPrediction
from src.localize import LeafLocalizer, LocalizationResult


@dataclass
class EndToEndDiagnosis:
    """Final output of the CropGuard AI diagnosis pipeline."""
    crop: str
    disease: str
    canonical_key: str
    confidence: float                  # Joint probability P(crop) * P(disease | crop)
    crop_confidence: float             # P(crop)
    disease_confidence: float          # P(disease | crop)
    status: str                        # 'CONFIDENT', 'UNCERTAIN_CROP', 'UNGROUNDED_ATTENTION', 'REJECTED'
    is_supported: bool
    energy_score: float
    leaf_overlap_score: Optional[float] = None
    is_grounded: Optional[bool] = None
    explainability_note: Optional[str] = None
    heatmap_data_uri: Optional[str] = None
    top2_crop: Optional[str] = None
    top2_disease: Optional[str] = None
    top2_confidence: Optional[float] = None


class CropGuardInferenceEngine:
    """Full inference orchestrator."""

    def __init__(
        self,
        classifier: HierarchicalClassifier,
        model_name: str = "dinov2_vits14",
        grounding_threshold: float = 0.65,
        device: Optional[str] = None,
    ):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.classifier = classifier.to(self.device)
        self.classifier.eval()

        self.localizer = LeafLocalizer(margin=0.15, target_size=(224, 224))
        self.extractor = DINOv2FeatureExtractor(model_name=model_name, device=str(self.device))
        self.gradcam_engine = DINOv2GradCAM(
            backbone=self.extractor.model,
            verifier=LeafOverlapVerifier(grounding_threshold=grounding_threshold),
            device=str(self.device),
        )

        self.transform = T.Compose([
            T.Resize((224, 224), interpolation=T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Union[str, Path],
        model_name: Optional[str] = None,
        grounding_threshold: float = 0.65,
        device: Optional[str] = None,
    ) -> CropGuardInferenceEngine:
        """Instantiate CropGuardInferenceEngine directly from a saved checkpoint file."""
        ckpt = torch.load(checkpoint_path, map_location=device or "cpu")
        in_feat = ckpt["in_features"]
        if model_name is None:
            if in_feat == 1024:
                model_name = "dinov2_vitl14"
            elif in_feat == 768:
                model_name = "dinov2_vitb14"
            else:
                model_name = "dinov2_vits14"
        classifier = HierarchicalClassifier(
            in_features=in_feat,
            crop_names=ckpt["crop_names"],
            crop_disease_map=ckpt["crop_disease_map"],
            energy_threshold=ckpt.get("energy_threshold", -2.5),
        )
        classifier.load_state_dict(ckpt["model_state"])
        return cls(
            classifier=classifier,
            model_name=model_name,
            grounding_threshold=grounding_threshold,
            device=device,
        )

    def diagnose(
        self,
        image_input: Union[Image.Image, bytes, np.ndarray],
        explain: bool = True,
    ) -> EndToEndDiagnosis:
        """
        Execute full diagnosis pipeline on input leaf photo.
        """
        # Step 0: Leaf Localization & Mask Extraction
        loc_res: LocalizationResult = self.localizer.localize(image_input)
        if not loc_res.has_leaf:
            return EndToEndDiagnosis(
                crop="Non-Crop / Background",
                disease="No Leaf Detected",
                canonical_key="__non_crop_____not_a_leaf__",
                confidence=0.0,
                crop_confidence=0.0,
                disease_confidence=0.0,
                status="REJECTED",
                is_supported=False,
                energy_score=999.0,
                explainability_note="Rejection gate: No sufficient plant foliage was detected in the photo.",
            )

        cropped_leaf: Image.Image = loc_res.cropped_image
        leaf_mask: np.ndarray = loc_res.leaf_mask

        # Step 1: Feature Extraction with Frozen DINOv2
        feat_vec = self.extractor.extract_image(cropped_leaf)

        # Steps 2, 3, 4: Hierarchical Classification & Energy Gate
        pred: HierarchicalPrediction = self.classifier.predict(feat_vec)

        if not pred.is_supported:
            return EndToEndDiagnosis(
                crop=pred.crop,
                disease=pred.disease,
                canonical_key=pred.canonical_key,
                confidence=pred.confidence,
                crop_confidence=pred.crop_confidence,
                disease_confidence=pred.disease_confidence,
                status="REJECTED",
                is_supported=False,
                energy_score=pred.energy_score,
                explainability_note="System reject: Input is unfamiliar, out-of-distribution, or an unsupported crop.",
            )

        # Step 5: Explainability & Leaf-Overlap Verification
        overlap_score = None
        is_grounded = None
        note = None
        heatmap_uri = None
        status = pred.status

        if explain and pred.crop in self.classifier.disease_heads:
            disease_head = self.classifier.disease_heads[pred.crop]
            disease_list = self.classifier.crop_disease_map.get(pred.crop, [])
            target_idx = disease_list.index(pred.disease) if pred.disease in disease_list else 0

            input_tensor = self.transform(cropped_leaf).unsqueeze(0).to(self.device)
            cam_res: ExplainabilityResult = self.gradcam_engine.generate_cam(
                head=disease_head,
                input_tensor=input_tensor,
                raw_rgb=cropped_leaf,
                leaf_mask=leaf_mask,
                target_class_idx=target_idx,
                target_class_name=pred.disease,
            )

            overlap_score = cam_res.leaf_overlap_score
            is_grounded = cam_res.is_grounded
            note = cam_res.status_note
            heatmap_uri = DINOv2GradCAM.overlay_to_base64_data_uri(cam_res.overlay_rgb)

            # If attention is not grounded on the leaf, downgrade status
            if not is_grounded:
                status = "UNGROUNDED_ATTENTION"

        return EndToEndDiagnosis(
            crop=pred.crop,
            disease=pred.disease,
            canonical_key=pred.canonical_key,
            confidence=pred.confidence,
            crop_confidence=pred.crop_confidence,
            disease_confidence=pred.disease_confidence,
            status=status,
            is_supported=True,
            energy_score=pred.energy_score,
            leaf_overlap_score=overlap_score,
            is_grounded=is_grounded,
            explainability_note=note,
            heatmap_data_uri=heatmap_uri,
            top2_crop=pred.top2_crop,
            top2_disease=pred.top2_disease,
            top2_confidence=pred.top2_confidence,
        )
