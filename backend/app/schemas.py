from typing import Literal, Optional

from pydantic import BaseModel


class I18n(BaseModel):
    en: str
    hi: str


class TopItem(BaseModel):
    class_id: str
    display: I18n
    p: float


class Severity(BaseModel):
    level: Literal["Mild", "Moderate", "Severe"]
    affected_pct: float
    leaf_fraction: float
    method: str


class Heatmap(BaseModel):
    method: str
    png_base64: str


class AdviceLang(BaseModel):
    symptoms: list[str]
    do_now: list[str]
    avoid: list[str]
    prevent: list[str]
    disclaimer: str


class Advice(BaseModel):
    en: AdviceLang
    hi: AdviceLang


class ModelInfo(BaseModel):
    name: str
    simulated: bool
    temperature: float
    threshold: float


class Scores(BaseModel):
    max_prob: float
    margin: float
    energy: Optional[float] = None


class LeafAnalytics(BaseModel):
    ndvi: float
    canopy_cover_pct: float
    leaf_moisture_pct: float
    chlorophyll_spad: float
    stress_index_pct: float


class CropGuess(BaseModel):
    name: str
    p: float


class PredictResponse(BaseModel):
    id: Optional[int] = None
    status: Literal["ok", "low_confidence", "unsupported_crop", "no_leaf"]
    class_id: Optional[str] = None
    scientific_name: Optional[str] = None
    crop: Optional[I18n] = None
    disease: Optional[I18n] = None
    display: Optional[I18n] = None
    confidence: float
    top3: list[TopItem]
    severity: Severity
    heatmap: Optional[Heatmap] = None
    advice: Advice
    sources: list[dict]
    model: ModelInfo
    scores: Scores
    crop_id: Optional[CropGuess] = None
    advice_tier: Literal["reviewed", "draft", "none"] = "none"
    hierarchical_meta: Optional[dict] = None
    leaf_analytics: Optional[LeafAnalytics] = None
    # Phase 6: DINOv2 separated confidence + leaf-overlap grounding fields
    crop_confidence: Optional[float] = None
    disease_confidence: Optional[float] = None
    is_reliable: Optional[bool] = True
    leaf_overlap_score: Optional[float] = None
    is_grounded: Optional[bool] = None
    explainability_note: Optional[str] = None
    top2_crop: Optional[str] = None
    top2_disease: Optional[str] = None
    top2_confidence: Optional[float] = None
    timings_ms: dict[str, float]


class FeedbackCreate(BaseModel):
    scan_id: Optional[int] = None
    is_correct: bool
    corrected_class_id: Optional[str] = None
    notes: Optional[str] = None
    expert_verified: bool = False


class FeedbackResponse(BaseModel):
    id: int
    ts: str
    scan_id: Optional[int] = None
    is_correct: bool
    corrected_class_id: Optional[str] = None
    predicted_class_id: Optional[str] = None
    display_en: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    expert_verified: bool


class FeedbackStats(BaseModel):
    total_feedback: int
    confirmed_correct: int
    corrections_reported: int
    accuracy_rate: float

