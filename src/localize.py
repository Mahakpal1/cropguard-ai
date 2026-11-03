"""Leaf Localizer and Segmentation Module for CropGuard.

Detects, segments, and crops the primary leaf area with a configurable margin (10-15%).
Generates binary leaf masks used both for background-isolated cropping and for
Layer 5's Grad-CAM leaf-overlap validation metric.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image


@dataclass
class LocalizationResult:
    """Output of the leaf localization and segmentation pipeline."""
    cropped_image: Image.Image         # Padded crop resized to target_size (default 224x224)
    leaf_mask: np.ndarray              # Binary mask (target_size) where 255=leaf, 0=background
    original_bbox: Tuple[int, int, int, int]  # (ymin, xmin, ymax, xmax) on raw image
    leaf_coverage_ratio: float         # Fraction of raw image occupied by leaf tissue
    has_leaf: bool                     # False if image lacks sufficient plant/foliage material
    confidence: float                  # Quality score of the leaf detection [0.0 - 1.0]


class LeafLocalizer:
    """Fast, robust leaf detection and segmentation using multi-cue color and morphological analysis."""

    def __init__(
        self,
        margin: float = 0.15,
        min_leaf_ratio: float = 0.04,
        target_size: Tuple[int, int] = (224, 224),
    ):
        """
        Args:
            margin: Extra padding around detected leaf bounding box (default: 0.15 = 15%).
            min_leaf_ratio: Minimum fraction of pixels that must be leaf tissue to pass leaf gate.
            target_size: Output resolution for cropped image and mask (W, H).
        """
        self.margin = margin
        self.min_leaf_ratio = min_leaf_ratio
        self.target_size = target_size

    def _to_cv2(self, image: Union[Image.Image, np.ndarray, bytes]) -> np.ndarray:
        """Convert input to standard BGR OpenCV format."""
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        if isinstance(image, Image.Image):
            rgb = np.array(image.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        elif isinstance(image, np.ndarray):
            if image.ndim == 2:
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            return image
        raise ValueError(f"Unsupported image type: {type(image)}")

    def segment_leaf(self, bgr: np.ndarray) -> np.ndarray:
        """
        Produce a binary mask for leaf tissue, including diseased (chlorotic, necrotic) regions.
        Combines HSV vegetation mask, Excess Green Index (ExG), and Lab luminance/a* thresholds.
        """
        h, w = bgr.shape[:2]

        # 1. HSV Segmentation: Covers healthy green, chlorotic yellow, and necrotic brown
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        
        # Green & yellow-green foliage
        lower_green = np.array([25, 30, 30])
        upper_green = np.array([88, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)

        # Yellow, chlorotic, and early necrotic spots
        lower_yellow = np.array([12, 40, 40])
        upper_yellow = np.array([25, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 2. Excess Green Index (ExG): 2*G - R - B (normalised)
        b, g, r = cv2.split(bgr.astype(np.float32))
        total = b + g + r + 1e-6
        rn, gn, bn = r / total, g / total, b / total
        exg = 2.0 * gn - rn - bn
        mask_exg = (exg > 0.05).astype(np.uint8) * 255

        # 3. Lab Color Space: negative a* represents green-shifted pixels
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)
        mask_lab = (a_chan < 125).astype(np.uint8) * 255

        # Combined candidate mask
        combined = cv2.bitwise_or(mask_green, mask_yellow)
        combined = cv2.bitwise_or(combined, mask_exg)
        combined = cv2.bitwise_or(combined, mask_lab)

        # 4. Morphological filtering to remove dust/noise and bridge interior lesion holes
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open, iterations=1)

        # 5. Extract significant leaf components (ignore tiny background specs)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned)
        if num_labels <= 1:
            return np.zeros((h, w), dtype=np.uint8)

        min_area = int(0.005 * h * w)  # At least 0.5% of total image area
        final_mask = np.zeros((h, w), dtype=np.uint8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                final_mask[labels == i] = 255

        return final_mask

    def localize(self, image: Union[Image.Image, np.ndarray, bytes]) -> LocalizationResult:
        """
        Locate leaf, compute bounding box with 10-15% padding, crop, and resize.
        """
        bgr = self._to_cv2(image)
        h, w = bgr.shape[:2]

        leaf_mask = self.segment_leaf(bgr)
        leaf_pixels = cv2.countNonZero(leaf_mask)
        leaf_coverage = leaf_pixels / float(h * w)

        # Leaf presence check
        has_leaf = leaf_coverage >= self.min_leaf_ratio

        if not has_leaf or leaf_pixels == 0:
            # Fallback to center-crop if no clean leaf contour found
            rgb_full = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil_crop = Image.fromarray(rgb_full).resize(self.target_size, Image.Resampling.BICUBIC)
            mask_crop = np.zeros(self.target_size, dtype=np.uint8)
            return LocalizationResult(
                cropped_image=pil_crop,
                leaf_mask=mask_crop,
                original_bbox=(0, 0, h, w),
                leaf_coverage_ratio=float(leaf_coverage),
                has_leaf=False,
                confidence=float(leaf_coverage),
            )

        # Compute bounding rectangle around all leaf pixels
        y_indices, x_indices = np.where(leaf_mask > 0)
        ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
        xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))

        bbox_h = ymax - ymin
        bbox_w = xmax - xmin

        # Add 10-15% padding margin
        pad_y = int(bbox_h * self.margin)
        pad_x = int(bbox_w * self.margin)

        crop_ymin = max(0, ymin - pad_y)
        crop_ymax = min(h, ymax + pad_y)
        crop_xmin = max(0, xmin - pad_x)
        crop_xmax = min(w, xmax + pad_x)

        # Slice crop
        bgr_crop = bgr[crop_ymin:crop_ymax, crop_xmin:crop_xmax]
        mask_crop_raw = leaf_mask[crop_ymin:crop_ymax, crop_xmin:crop_xmax]

        # Convert to RGB and resize to target_size
        rgb_crop = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2RGB)
        pil_crop = Image.fromarray(rgb_crop).resize(self.target_size, Image.Resampling.BICUBIC)
        mask_crop = cv2.resize(mask_crop_raw, self.target_size, interpolation=cv2.INTER_NEAREST)

        confidence = min(1.0, leaf_coverage * 2.5)

        return LocalizationResult(
            cropped_image=pil_crop,
            leaf_mask=mask_crop,
            original_bbox=(crop_ymin, crop_xmin, crop_ymax, crop_xmax),
            leaf_coverage_ratio=float(leaf_coverage),
            has_leaf=True,
            confidence=float(confidence),
        )
