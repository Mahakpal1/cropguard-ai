# CropGuard Dataset Registry & Provenance

This document catalogues all training, validation, and benchmarking datasets integrated into CropGuard, following strict data provenance, licensing, and lab-vs-field separation principles.

---

## 1. Indian Field & Lab Datasets (data/raw/)

| Source ID | Crop / Category | Classes Included | Image Count | Lab vs Field | License | URL / Origin |
|-----------|-----------------|------------------|-------------|--------------|---------|--------------|
| `rice_dslr` | Rice (*Oryza sativa*) | Bacterial Leaf Blight, Brown Spot, Leaf Blast, Tungro, Healthy | 7,901 | Field (DSLR & field survey) | CC0 / Public Domain | [HuggingFace amdmqd](https://huggingface.co/datasets/amdmqd/rice_leaf_disease_dataset) & AveyBD |
| `mangoleafbd` | Mango (*Mangifera indica*) | Anthracnose, Bacterial Canker, Cutting Weevil, Die Back, Gall Midge, Powdery Mildew, Sooty Mould, Healthy | 4,000 | Lab / On-leaf field | CC BY 4.0 | [MangoLeafBD / pypi-ahmad](https://github.com/pypi-ahmad/Mango-Leaf-Disease-Prediction) |
| `wheat_field` | Wheat (*Triticum aestivum*) | Brown Rust (Leaf Rust), Stem Rust, Healthy | 876 | Field | CC0 / Research | [WheatDiseaseDataset / mubashar1030](https://github.com/mubashar1030/WheatDiseaseDataset) |
| `cotton_field` | Cotton (*Gossypium hirsutum*) | Bacterial Blight, Healthy | 766 | Field | CC BY 4.0 / Open | [CottonDiseasePrediction / Farmaan10](https://github.com/Farmaan10/CottonDiseasePrediction) |
| `sugarcane_field` | Sugarcane (*Saccharum officinarum*) | Bacterial Blight, Red Rot, Healthy | 300 | Field | CC BY 4.0 | [Sugarcane-Disease-Dataset / sabidarrow](https://github.com/sabidarrow/Sugarcane-Disease-Dataset) |
| `generic_negative` | Non-Crop / Not-a-Leaf | Soil & dirt, Weeds & grass, Human hands & tools, Sky & background | 128 | Real Scenes (OOD Negatives) | CC0 / Public Domain | Ultralytics COCO / Field Negatives |

**Total Raw Indian Field Images:** 13,971 images

---

## 2. Benchmark & Complementary Datasets

| Source ID | Crop / Category | Classes Included | Image Count | Lab vs Field | License | Notes |
|-----------|-----------------|------------------|-------------|--------------|---------|-------|
| `plantdoc` | Multi-crop (Tomato, Potato, Corn, Apple, Grape, Pepper, etc.) | 28 classes with field symptoms | ~2,500 | Field (Web harvested, unconstrained) | MIT | Real-world field benchmark; unconstrained lighting & occlusions |
| `plantvillage` | Multi-crop (Tomato, Potato, Pepper, Apple, Grape, Peach, Squash, Strawberry, etc.) | 38 classes (diseased & healthy) | 41,276+ | Lab (Detached leaves, uniform background) | CC BY 4.0 | Capped at 50% ratio (`cap_lab_ratio: 0.50`) to prevent background over-fitting |

---

## 3. Data Integrity & Splitting Rules

1. **Perceptual Hash Deduplication (`pHash`):**
   - 64-bit DCT perceptual hash computed for every single image.
   - Images with Hamming distance $\le 4$ are clustered into `leaf_group_id` via Union-Find.
   - Near-duplicate shots of the same leaf are placed strictly within the same split (never leaked across train/val/test).

2. **Source and Domain-Aware Splits:**
   - Splits preserve domain separation.
   - Held-out validation and test sets prioritize real field-style imagery for honest performance metrics.

3. **Lab Capping Policy:**
   - Lab samples (PlantVillage, MangoLeafBD) are constrained to at most 50% of the training distribution per crop (`cap_lab_ratio=0.50`).
   - Lab samples undergo synthetic background randomization (segmented leaf pasted onto random field/soil textures) and photometric jitter (JPEG compression, color jitter, blur) to break reliance on homogeneous lab backgrounds.

4. **Out-of-Distribution (OOD) Negative Class:**
   - The `__non_crop` class incorporates non-leaf surfaces (soil, grass, hands, tools, sky) to train the crop classifier head to explicitly predict `"unsupported / not a leaf"` rather than forcing an inaccurate crop prediction.
