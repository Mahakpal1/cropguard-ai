# Professor Q&A: short, honest answers

**1. What does the system do?** Takes a leaf photo and returns the disease, a calibrated confidence, a severity estimate, a heatmap of where the model looked, and curated advice (do now / avoid / prevent) in English or Hindi.

**2. Which data?** PlantVillage (15 classes: tomato, potato, pepper; about 20k lab-style images). For field testing we use PlantDoc (real photos) and our own phone photos.

**3. Why transfer learning?** ImageNet features (edges, textures, spots) already transfer well. We train the new head first, then fine-tune everything with a smaller learning rate. Less data, less time, higher accuracy than training from scratch. The notebook proves it by comparing against a simple CNN and ResNet50.

**4. Why EfficientNet-B0?** Good accuracy for only about 5 M parameters, so it exports to a small ONNX file and runs on a CPU.

**5. How did you split the data? Is the test score inflated?** We split by leaf group, not by random image, because PlantVillage has several photos of the same leaf. We also run a near-duplicate check between test and train and print the percentage (`metrics.json: near_duplicate_pct`).

**6. What accuracy do you get?** Quote only numbers from your own `metrics.json` / `model_comparison.csv`. Lab accuracy is high; always show the field number next to it.

**7. Why is field accuracy lower?** Lab photos have plain backgrounds and one leaf. Real photos have soil, shadows, other leaves. We (a) augment with background replacement, (b) measure on PlantDoc, (c) fine-tune on PlantDoc train, and report the before/after gap.

**8. How do you know "94 % confident" means something?** We measure calibration (ECE, reliability diagram) and fix over-confidence with temperature scaling fitted on a validation split. The retake threshold is chosen from a risk-coverage table, not guessed.

**9. What if the photo is bad or the crop is unsupported?** The API returns `low_confidence`, `unsupported_crop` or `no_leaf` and the UI asks for a retake instead of guessing.

**10. How is severity computed? Is it validated?** Lesion pixels ÷ leaf pixels using HSV colour rules. It is an image-based estimate (the dataset has no severity labels), so the UI calls it an estimate. Validation against an expert score is future work.

**11. Why not use an LLM for the advice?** A wrong dosage can damage a crop or a farmer's health. Advice comes from reviewed JSON entries based on extension guidance, contains no dosage numbers, and always defers to the product label and the local agricultural officer. A test enforces the no-dosage rule.

**12. Is the advice correct?** Entries are marked `draft` until a domain expert reviews them and sources are attached. We say so openly; review status is part of each file.

**13. How do you explain the AI's decision?** Occlusion sensitivity in the app (works with any ONNX model) and Grad-CAM in the report notebook. Both show whether the model looks at the lesion or at the background.

**14. Why ONNX Runtime?** One portable model file, small, fast on CPU, no PyTorch needed at deployment.

**15. Why HSV segmentation and not a deep model?** It is simple and explainable and needs no extra labels. Known weaknesses: strong shadows, soil, yellow backgrounds. Future work: GrabCut or a small U-Net.

**16. Did you train the model yourselves or use a pretrained one?** Say exactly which. Path A: community pretrained model, evaluated by us on our split. Path B: our own EfficientNet-B0 fine-tuned in the notebook. Never present someone else's accuracy as yours.

**17. What happens to the farmer's photos?** The server keeps only a 64-px thumbnail and the result in SQLite; the original photo is not stored. History can be deleted with one call.

**18. What about pests?** The dataset is diseases; spider mites are the only pest class. Pest detection is future work.

**19. Hindi and voice?** Advice is stored in English and Hindi (Hindi to be reviewed by a native speaker). Read-aloud uses the browser's speech synthesis; no extra service or cost.

**20. How is it reproducible and maintainable?** Fixed seeds, a one-click Colab notebook, pinned requirements, 49 automated tests (including a contract test that keeps the API and its specification in sync), Docker Compose, CI on every push.

**21. What are the main limitations?** Lab-style data, 15 classes, severity is an estimate, no on-device mode, advice is general guidance. See `docs/ARCHITECTURE.md`.

**22. What would you do next?** More field photos from real farms, a field-trained model, GrabCut/U-Net segmentation, an expert-scored severity set, pest classes, more Indian languages, offline mobile app.

**23. Why does the app sometimes say "not sure" even when a disease is visible?** The model only knows the crops and photo styles it was trained on, and we prefer an honest "not sure, here are the likely candidates" to a confident wrong answer that could lead to the wrong spray. We measure how often unsure answers are avoidable (risk-coverage) and fix the cause: field data, more crops, and a crop-identification stage.

**24. How do you add a new crop?** Add labelled photos to the unified dataset, add the crop to `crops.json`, retrain, then an expert writes and reviews the advice entry. Until reviewed, the app labels the advice as draft or generic.
