# Roadmap: reliable predictions and many more crops

Run every command in the VS Code terminal opened at the project folder with `(.venv)` active (see `SETUP_AND_TRAINING_GUIDE.md`). Windows PowerShell syntax first; on Mac/Linux use `python3` and `export NAME=value` instead of `$env:NAME="value"`.

## What the problem is (short)
* A model trained on lab photos of 3 crops will be unsure or wrong on other crops and on real field photos. "Unsure" is often the **honest** answer. Lowering the threshold only hides it.
* So the fix is: (1) find out which failure you have, (2) make the unsure/unsupported logic smarter, (3) give the model **field data and more crops**, (4) identify the **crop first**, (5) let experts review the advice for each new disease.

## Phase 0: diagnose (30 minutes, no training)
```powershell
python ml/diagnose.py "C:\path\to\the\photo.jpg"       # or a whole folder of photos that failed
```
It prints the top-5 guesses over **all** the model's outputs, how much probability sits on crops you do not support, the uncertainty scores, whether the test-time-augmentation views agree, and a hint:

| What you see | Meaning | Fix |
|---|---|---|
| most probability on "other crops" | the crop is not covered | Phase 2 + 4 (more crops) |
| views disagree | sensitive to framing/scale (close-ups, big lesions) | Phase 3 (scale augmentation, field data) |
| flat probabilities between look-alike diseases | ambiguous or domain shift | Phase 3 (field data), show top-3 candidates |
| confidence gate 0.85-0.9 | gate chosen too strictly or from too little data | Phase 1 (`calibrate_gates.py`) |

Also check which model is active: `python ml/switch_model.py --list`.

## Phase 1: quick wins (already in the project)
Changed in code (nothing to do except restart the server):
* the page sends the **original photo**, and both page and backend **pad to a square** instead of cropping (no lesion is cut off);
* **test-time augmentation**: 3 views (full, centre 80 %, flipped) with averaged logits;
* **energy score** and **margin** are reported (`scores` in the API) and can be used as gates;
* an uncertain result now shows the **top-3 candidates** instead of a dead end;
* classes without a reviewed advice entry get generic advice and an `advice_tier` label.

Set the gates from data (needs a held-out folder of **field** photos, sub-folders named like the classes, and optionally a folder of photos of crops you do **not** support):
```powershell
python ml/calibrate_gates.py --id-dir "D:\field_val" --ood-dir "D:\other_crops" --target-precision 0.9 --write
```
It prints coverage vs precision for each threshold, the energy threshold that keeps 95 % of normal photos, and (with `--ood-dir`) the AUROC for rejecting unknown photos. `--write` stores `confidence_threshold` and `energy_threshold` in the active `model_config.json`. Optional manual keys there: `margin_threshold`, `tta` (true/false).

## Phase 2: build a broad dataset
### 2a. Sources (check every licence before you use or share anything)
| Dataset | What | Get it | Licence / note |
|---|---|---|---|
| PlantVillage | lab photos, 38 classes, 14 crops | Kaggle: `emmarex/plantdisease` (15 classes, what you used) or search Kaggle for "PlantVillage dataset" (38 classes). Avoid "augmented" copies unless you group-split | research use; lab only |
| PlantDoc | 2,598 field photos, 27 classes | `git clone https://github.com/pratikkayal/PlantDoc-Dataset data/raw/plantdoc_repo` | small but real |
| PlantWild | 18,542 field photos, 89 classes (v1); 11,488 photos, 115 diseases (v2) | https://huggingface.co/datasets/uqtwei2/PlantWild (original) or `Voxel51/PlantWild` (FiftyOne format; 673 files look like duplicates) | **CC BY-NC-ND 4.0: non-commercial only.** Paper: https://arxiv.org/abs/2408.03120 , code https://github.com/tqwei05/MVPDR |
| PlantSeg | 11,458 field photos, 115 diseases, with masks | linked from the paper https://arxiv.org/abs/2409.04038 | masks could later improve severity |
| Crop-specific sets | rice, wheat, maize, cassava, apple... | search Kaggle / paper sites, e.g. "Paddy Doctor", "Cassava Leaf Disease Classification", "Plant Pathology FGVC (apple)" | I have not verified size or licence: check each |
| **Your own photos** | the most valuable data | folders named like the classes | label carefully, different leaves for test |

### 2b. Export PlantWild to class folders
```powershell
pip install fiftyone huggingface_hub
python - <<'PY'
import fiftyone as fo
from fiftyone import ViewField as F
from fiftyone.utils.huggingface import load_from_hub
ds = load_from_hub("Voxel51/PlantWild")
v1 = ds.match(F("dataset_version") == "v1")
v1.export(export_dir="data/raw/plantwild", dataset_type=fo.types.ImageClassificationDirectoryTree, label_field="ground_truth")
PY
```
(PowerShell has no here-doc: save the Python lines as `export_plantwild.py` and run `python export_plantwild.py`.)

### 2c. Merge everything under one label list
Arrange each dataset as `data/raw/<name>/<class folder>/<images>`, then:
```powershell
python ml/datasets/prepare_union.py --src plantvillage=data/raw/plantvillage --src plantdoc=data/raw/plantdoc --src plantwild=data/raw/plantwild --out data/union
```
* Folders named like `Tomato___Early_blight` are understood automatically; PlantDoc names are mapped by `ml/datasets/label_map.csv`.
* For any folder it cannot map it writes `ml/datasets/unmapped_<source>.csv`. Fill `crop` and `disease`, append the rows to `label_map.csv`, run again.
* Exact duplicates are removed; the summary shows images per source and crop, and classes with fewer than 30 images (treat those as experimental).

### 2d. Class list and advice entries for the new classes
```powershell
python ml/datasets/make_class_names.py --manifest data/union/manifest.csv --out contracts/class_names.broad.json
python ml/datasets/make_kb_scaffolds.py --classes contracts/class_names.broad.json
```
The scaffolds land in `knowledge_base/drafts/`. Experts fill them, then you move them to `knowledge_base/`. Until then the app says "generic advice" for those diseases.

## Phase 3: train on the broad data (Colab or a local GPU)
Colab cells (after uploading `cropguard.zip` and `union.zip`, or mounting Drive; Runtime = T4 GPU):
```
!unzip -q cropguard.zip && cd cropguard && unzip -q ../union.zip -d data
!pip -q install timm scikit-learn pandas pillow onnx onnxruntime
!cd cropguard && python ml/train_union.py --data data/union --out ml/models/union --backbone efficientnet_b0 --epochs 12 --holdout-source plantdoc --ood-crops Apple,Grape
```
* **Run 1 (honest estimate):** `--holdout-source plantdoc` tests on a dataset the model never trained on; `--ood-crops` keeps whole crops out of training to measure how well unknown crops are rejected. Read `metrics.json`: accuracy by source and crop, ECE, thresholds, `ood_auroc`.
* **Run 2 (production):** repeat without those two flags so the model uses all data.
* Bigger backbones (`--backbone convnext_tiny`, any timm name) help if you have GPU time. Use `--quick --no-pretrained` first to check that everything runs.
* The script saves `ml/models/union/` (ONNX + `model_config.json`). Download that folder into your project's `ml/models/`.

Install it:
```powershell
python ml/switch_model.py union
$env:CLASSES_PATH="contracts/class_names.broad.json"
python -m uvicorn backend.app.main:app --port 8000
python ml/calibrate_gates.py --id-dir "D:\field_val" --ood-dir "D:\other_crops" --write      # final gates with the real pipeline
```
`CLASSES_PATH` makes the backend use the broad class list; classes without a knowledge entry get generic advice.

## Phase 4: identify the crop first (optional, biggest coverage gain per effort)
On Colab or a PC with PyTorch:
```
pip install torch open_clip_torch onnx onnxruntime
python ml/export_crop_id.py --crops ml/datasets/crops.json --out ml/models/crop_id
```
This exports the BioCLIP image encoder to ONNX and pre-computes text embeddings for the 42 crops (+ 3 "other/not a plant" entries) in `ml/datasets/crops.json`. Copy the `ml/models/crop_id/` folder into the project and restart: `/api/v1/health` shows `"crop_id": true`. Effects: crops with no disease classes are reported as "crop not supported yet: <name>", and the disease probabilities are restricted to the detected crop. Tune `threshold` in `ml/models/crop_id/config.json` on real photos. Crop names in `crops.json` must match the crop names in the class list (e.g. `Maize`, `Pepper`).

## Phase 5: expert review loop (what really limits coverage)
1. Every new disease needs an advice entry: symptoms, do now, prevent, sources, English and Hindi.
2. An agriculture expert reviews it; a native speaker checks Hindi. Then set `"review": {"status": "reviewed", "reviewed_by": "...", "date": "..."}`.
3. The app labels advice as reviewed / draft / generic. Only show full advice for classes whose **field** accuracy you have measured and found good (for example precision of 85 % or more on field-test photos); otherwise show the candidates and send the farmer to an officer.
4. With consent, store the photos the app was unsure about, have them labelled, add them to `data/raw/mine`, rebuild the union and retrain. That loop is how coverage grows.

## How to decide whether it worked
Report, per crop and per source: field top-1 accuracy, macro-F1, ECE, accuracy at a fixed coverage (for example "answers 70 % of photos at 90 % precision"), and unknown-crop rejection (`ood_auroc`, share caught). Do not report the lab number alone.

## Status of this code
Tested here with automated tests: diagnose, gate calibration, test-time augmentation, energy and margin gates, crop stage (with a toy encoder), padding, advice tiers, dataset merging and class/knowledge scaffolding, and the web page against the live backend. **Not run here** (needs a GPU, large downloads or sites I cannot reach): `train_union.py` on real data, `export_crop_id.py` with BioCLIP, the PlantWild export, the Kaggle and Hugging Face downloads. Expect to fix small errors on the first real run and read `metrics.json` before trusting any number.
