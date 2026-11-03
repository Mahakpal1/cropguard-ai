"""Explainability and Physiological Grounding Engine for CropGuard.

Implements:
1. ViT Reshape Transform: Converts (B, 1+N, C) sequence tokens into spatial (B, C, H, W) feature maps.
2. DINOv2GradCAM: Precision Grad-CAM++ lesion localization on the final Vision Transformer block.
3. LeafOverlapVerifier: Computes leaf-overlap ratio (heat inside leaf / total heat).
   Detects explainability drift onto background soil/clutter and flags ungrounded predictions.
4. Heatmap Visualizer: Colorizes and blends heatmaps over the original RGB leaf photo.
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget


@dataclass
class ExplainabilityResult:
    """Detailed explainability report for a model prediction."""
    heatmap: np.ndarray                # 2D float32 array (224, 224) in [0.0, 1.0]
    overlay_rgb: np.ndarray            # 3D uint8 array (224, 224, 3) blended visualization
    leaf_overlap_score: float          # Fraction of heatmap energy situated strictly within the leaf mask [0.0 - 1.0]
    is_grounded: bool                  # True if leaf_overlap_score >= threshold (default 0.65)
    status_note: str                   # Human-readable grounding status
    target_class_index: int            # Class index targeted by Grad-CAM++
    target_class_name: str             # Canonical name of targeted crop or disease


def vit_reshape_transform(tensor: torch.Tensor, height: int = 16, width: int = 16) -> torch.Tensor:
    """
    Transforms 1D patch tokens into 2D spatial feature map for Vision Transformer Grad-CAM.
    Input: (B, 1 + N, C) where index 0 is the [CLS] token.
    Output: (B, C, height, width).
    """
    if tensor.shape[1] == 1 + height * width:
        # Strip [CLS] token and reshape spatial tokens
        result = tensor[:, 1:, :].reshape(tensor.size(0), height, width, tensor.size(2))
    elif tensor.shape[1] == height * width:
        result = tensor.reshape(tensor.size(0), height, width, tensor.size(2))
    else:
        # Approximate square if custom spatial resolution
        h = int(np.sqrt(tensor.shape[1]))
        result = tensor[:, :h * h, :].reshape(tensor.size(0), h, h, tensor.size(2))

    # Permute channels to standard CNN order: (B, C, H, W)
    return result.transpose(2, 3).transpose(1, 2)


class SingleHeadModelWrapper(nn.Module):
    """Wraps DINOv2 backbone and a specific head into a single callable PyTorch module."""

    def __init__(self, backbone: nn.Module, head: nn.Module):
        super().__init__()
        self.backbone = backbone
        self.head = head

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.backbone(x)
        feat = torch.nn.functional.normalize(feat, dim=-1)
        return self.head(feat)


class LeafOverlapVerifier:
    """Verifies that model attention is grounded on foliar tissue rather than background noise."""

    def __init__(self, grounding_threshold: float = 0.65):
        """
        Args:
            grounding_threshold: Minimum fraction of activation energy that must reside inside leaf mask.
        """
        self.grounding_threshold = grounding_threshold

    def evaluate(self, heatmap: np.ndarray, leaf_mask: np.ndarray) -> Tuple[float, bool, str]:
        """
        Compute fraction of heat located inside leaf mask.
        Returns:
            (overlap_score, is_grounded, status_message)
        """
        # Ensure identical spatial shape
        if heatmap.shape != leaf_mask.shape:
            leaf_mask = cv2.resize(leaf_mask, (heatmap.shape[1], heatmap.shape[0]), interpolation=cv2.INTER_NEAREST)

        mask_binary = (leaf_mask > 0).astype(np.float32)
        total_heat = float(np.sum(heatmap)) + 1e-7
        leaf_heat = float(np.sum(heatmap * mask_binary))

        overlap_score = float(leaf_heat / total_heat)
        is_grounded = overlap_score >= self.grounding_threshold

        if is_grounded:
            note = f"Well-grounded: {overlap_score:.1%} of diagnostic attention is concentrated on leaf tissue."
        else:
            note = (
                f"Attention warning: Only {overlap_score:.1%} of attention is on the leaf; "
                f"model may be cueing on background context (soil, lighting, or foreign textures)."
            )

        return overlap_score, is_grounded, note


class DINOv2GradCAM:
    """Generates Grad-CAM++ heatmaps from frozen DINOv2 Vision Transformers."""

    def __init__(
        self,
        backbone: nn.Module,
        verifier: Optional[LeafOverlapVerifier] = None,
        device: Optional[str] = None,
    ):
        self.backbone = backbone
        self.verifier = verifier or LeafOverlapVerifier()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.backbone.to(self.device)

        # Target final transformer block norm layer
        if hasattr(self.backbone, "blocks") and len(self.backbone.blocks) > 0:
            last_block = self.backbone.blocks[-1]
            self.target_layer = last_block.norm1 if hasattr(last_block, "norm1") else last_block
        else:
            self.target_layer = self.backbone

    def generate_cam(
        self,
        head: nn.Module,
        input_tensor: torch.Tensor,
        raw_rgb: Image.Image,
        leaf_mask: np.ndarray,
        target_class_idx: int,
        target_class_name: str = "Disease",
        alpha: float = 0.50,
    ) -> ExplainabilityResult:
        """
        Compute Grad-CAM++ heatmap for the specified target class.
        """
        head.to(self.device)
        wrapper = SingleHeadModelWrapper(self.backbone, head).to(self.device)
        wrapper.eval()

        cam_engine = GradCAMPlusPlus(
            model=wrapper,
            target_layers=[self.target_layer],
            reshape_transform=vit_reshape_transform,
        )

        input_tensor = input_tensor.to(self.device)
        targets = [ClassifierOutputTarget(target_class_idx)]

        # Generate 2D grayscale heatmap in [0.0, 1.0]
        grayscale_cam = cam_engine(input_tensor=input_tensor, targets=targets)[0]

        # Evaluate physiological leaf overlap
        overlap_score, is_grounded, note = self.verifier.evaluate(grayscale_cam, leaf_mask)

        # Create blended RGB overlay
        rgb_np = np.array(raw_rgb.convert("RGB").resize((224, 224))) / 255.0
        heatmap_colored = cv2.applyColorMap(np.uint8(255 * grayscale_cam), cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB) / 255.0

        overlay = (1.0 - alpha) * rgb_np + alpha * heatmap_colored
        overlay = np.clip(overlay * 255.0, 0, 255).astype(np.uint8)

        return ExplainabilityResult(
            heatmap=grayscale_cam.astype(np.float32),
            overlay_rgb=overlay,
            leaf_overlap_score=overlap_score,
            is_grounded=is_grounded,
            status_note=note,
            target_class_index=target_class_idx,
            target_class_name=target_class_name,
        )

    @staticmethod
    def overlay_to_png_bytes(overlay_rgb: np.ndarray) -> bytes:
        """Encode RGB overlay array into compressed PNG bytes."""
        pil = Image.fromarray(overlay_rgb)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def overlay_to_base64_data_uri(overlay_rgb: np.ndarray) -> str:
        """Encode RGB overlay array into base64 image data URI for direct frontend display."""
        raw_bytes = DINOv2GradCAM.overlay_to_png_bytes(overlay_rgb)
        b64 = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"
