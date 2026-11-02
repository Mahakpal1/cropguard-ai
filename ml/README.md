# ml/ : getting a model (owner: Student A)

CropGuard needs one ONNX model in `ml/models/` plus a `model_config.json`. Two ways to get it; **do both** if time allows
(the pretrained model is your safety net, your own trained model is your "genuine ML work").

| Path | Command | Time | What you can claim |
|---|---|---|---|
| **A. Pretrained (community)** | `python ml/download_pretrained.py` (files go to `ml/models/community/`) | 5 min | "We evaluated an existing PlantVillage model on our own split" (cite the author, check the licence) |
| **B. Train it yourself** | open `notebooks/CropGuard_Training.ipynb` in Colab (free T4), run all, then unzip into `ml/models/cropguard/` and run `python ml/make_model_config.py` | about 1 hour | transfer learning, leaf-level split, calibration, lab-vs-field gap, ONNX export |

Then check it before you trust it:

```bash
python ml/evaluate_onnx.py --data /path/to/your/test_images
```

No model present? The app still runs in **simulated mode** and every API response says `model.simulated = true`; the web page shows
"classifier simulated". Never present simulated output as a real prediction.

Other open-source projects worth reading and citing (training code, Grad-CAM, apps):
`tkalaskar/Plant-Disease-Classifier`, `pavanmanjunath18/Plant_Disease_Classifier`, `tamannahazra28406/Plant-Disease-Classifier` (GitHub),
and the `plantdoc-predictor` package (model zoo).

`models/` is git-ignored: share weights through Drive or a GitHub Release, never through git history.


Switch between models any time: `python ml/switch_model.py --list`, then `python ml/switch_model.py community` or `cropguard`, then restart the server.
Full step-by-step instructions (Windows and Mac): `docs/SETUP_AND_TRAINING_GUIDE.md`.

## Tools in this folder
| Script | Use |
|---|---|
| `diagnose.py` | why is this photo rejected or wrong? (top-5 over all outputs, scores, hints) |
| `calibrate_gates.py` | set confidence and energy gates from held-out data |
| `evaluate_onnx.py` | accuracy, macro-F1, ECE, risk-coverage of the active model on an ImageFolder |
| `datasets/prepare_union.py`, `make_class_names.py`, `make_kb_scaffolds.py` | merge datasets, build the class list and advice scaffolds |
| `../notebooks/CropGuard_Train_38class_Colab.ipynb` | train on a 38-class train/valid dataset in Colab (group-aware split, calibration, field test, export) |
| `train_union.py` | train on the merged data (Colab / GPU), leave-one-source-out and unknown-crop tests |
| `export_crop_id.py` | optional crop-identification stage (BioCLIP to ONNX) |
Broad-coverage steps: `docs/ACCURACY_AND_COVERAGE_ROADMAP.md`.
