# Team workflow (so independent work still integrates)

1. **Contracts first.** `contracts/` is the agreement: API shape, class list, knowledge schema. Changing it needs a PR approved by all four owners (see `.github/CODEOWNERS`). `tests/test_contract.py` fails if code and contract drift.
2. **Everyone can run everything from day one.** With no model installed the backend runs in *simulated mode*, so frontend work never waits for ML, and ML work never waits for the UI.
3. **One owner per folder** (README table). Touch another folder only via a PR the owner reviews.
4. **Git rules.** Branch `feature/<name>-<thing>`; PR into `main`; no direct pushes; CI (`python -m pytest`) must pass. Never commit data or weights: share them via Drive or a GitHub Release link.
5. **Integration points are tiny.** ML to backend: `ml/models/model_config.json` + one `.onnx` file. CV to backend: `cv.severity.estimate(image)`. Backend to frontend: `POST /api/v1/predict`.
6. **Definition of done** for any change: tests pass, docs updated if behaviour changed, screenshot or short note in the PR.

## Who does what when
| Week | A (ML) | B (CV) | C (Backend) | D (Frontend + content) |
|---|---|---|---|---|
| 1 | explore data, run notebook with `QUICK=True` | tune HSV thresholds on real photos | API + tests (done) | review/translate knowledge entries |
| 2 | train EfficientNet-B0, baselines | severity sanity checks vs hand estimates | Docker, deploy to a free host | polish UI, test on phones |
| 3 | field test + calibration, export ONNX | try GrabCut as an upgrade | connect real model, check timings | usability test with 3-5 people |
| 4 | fill `docs/MODEL_CARD.md` | edge cases list | final regression run | record backup demo video |
