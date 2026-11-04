"""Field Augmentation and Background Randomization for CropGuard.

Closes the lab-to-field domain gap without needing manual field photos:
1. Background Randomizer: Segments lab leaves and composites them onto realistic field backgrounds
   (soil, weed patches, field clutter) with alpha edge feathering.
2. Photometric Field Augmenter: Simulates real-world outdoor smartphone capture conditions
   (harsh sun/shadow jitter, motion blur, WhatsApp JPEG compression, partial stem occlusion).
"""
from __future__ import annotations

import io
import random
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


class BackgroundRandomizer:
    """Composites segmented leaf foreground onto field-style backgrounds."""

    def __init__(self, background_dir: Optional[str] = None):
        """
        Args:
            background_dir: Optional path to folder containing background images (soil, fields, weeds).
                            If empty or None, procedural field backgrounds are generated.
        """
        self.background_dir = background_dir
        self._bg_paths: List[str] = []
        if background_dir:
            from pathlib import Path
            p = Path(background_dir)
            if p.exists():
                self._bg_paths = [str(f) for f in p.rglob("*.*") if f.suffix.lower() in (".jpg", ".jpeg", ".png")]

    @staticmethod
    def generate_procedural_field_background(shape: Tuple[int, int]) -> np.ndarray:
        """
        Generate a realistic field background (soil, loam, weed greenery, dry leaves)
        using multi-scale Perlin/Gaussian textures.
        """
        h, w = shape
        bg_type = random.choice(["soil", "weeds", "mulch", "mixed"])

        if bg_type == "soil":
            # Rich brown/dark loam tones
            base_color = np.array([30, 45, 65], dtype=np.float32)  # BGR
            noise = np.random.normal(0, 15, (h, w, 3)).astype(np.float32)
            bg = np.clip(base_color + noise, 0, 255).astype(np.uint8)
            bg = cv2.GaussianBlur(bg, (9, 9), 0)
        elif bg_type == "weeds":
            # Desaturated background weed greens and shadows
            base_color = np.array([35, 75, 45], dtype=np.float32)  # BGR
            noise = np.random.normal(0, 25, (h, w, 3)).astype(np.float32)
            bg = np.clip(base_color + noise, 0, 255).astype(np.uint8)
            bg = cv2.GaussianBlur(bg, (13, 13), 0)
        elif bg_type == "mulch":
            # Dry straw, hay, dried crop mulch
            base_color = np.array([40, 80, 110], dtype=np.float32)  # BGR
            noise = np.random.normal(0, 20, (h, w, 3)).astype(np.float32)
            bg = np.clip(base_color + noise, 0, 255).astype(np.uint8)
        else:
            # Multi-patch field clutter
            base = np.zeros((h, w, 3), dtype=np.uint8)
            base[:, :w // 2] = [35, 50, 70]   # Soil
            base[:, w // 2:] = [40, 80, 50]   # Foliage
            noise = np.random.normal(0, 20, (h, w, 3)).astype(np.float32)
            bg = np.clip(base + noise, 0, 255).astype(np.uint8)
            bg = cv2.GaussianBlur(bg, (21, 21), 0)

        return bg

    def composite(
        self,
        leaf_bgr: np.ndarray,
        leaf_mask: np.ndarray,
        feather_radius: int = 5,
    ) -> np.ndarray:
        """
        Blend leaf foreground into a field background using anti-aliased alpha feathering.
        """
        h, w = leaf_bgr.shape[:2]

        # Get or generate background
        if self._bg_paths and random.random() < 0.6:
            bg_file = random.choice(self._bg_paths)
            bg_raw = cv2.imread(bg_file)
            if bg_raw is not None:
                bg = cv2.resize(bg_raw, (w, h))
            else:
                bg = self.generate_procedural_field_background((h, w))
        else:
            bg = self.generate_procedural_field_background((h, w))

        # Feather mask edges to eliminate hard cutout seams
        mask_float = (leaf_mask > 127).astype(np.float32)
        if feather_radius > 0:
            k = feather_radius * 2 + 1
            alpha = cv2.GaussianBlur(mask_float, (k, k), 0)[:, :, np.newaxis]
        else:
            alpha = mask_float[:, :, np.newaxis]

        # Alpha composite: F * alpha + B * (1 - alpha)
        blended = (leaf_bgr.astype(np.float32) * alpha + bg.astype(np.float32) * (1.0 - alpha))
        return np.clip(blended, 0, 255).astype(np.uint8)


class PhotometricFieldAugmenter:
    """Simulates harsh field lighting, mobile compression, and outdoor noise."""

    @staticmethod
    def apply_color_jitter(pil_img: Image.Image) -> Image.Image:
        """Random brightness, contrast, and color balance jitter."""
        # Brightness (0.75 - 1.30)
        enh = ImageEnhance.Brightness(pil_img)
        pil_img = enh.enhance(random.uniform(0.75, 1.30))

        # Contrast (0.75 - 1.25)
        enh = ImageEnhance.Contrast(pil_img)
        pil_img = enh.enhance(random.uniform(0.75, 1.25))

        # Color Saturation (0.70 - 1.35)
        enh = ImageEnhance.Color(pil_img)
        pil_img = enh.enhance(random.uniform(0.70, 1.35))

        return pil_img

    @staticmethod
    def apply_field_blur(pil_img: Image.Image) -> Image.Image:
        """Random slight Gaussian blur or defocus."""
        if random.random() < 0.35:
            radius = random.uniform(0.5, 1.8)
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius))
        return pil_img

    @staticmethod
    def apply_jpeg_compression(pil_img: Image.Image, quality_range: Tuple[int, int] = (35, 75)) -> Image.Image:
        """Simulate mobile upload / messaging service compression artifacts."""
        quality = random.randint(quality_range[0], quality_range[1])
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    @staticmethod
    def apply_partial_cutout(np_img: np.ndarray, num_patches: int = 1, patch_ratio: float = 0.15) -> np.ndarray:
        """
        Simulate partial occlusion of leaf surface (twigs, soil specks, cast shadows).
        """
        h, w = np_img.shape[:2]
        out = np_img.copy()
        for _ in range(num_patches):
            ph, pw = int(h * patch_ratio), int(w * patch_ratio)
            y = random.randint(0, max(0, h - ph))
            x = random.randint(0, max(0, w - pw))
            # Dark occlusion patch
            out[y:y + ph, x:x + pw] = [random.randint(15, 45)] * 3
        return out

    @staticmethod
    def apply_random_crop_and_rotation(pil_img: Image.Image) -> Image.Image:
        """Random rotation (-30 to +30 deg or 90 deg steps) and slight zoom/crop (0.85 - 1.0)."""
        w, h = pil_img.size
        if random.random() < 0.7:
            angle = random.uniform(-30, 30) if random.random() < 0.7 else float(random.choice([0, 90, 180, 270]))
            if angle != 0:
                pil_img = pil_img.rotate(angle, resample=Image.BILINEAR, expand=False)
        if random.random() < 0.5:
            scale = random.uniform(0.85, 0.98)
            cw, ch = int(w * scale), int(h * scale)
            x1 = random.randint(0, w - cw)
            y1 = random.randint(0, h - ch)
            pil_img = pil_img.crop((x1, y1, x1 + cw, y1 + ch)).resize((w, h), Image.BILINEAR)
        return pil_img

    def augment(
        self,
        image: Union[Image.Image, np.ndarray],
        p_randomize_bg: float = 0.5,
        leaf_mask: Optional[np.ndarray] = None,
        randomizer: Optional[BackgroundRandomizer] = None,
    ) -> Image.Image:
        """
        Execute full field-adaptation pipeline.
        """
        if isinstance(image, Image.Image):
            pil_img = image.convert("RGB")
            bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        else:
            bgr = image
            pil_img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

        # 1. Background Randomization (for lab leaves with masks)
        if leaf_mask is not None and randomizer is not None and random.random() < p_randomize_bg:
            bgr = randomizer.composite(bgr, leaf_mask)
            pil_img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

        # 2. Geometric Flips, Crops & Rotations
        if random.random() < 0.5:
            pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
        if random.random() < 0.2:
            pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
        pil_img = self.apply_random_crop_and_rotation(pil_img)

        # 3. Photometric Jitter
        pil_img = self.apply_color_jitter(pil_img)

        # 4. Blur & Compression
        pil_img = self.apply_field_blur(pil_img)
        if random.random() < 0.50:
            pil_img = self.apply_jpeg_compression(pil_img)

        # 5. Partial Occlusion Cutout
        if random.random() < 0.30:
            arr = np.array(pil_img)
            arr = self.apply_partial_cutout(arr)
            pil_img = Image.fromarray(arr)

        return pil_img
