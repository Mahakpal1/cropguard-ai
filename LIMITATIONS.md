# CropGuard: Known Limitations & Field Gap Analysis

CropGuard is engineered with honest evaluation standards. Rather than presenting inflated benchmark numbers on lab data, this document explicitly outlines current coverage limitations, the expected real-world field-to-lab drop, and operational boundaries.

---

## 1. Crop Coverage Gaps

While public datasets provide solid coverage for key Indian staples (Rice, Wheat, Sugarcane, Mango, Cotton, Tomato, Potato), public image coverage remains severely limited or absent for several important Indian agricultural crops:

- **Pulses:** Chickpea (Gram / Chana), Pigeon pea (Arhar / Tur), Moong, Urad. Public high-resolution field pathology datasets for Indian pulse varieties are currently scarce or poorly annotated.
- **Millets:** Bajra (Pearl millet), Jowar (Sorghum), Ragi (Finger millet). Although drought-resilient and national priority crops, few public labeled field datasets exist.
- **Commercial & Plantation:** Jute, Tea, Coffee, Rubber, Turmeric, Ginger, Cardamom.
- **Vegetables:** Onion (Stemphylium blight, purple blotch), Brinjal / Eggplant (phomopsis blight, little leaf).
- **Oilseeds:** Mustard / Rapeseed (Alternaria blight, white rust), Groundnut field sets are currently constrained in public repositories without gated access.

**System Behavior on Missing Crops:**  
When an unsupported crop photo is presented, CropGuard's energy-based OOD detector and `"__non_crop_____not_a_leaf__"` head are calibrated to identify the input as `"unsupported / not a leaf"` or trigger the low-confidence reject threshold rather than hallucinating an inaccurate diagnosis.

---

## 2. Lab-to-Field Performance Gap

- **Lab Accuracy vs. Field Accuracy:**
  - Modern CNNs and Vision Transformers commonly report 98–99% accuracy on lab datasets like PlantVillage because models memorize uniform neutral backgrounds (light grey, white plastic sheets).
  - In real farming conditions (direct sunlight glare, shadow occlusion, wet leaves, complex soil/weed backgrounds, multiple diseased leaves in frame), baseline models drop to 50–65%.
- **Expected Field Performance:**
  - With frozen DINOv2 ViT features, leaf localization, and background randomization, CropGuard targets an empirical field joint accuracy between **75% and 85%**, which aligns with state-of-the-art agricultural vision literature.
- **Symptom Confusion:**
  - Early-stage bacterial leaf blight and early-stage brown spot in rice can appear nearly identical at low phone resolutions.
  - Nutritional deficiencies (nitrogen/potassium chlorosis) can mimic fungal viral scorch patterns.

---

## 3. Operational & Hardware Limitations

1. **Leaf Localization Fallback:**
   - In photos where leaves are severely wilted, tangled with dense weeds, or taken from a distance (> 1 meter), the localizer may fail to isolate an individual leaf. CropGuard falls back to the full image while automatically discounting the final confidence score.
2. **Inference Latency on Low-end CPU:**
   - DINOv2 ViT-B/14 feature extraction takes ~30–50ms on NVIDIA RTX 4050 Laptop GPU, but requires 350–700ms on a 4-core laptop CPU.
3. **Lighting & Occlusion:**
   - Extreme over-exposure (specular flash on wet leaves) or severe motion blur degrades ViT token representations.

---

## 4. Path to Improvement

To expand coverage for future iterations:
1. Integrate ICAR (Indian Council of Agricultural Research) and state agricultural university field repositories.
2. Incorporate farmer-submitted crowd-validated feedback loops via CropGuard's API.
3. Add multi-spectral or time-series tracking for complex viral symptom progression.
