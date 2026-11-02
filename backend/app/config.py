import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _b(name, default):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")


@dataclass
class Settings:
    root: Path = ROOT
    model_dir: Path = field(default_factory=lambda: Path(os.environ.get("MODEL_DIR", ROOT / "ml" / "models")))
    kb_dir: Path = field(default_factory=lambda: Path(os.environ.get("KB_DIR", ROOT / "knowledge_base" / "broad")))
    classes_path: Path = field(default_factory=lambda: Path(os.environ.get("CLASSES_PATH", ROOT / "contracts" / "class_names.json")))
    frontend_dir: Path = field(default_factory=lambda: Path(os.environ.get("FRONTEND_DIR", ROOT / "frontend")))
    db_path: Path = field(default_factory=lambda: Path(os.environ.get("DB_PATH", ROOT / "data" / "cropguard.db")))
    max_upload_mb: int = int(os.environ.get("MAX_UPLOAD_MB", 10))
    cors_origins: str = os.environ.get("CORS_ORIGINS", "*")
    occlusion_grid: int = int(os.environ.get("OCCLUSION_GRID", 6))
    explain_default: bool = _b("EXPLAIN_DEFAULT", True)
    min_leaf_fraction: float = float(os.environ.get("MIN_LEAF_FRACTION", 0.08))
    sev_bins: tuple = tuple(float(x) for x in os.environ.get("SEVERITY_BINS", "10,35").split(","))
    default_threshold: float = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.6))
