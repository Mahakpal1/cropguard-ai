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
        if cfg.get("model_folder") and cfg["model_folder"] in MODEL_ORDER:
            return cfg["model_folder"]
        if cfg.get("model_type") == "dinov2_hierarchical" or "dinov2" in cfg.get("name", "").lower():
            return "dinov2_hierarchical"
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
        # Always use just the filename (basename) so we never double-prepend the
        # folder name when _switch_model is called repeatedly or when the config
        # already contains a relative path like "dinov2_hierarchical/heads.pt".
        for key in ("onnx", "checkpoint", "labels_file", "classes_file"):
            if key in cfg and cfg[key]:
                val = Path(cfg[key]).name   # strip any existing folder prefix
                cfg[key] = f"{name}/{val}"
    cfg["model_folder"] = name
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
        md = _models_dir(s)

        models_meta = []
        for m in available:
            m_cfg_path = md / m / "model_config.json"
            display_name = m
            tag = "BASELINE"
            is_mine = False
            if m == "dinov2_hierarchical":
                display_name = "⭐ My Model: DINOv2 ViT-L/14 (Hierarchical 518px)"
                tag = "MY MODEL"
                is_mine = True
            elif m_cfg_path.exists():
                try:
                    c = json.loads(m_cfg_path.read_text(encoding="utf-8"))
                    display_name = c.get("display_name") or c.get("name", m)
                    tag = c.get("tag", "BASELINE")
                    is_mine = bool(c.get("is_user_model", False))
                except Exception:
                    pass
            models_meta.append({
                "id": m,
                "label": display_name,
                "tag": tag,
                "is_mine": is_mine,
            })

        return {
            "available": available,
            "active": active,
            "active_info": pipe.info(),
            "models": models_meta,
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
        if fb.corrected_class_id:
            valid_ids = set(app.state.pipe.by_id.keys())
            # Check labels from model config
            for cfg_path in [
                getattr(app.state.pipe.s, "model_dir", Path("ml/models")) / "model_config.json",
                Path("ml/models/model_config.json"),
            ]:
                if cfg_path.exists():
                    try:
                        cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
                        if "labels" in cfg_data:
                            valid_ids.update(cfg_data["labels"])
                    except Exception:
                        pass
            # Also allow canonical classes from classifier
            if hasattr(app.state.pipe, "clf") and hasattr(app.state.pipe.clf, "classes") and app.state.pipe.clf.classes:
                valid_ids.update(c["id"] if isinstance(c, dict) else str(c) for c in app.state.pipe.clf.classes)
            # Normalize casing and formatting
            corr_norm = fb.corrected_class_id.strip()
            is_valid = corr_norm in valid_ids or any(k.lower() == corr_norm.lower() for k in valid_ids)
            if not is_valid:
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
