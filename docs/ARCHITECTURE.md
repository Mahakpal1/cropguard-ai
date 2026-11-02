# Architecture (one page)

```
 Browser (frontend/)                         FastAPI (backend/app)                         cv/ + knowledge_base/
 ┌───────────────────────┐   POST /predict   ┌──────────────────────────────┐
 │ upload / camera       │ ───────────────▶ │ 1 decode image               │
 │ animated pipeline view│                   │ 2 severity  ───────────────▶ │ cv.severity (HSV leaf + lesion)
 │ diagnosis + advice    │ ◀─────────────── │ 3 classify (ONNX Runtime)    │ ml/models/*.onnx
 │ English / Hindi, voice│   JSON            │ 4 confidence gate            │
 └───────────────────────┘                   │ 5 explain (occlusion map)    │
                                             │ 6 advice lookup  ──────────▶ │ knowledge_base/*.json (reviewed)
                                             │ 7 save thumbnail (SQLite)    │
                                             └──────────────────────────────┘
```

## The seven steps, in plain words

1. **Decode**: open the photo, fix rotation, shrink to at most 1024 px.
2. **Severity** (`cv/`): colour rules in HSV find the leaf (coloured, not dark) and the lesions (leaf pixels that are not healthy green). Severity = lesion pixels ÷ leaf pixels; bins Mild < 10 %, Moderate 10-35 %, Severe > 35 %. If almost no leaf is found, we stop and ask for a new photo (`no_leaf`).
3. **Classify**: resize to the model's input size, normalise like in training, run the ONNX model. A 38-class model is mapped down to our 15 classes; probability on other crops means `unsupported_crop`.
4. **Confidence gate**: probabilities are *calibrated* (temperature scaling fitted in the notebook). Below the threshold the app says "unsure, retake" rather than guessing (`low_confidence`).
5. **Explain**: occlusion sensitivity. Hide one square at a time; the squares that make the prediction drop are the ones the model relied on. Works with any ONNX model and needs no PyTorch. (Grad-CAM figures for the report come from the notebook.)
6. **Advice**: the class id selects a hand-reviewed JSON entry (symptoms, do now, avoid, prevent; English and Hindi). Nothing is generated at run time.
7. **Store**: a 64-px thumbnail and the result go to SQLite for the history page. The original photo is not kept.

## Why this design

| Choice | Reason |
|---|---|
| ONNX Runtime | small, fast, no PyTorch at deploy time, same model file for every team member |
| Curated knowledge base, no LLM advice | a wrong dose can harm a crop; entries are reviewable, citable and testable (a test fails if a dosage number appears) |
| Calibration + status codes | an AI that says "I am not sure" is safer than one that is always confident |
| HSV segmentation | simple, explainable, no extra training data; known limits: shadows, soil, yellow backgrounds |
| Simulated mode | the team can build UI, API and docs in parallel before the model is ready, and the demo can never fail for lack of a model |
| Contracts folder + contract test | frontend, backend and ML can work independently; `tests/test_contract.py` fails if the code and `api.openapi.yaml` drift apart |

## Failure modes and what the user sees

| Situation | `status` | UI |
|---|---|---|
| clear leaf, confident | `ok` | diagnosis, severity, heatmap, advice |
| blurry or odd photo | `low_confidence` | "unsure, please retake" + photo tips |
| apple/corn/other crop (38-class model) | `unsupported_crop` | "this demo covers tomato, potato, pepper" |
| no leaf found | `no_leaf` | retake tips |
| not an image / too large | HTTP 415 / 400 / 413 | friendly error, page falls back to demo mode |
| backend down | n/a | page works in demo mode and says so |

## Limits (state them yourselves before the examiner does)

Lab-style training data; only 15 classes; spider mites are the only pest; severity is an estimate; occlusion maps are coarse (6×6 by default); advice is general extension guidance, not a prescription.
