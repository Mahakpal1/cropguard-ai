# Model card (fill from `metrics.json` after training; do not invent numbers)

| Field | Value |
|---|---|
| Model | EfficientNet-B0 (ImageNet pretrained), fine-tuned, exported to ONNX |
| Source | ☐ trained by us (notebook)  ☐ community pretrained: ______ (licence: ______) |
| Input | 224×224 RGB, ImageNet mean/std |
| Classes | 15 (tomato, potato, pepper), see `contracts/class_names.json` |
| Training data | PlantVillage (+ PlantDoc train for field fine-tuning) |
| Split | by leaf group, seed 42; near-duplicate check: ___ % of test images |
| Lab test | accuracy ___ · macro-F1 ___ · top-3 ___ |
| Field test (PlantDoc test) | accuracy ___ before / ___ after field fine-tuning |
| Calibration | temperature ___ · ECE ___ before → ___ after |
| Confidence threshold | ___ (chosen on field-val; accuracy when answering ___ , coverage ___) |
| Explanations | occlusion sensitivity (app), Grad-CAM (notebook) |
| Known failure cases | ______ (add 3-5 real examples with photos) |
| Intended use | decision support for a farmer, never a replacement for an agricultural officer |
| Not suitable for | other crops, pests (except spider mites), severity as a measurement, legal or insurance decisions |
