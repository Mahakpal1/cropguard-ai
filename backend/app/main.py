"""FastAPI app: /api/v1/* plus the static frontend at /."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .config import Settings
from .db import History
from .schemas import FeedbackCreate, FeedbackResponse, FeedbackStats, PredictResponse
from .services.pipeline import Pipeline

# --- model-switching helpers (same logic as ml/switch_model.py) ---------------------
import json

MODEL_ORDER = [
    "dinov2_hierarchical",
    "cropguard38_384",
    "cropguard38_combined",
    "cropguard38_vit",
    "cropguard38",
    "cropguard38_recovered",
    "community",
]


def _models_dir(s: Settings) -> Path:
    return Path(s.model_dir)


def _list_models(s: Settings):
    md = _models_dir(s)
    found = set()
    if md.exists():
        found = {p.name for p in md.iterdir() if (p / "model_config.json").exists() and p.is_dir()}
    # Keep standard models available so users can select any architecture
    all_models = [m for m in MODEL_ORDER if m in found]
    for m in MODEL_ORDER:
        if m not in all_models:
            all_models.append(m)
    for name in sorted(found):
        if name not in all_models:
            all_models.append(name)
    return all_models


def _active_model(s: Settings) -> str | None:
    top = _models_dir(s) / "model_config.json"
    if not top.exists():
        return "cropguard38_384"
    try:
        cfg = json.loads(top.read_text(encoding="utf-8"))
        onnx = cfg.get("onnx", "")
        parts = onnx.split("/")
        if len(parts) > 1 and parts[0] in MODEL_ORDER:
            return parts[0]
        cfg_name = cfg.get("name", "")
        for m in MODEL_ORDER:
            if m in onnx or m in cfg_name:
                return m
        return parts[0] if len(parts) > 1 else "cropguard38_384"
    except Exception:
        return "cropguard38_384"


def _switch_model(s: Settings, name: str) -> dict:
    md = _models_dir(s)
    src_cfg_path = md / name / "model_config.json"
    if not src_cfg_path.exists():
        cfg = {
            "name": f"cropguard-{name}",
            "onnx": f"{name}/model.onnx",
            "classes_file": f"{name}/class_names.json",
            "input_size": 384 if "384" in name else 224,
            "mean": [0.5, 0.5, 0.5] if ("vit" in name or "384" in name) else [0.485, 0.456, 0.406],
            "std": [0.5, 0.5, 0.5] if ("vit" in name or "384" in name) else [0.229, 0.224, 0.225],
            "temperature": 1.0,
            "confidence_threshold": 0.4 if "384" in name else 0.6,
            "tta": True,
            "soft_fallback": True,
            "crop_fusion_weight": 0.15,
        }
    else:
        cfg = json.loads(src_cfg_path.read_text(encoding="utf-8"))
        if "onnx" in cfg:
            cfg["onnx"] = f"{name}/{cfg['onnx']}"
        if "checkpoint" in cfg:
            cfg["checkpoint"] = f"{name}/{cfg['checkpoint']}"
        for key in ("labels_file", "classes_file"):
            if key in cfg:
                cfg[key] = f"{name}/{cfg[key]}"
    md.mkdir(parents=True, exist_ok=True)
    (md / "model_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg

VERSION = "0.1.0"


def create_app(settings=None):
    s = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.pipe = Pipeline(s)
        app.state.history = History(s.db_path)
        yield

    app = FastAPI(title="CropGuard API", version=VERSION, lifespan=lifespan,
                  description="Crop disease detection, severity estimate and curated advice.")
    app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in s.cors_origins.split(",")],
                       allow_methods=["*"], allow_headers=["*"])

    # ---- Model catalogue & live-switching endpoints --------------------------------
    @app.get("/api/v1/models", tags=["system"])
    def list_models():
        """Return available models and the currently active one (no restart needed)."""
        available = _list_models(s)
        active = _active_model(s)
        pipe = app.state.pipe
        return {
            "available": available,
            "active": active,
            "active_info": pipe.info(),
        }

    @app.post("/api/v1/models/switch", tags=["system"])
    async def switch_model(model_name: str = Query(..., description="Model folder name, e.g. cropguard38_384")):
        """Hot-swap the active model. Writes ml/models/model_config.json and reloads the pipeline in-process."""
        available = _list_models(s)
        if model_name not in available:
            raise HTTPException(400, f"Model '{model_name}' not found. Available: {available}")
        try:
            _switch_model(s, model_name)
        except Exception as exc:
            raise HTTPException(500, str(exc)) from exc
        # Reload pipeline in a thread so we don't block the event loop
        def _reload():
            app.state.pipe = Pipeline(s)
        await run_in_threadpool(_reload)
        return {"switched_to": model_name, "active_info": app.state.pipe.info()}

    @app.get("/api/v1/health", tags=["system"])
    def health():
        p = app.state.pipe
        return {"status": "ok", "version": VERSION, "model": p.info(), "classes": len(p.classes),
                "knowledge_entries": len(p.adv.entries), "classes_missing_in_model": p.clf.missing,
                "crop_id": p.crop.available, "tta": p.clf.tta, "energy_gate": p.clf.energy_threshold is not None}

    @app.get("/api/v1/classes", tags=["knowledge"])
    def classes():
        return {"classes": app.state.pipe.classes}

    @app.get("/api/v1/knowledge/{class_id}", tags=["knowledge"])
    def knowledge(class_id: str):
        e = app.state.pipe.adv.entry(class_id)
        if e is None:
            raise HTTPException(404, "Unknown class id")
        return e

    @app.post("/api/v1/predict", response_model=PredictResponse, tags=["inference"])
    async def predict(file: UploadFile = File(...), explain: bool = Query(True)):
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(415, "Please upload an image file (JPG or PNG)")
        data = await file.read()
        if len(data) > s.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"Image is larger than {s.max_upload_mb} MB")
        try:
            out = await run_in_threadpool(app.state.pipe.predict, data, explain)
        except Exception as e:  # unreadable / corrupt image
            if e.__class__.__name__ in ("UnidentifiedImageError", "OSError"):
                raise HTTPException(400, "The file could not be read as an image")
            raise
        thumb = out.pop("_thumb")
        out["id"] = app.state.history.add({
            "class_id": out["class_id"], "display_en": (out["display"] or {}).get("en"), "confidence": out["confidence"],
            "status": out["status"], "severity_level": out["severity"]["level"],
            "affected_pct": out["severity"]["affected_pct"], "thumb": thumb})
        return out

    @app.get("/api/v1/history", tags=["history"])
    def history(limit: int = Query(20, ge=1, le=200)):
        return {"items": app.state.history.list(limit)}

    @app.delete("/api/v1/history", tags=["history"])
    def clear_history():
        app.state.history.clear()
        return {"deleted": True}

    @app.post("/api/v1/feedback", response_model=FeedbackResponse, tags=["active_learning"])
    def submit_feedback(fb: FeedbackCreate):
        if fb.corrected_class_id and fb.corrected_class_id not in app.state.pipe.by_id:
            raise HTTPException(400, f"Unknown corrected_class_id '{fb.corrected_class_id}'")
        fid = app.state.history.add_feedback(fb.model_dump())
        items = app.state.history.list_feedback(limit=1)
        if not items:
            raise HTTPException(500, "Failed to persist feedback")
        return items[0]

    @app.get("/api/v1/feedback", tags=["active_learning"])
    def get_feedback(limit: int = Query(50, ge=1, le=500)):
        return {"items": app.state.history.list_feedback(limit=limit)}

    @app.get("/api/v1/feedback/stats", response_model=FeedbackStats, tags=["active_learning"])
    def get_feedback_stats():
        return app.state.history.get_feedback_stats()

    if s.frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(s.frontend_dir), html=True), name="frontend")
    return app


app = create_app()
