# Setup and training guide: exactly where to type what

## 0. Words you need
* **Project folder** = the folder named `cropguard` that directly contains `README.md`, `backend`, `frontend`, `ml`. Unzip `cropguard.zip` first and never work from inside the zip.
* **Terminal** = the command window inside VS Code. Open it with `Terminal -> New Terminal` (shortcut Ctrl+`). Every command in this guide that looks like `python ...` or `pip ...` is typed **there**, then Enter.
* **Notebook cells** = code boxes inside `CropGuard_Training.ipynb` (in Colab or VS Code). You press the play button on them; you never type notebook code into the terminal.
* **Browser** = Chrome/Edge, only for opening `http://localhost:8000`.

| You want to... | Where | What |
|---|---|---|
| install packages, run tests, start the app, run `ml/` scripts | VS Code terminal, at the project folder | commands below |
| train a model | Colab (browser) **or** the notebook opened in VS Code | run the notebook cells |
| look at the app | browser | http://localhost:8000 |

`make` (Makefile) does not exist on Windows; ignore it and use the explicit commands below.

## 1. One-time installs
1. **Python 3.10, 3.11 or 3.12** from python.org. On Windows tick **"Add python.exe to PATH"**. Check in a terminal: `python --version` (Mac/Linux: `python3 --version`).
2. **VS Code** (code.visualstudio.com) and its extensions **Python** and **Jupyter** (Extensions icon on the left, search, Install).
3. **Git** (git-scm.com). Needed by the notebook to fetch the PlantDoc field dataset.
4. A free **Kaggle** account (kaggle.com): Settings -> API -> **Create New Token** downloads `kaggle.json`. Keep it.
5. Optional: Docker Desktop (only for `docker compose`).

## 2. Run the app (works with no model, in simulated mode)
In VS Code: `File -> Open Folder...` -> choose the **cropguard** folder. Then `Terminal -> New Terminal` and check you are in it (the prompt ends with `cropguard`; `dir` on Windows / `ls` on Mac shows `backend`, `frontend`...).

| Step | Windows (PowerShell) | Mac / Linux |
|---|---|---|
| create environment | `python -m venv .venv` | `python3 -m venv .venv` |
| activate it | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| install packages | `pip install -r requirements-dev.txt` | same |
| run the tests | `python -m pytest` | same |
| start the app | `python -m uvicorn backend.app.main:app --port 8000` | same |

* If Windows says scripts are disabled: run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.
* After activation the prompt starts with `(.venv)`. VS Code may ask "use this environment?": say Yes (or `Ctrl+Shift+P` -> *Python: Select Interpreter* -> `.venv`).
* Open **http://localhost:8000** in the browser. Header chip "Backend connected · classifier simulated" means everything works but no real model is installed yet.
* The app keeps running in that terminal. Stop it with Ctrl+C. For any other command open a **second terminal** with the `+` icon (check it shows `(.venv)`).

## 3. Install a pretrained model (5 minutes)
Second terminal, project folder, `(.venv)` active:
```
python ml/download_pretrained.py
```
It downloads a community PlantVillage model (EfficientNetV2-S, 38 classes) into `ml/models/community/` and makes it active. If the download fails (blocked site), open https://huggingface.co/BiernyVR/crop-disease-classifier in the browser, download `efficientnet_v2_s_best.onnx`, `efficientnet_v2_s_best.onnx.data` and `classes.json` into `ml/models/community/`, and run the command again.

Then **restart the app** (Ctrl+C in the app terminal, run the uvicorn command again) and refresh the browser. Check:
1. The header chip says **"Live model · efficientnetv2s-plantvillage38 (community)"**.
2. http://localhost:8000/api/v1/health shows `"simulated": false`.
3. Upload a leaf: the Classify and Occlusion-map nodes show LIVE.

Read the model's licence on its page before using it in a report, and **check it yourselves**:
```
python ml/evaluate_onnx.py --data "C:\path\to\folder\with\class\subfolders" --limit 100
```
(The folder must contain one sub-folder per class, e.g. the unzipped PlantVillage dataset.) The community model may have seen those images in its own training, so use your own field photos for an honest number.

## 4. "Make mine better": what that really means
You cannot edit someone's ONNX file. You **train your own model**, which already starts from a pretrained network (EfficientNet-B0 with ImageNet weights, i.e. transfer learning), then teach it with PlantVillage plus real field photos. The community model is your **baseline to compare against** and your **safety net** if training fails. What actually improves a model like this:
1. Fine-tuning on **field photos** (PlantDoc is downloaded automatically; add your own, section 7).
2. **Calibration** and a tuned confidence threshold (the notebook does both).
3. More, varied data: other lighting, backgrounds, phones.

## 5. Train on Colab (free GPU) and bring the model into the project
1. Go to colab.research.google.com -> `File -> Upload notebook` -> choose `ml/notebooks/CropGuard_Training.ipynb`.
2. `Runtime -> Change runtime type -> T4 GPU -> Save`.
3. **First do a test run:** in the config cell change `QUICK = False` to `QUICK = True`, then `Runtime -> Run all`. When asked, upload `kaggle.json`. It finishes in 5-10 minutes; the numbers mean nothing, it only proves everything runs.
4. **Real run:** set `QUICK = False`, `Runtime -> Restart session and run all`. About 45-90 minutes. Keep the tab open (if Colab disconnects, run again).
5. At the end the browser downloads **`cropguard_artifacts.zip`**.
6. **Integrate (on your PC, in VS Code):**
   * unzip it so that this file exists: `ml/models/cropguard/cropguard_effb0.onnx` (plus `class_names.json`, `calibration.json`, `metrics.json` in the same folder);
   * in the terminal run `python ml/make_model_config.py`. It prints "Installed and activated";
   * restart the app and refresh the browser: the chip now says **"Live model · cropguard-efficientnet-b0"**.
7. Switch models any time: `python ml/switch_model.py --list`, then `python ml/switch_model.py community` or `python ml/switch_model.py cropguard`, then restart.

## 6. Train on your own PC in VS Code instead
Only sensible with an **NVIDIA GPU** (check: `nvidia-smi` in the terminal prints a table). No GPU: use Colab.
1. Terminal, `(.venv)` active. Install PyTorch with CUDA: open https://pytorch.org -> *Get Started* -> choose Stable / your OS / Pip / Python / CUDA -> **copy the command it shows** and run it. (Do not guess the version; use the site's command.)
2. `pip install timm onnx grad-cam scikit-learn matplotlib pandas kaggle jupyter ipykernel`
3. Check: `python -c "import torch; print(torch.cuda.is_available())"` must print `True`.
4. Put `kaggle.json` in `C:\Users\<you>\.kaggle\` (Windows; create the folder) or `~/.kaggle/` (Mac/Linux).
5. In VS Code open `ml/notebooks/CropGuard_Training.ipynb`. Top right: **Select Kernel -> Python Environments -> .venv**.
6. Do the `QUICK = True` test run first (`Run All`), then set `False` and run again.
7. The last cells copy the result into `ml/models/cropguard/` and activate it by themselves. Restart the app.

## 7. Add your own field photos (the biggest accuracy gain for a demo)
1. Take 30-50 phone photos per disease you can find, **different leaves**, different light and backgrounds.
2. Folders named exactly like the classes (see `contracts/class_names.json`), e.g. `my_photos/Tomato_Early_blight/IMG_001.jpg`. Put a **separate** set of *other* leaves in `my_test_photos/` with the same folder names: that is your honest test.
3. Place both next to the notebook (`ml/notebooks/`). On Colab: zip them, upload with the folder icon on the left, unzip with a cell containing `!unzip my_photos.zip`.
4. In the config cell set `MY_PHOTOS_DIR = 'my_photos'` and `MY_TEST_DIR = 'my_test_photos'`, run all. The lab-vs-field table now includes your photos.
5. Optional: set `PRETRAINED_DIR = '../ml/models/community'` (local runs) to get a table of **community model vs yours** on the same images (`community_vs_ours.csv`).

## 8. What you get after training (for the report)
In `ml/models/cropguard/`: `metrics.json` (accuracy, macro-F1, top-3, calibration, lab-vs-field, threshold), plus the ONNX model. The notebook shows the confusion matrix, reliability diagram, risk-coverage curve and Grad-CAM grid; screenshot them. Fill `docs/MODEL_CARD.md` from these numbers.

## 9. Common problems
| Message / symptom | Cause and fix |
|---|---|
| `'python' is not recognized` | Python not on PATH: reinstall and tick "Add to PATH", or try `py -m venv .venv` |
| activation blocked ("running scripts is disabled") | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `ModuleNotFoundError: backend` | terminal is not in the project folder: `cd` into `cropguard` |
| `Address already in use` | the app is already running in another terminal; stop it (Ctrl+C) or use `--port 8001` and open that port |
| page says "Demo mode" | you double-clicked `index.html`; open http://localhost:8000 and keep the server running |
| chip says "classifier simulated" | no active model: `python ml/switch_model.py --list`, then install one (sections 3 or 5) |
| `classes_missing_in_model` is not empty | the model lacks some of our 15 classes; those can never be predicted |
| Kaggle 401 / 403 | token missing or wrong place; open the dataset page once while logged in and accept its terms |
| Colab "cannot connect to GPU" | free quota used up; try later, or use VS Code on a GPU PC |
| CUDA out of memory | in the config cell lower `bs=64` to `bs=32` |
| download of the pretrained model fails | download the 3 files by hand into `ml/models/community/` (section 3) |

## 10. Train on your own 38-class dataset (`data\disease_dataset\train` and `valid`)
Notebook: `ml/notebooks/CropGuard_Train_38class_Colab.ipynb` (upload it to Colab like in section 5).

1. **Get the data into Colab.** Easiest: in the config cell keep `DATA_SOURCE = 'kaggle'` and upload `kaggle.json` when asked. Or use your local copy: open a terminal in `E:\MINOR\cropguard\data` and run `tar -a -c -f disease_dataset.zip disease_dataset` (PowerShell's `Compress-Archive` can fail above 2 GB), put the zip in Google Drive at `MyDrive/cropguard/disease_dataset.zip`, and set `DATA_SOURCE = 'drive'`.
2. `Runtime -> Change runtime type -> T4 GPU`. First run with `QUICK = True` (about 10 minutes), then `QUICK = False` and `Runtime -> Run all` (roughly 1 to 1.5 hours, an estimate).
3. The browser downloads `cropguard38_model.zip`. Extract it to `E:\MINOR\cropguard\ml\models\cropguard38\` so that `ml\models\cropguard38\model.onnx` exists.
4. In the VS Code terminal at `E:\MINOR\cropguard` (with `(.venv)` active):
```
python ml/switch_model.py cropguard38
python -m uvicorn backend.app.main:app --port 8000
```
5. Check http://localhost:8000/api/v1/health shows `"simulated": false` and `"classes": 38`. The class list comes with the model (`class_names.json` next to `model.onnx`); you do not need `CLASSES_PATH`.
6. Advice texts exist for 15 of the 38 classes. For the rest the app shows generic advice and says so. Create empty entries for experts: `python ml/datasets/make_kb_scaffolds.py --classes ml/models/cropguard38/class_names.json`.
7. Judge the model by `metrics.json` (held-out test split and PlantDoc field test), not by the training curve.
