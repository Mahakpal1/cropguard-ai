"""The ONE entry point the API uses: Pipeline.predict(image_bytes) -> dict.

decode + pad to square -> severity (cv) -> leaf found? -> [crop id] -> classify (ONNX, with test-time augmentation)
-> uncertainty gates (energy, calibrated probability, margin) -> explain -> advice.
"""
import base64
import io
import json
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from cv import severity as sev_mod

from .advisory import Advisory
from .class_mapping import load_classes
from .classifier import Classifier
from .crop_id import CropID
from .explain import dinov2_gradcam_png, lesion_proxy_png, occlusion_png
from .hierarchical_router import HierarchicalRouter

PAD = (128, 128, 128)   # neutral grey: low saturation, so segmentation ignores it and the model sees ~mean colour


def pad_square(img, fill=PAD):
    w, h = img.size
    if w == h:
        return img
    s = max(w, h)
    out = Image.new("RGB", (s, s), fill)
    out.paste(img, ((s - w) // 2, (s - h) // 2))
    return out


class Pipeline:
    def __init__(self, settings):
        self.s = settings
        self.classes = load_classes(self._classes_path(settings))
        self.by_id = {c["id"]: c for c in self.classes}
        self.clf = Classifier(settings.model_dir, self.classes, settings.default_threshold)
        self.crop = CropID(settings.model_dir)
        self.adv = Advisory(settings.kb_dir)
        self.router = HierarchicalRouter()
        self.supported_crops = sorted({c["crop"]["en"] for c in self.classes})

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _classes_path(settings):
        """A model folder can ship its own class list (model_config.json: "classes_file"); env CLASSES_PATH overrides it."""
        if os.environ.get("CLASSES_PATH"):
            return Path(os.environ["CLASSES_PATH"])
        md = Path(settings.model_dir)
        cfgp = md / "model_config.json"
        if cfgp.exists():
            try:
                f = json.load(open(cfgp, encoding="utf-8")).get("classes_file")
                if f and (md / f).exists():
                    return md / f
            except Exception:
                pass
        if (md / "class_names.json").exists():
            return md / "class_names.json"
        if settings.classes_path and Path(settings.classes_path).exists():
            return settings.classes_path
        # Standard 38-class definition across all 14 crops
        for parent_cand in [md.parent / "cropguard38_384" / "class_names.json", md.parent / "cropguard38" / "class_names.json"]:
            if parent_cand.exists():
                return parent_cand
        return settings.classes_path

    def _display(self, cid):
        c = self.by_id[cid]
        return {l: f"{c['crop'][l]} · {c['disease'][l]}" for l in ("en", "hi")}

    @staticmethod
    def decode(data):
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        img.thumbnail((1024, 1024))
        return pad_square(img)

    @staticmethod
    def _thumb(img):
        t = img.copy()
        t.thumbnail((64, 64))
        buf = io.BytesIO()
        t.save(buf, "JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    def info(self):
        return {"name": self.clf.name, "simulated": self.clf.simulated, "temperature": self.clf.temperature,
                "threshold": self.clf.threshold}

    def _top3(self, probs):
        order = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
        return [(c, p) for c, p in order]

    # ---- main ----------------------------------------------------------
    def predict(self, image_bytes, explain=None):
        explain = self.s.explain_default if explain is None else explain
        t = {}
        t0 = time.perf_counter()
        img = self.decode(image_bytes)
        t["decode"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sev, leaf, lesion = sev_mod.estimate(img, bins=self.s.sev_bins, return_masks=True)
        t["severity"] = (time.perf_counter() - t0) * 1000
        base = {"id": None, "class_id": None, "scientific_name": None, "crop": None, "disease": None, "display": None,
                "confidence": 0.0, "top3": [], "severity": sev, "heatmap": None, "sources": [], "model": self.info(),
                "scores": {"max_prob": 0.0, "margin": 0.0, "energy": None}, "crop_id": None, "advice_tier": "none",
                # Phase 6: DINOv2 separated confidence + leaf-overlap grounding
                "crop_confidence": None, "disease_confidence": None,
                "leaf_overlap_score": None, "is_grounded": None,
                "explainability_note": None,
                "top2_crop": None, "top2_disease": None, "top2_confidence": None,
                "timings_ms": t}

        if sev["leaf_fraction"] < self.s.min_leaf_fraction * 0.75:   # padding takes up to 25 % of the frame
            base.update(status="no_leaf", advice=self.adv.fallback_advice("no_leaf"))
            return self._finish(base, img, leaf_mask=leaf)

        crop = None
        if self.crop.available:
            t0 = time.perf_counter()
            crop = self.crop.predict(img)
            t["crop_id"] = (time.perf_counter() - t0) * 1000
            base["crop_id"] = {"name": crop["name"], "p": round(crop["p"], 4)}

        t0 = time.perf_counter()
        x, views = self.clf.prepare(img) if not self.clf.simulated else (None, None)
        t["preprocess"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        r = self.clf.predict(x, hint_pct=sev["affected_pct"], views=views)
        t["inference"] = (time.perf_counter() - t0) * 1000
        probs = r["probs"]

        # ---- Stage 1 & Stage 2 Hierarchical Bayesian Evidence Fusion ----
        if crop is not None:
            soft_fb = getattr(self.s, "crop_soft_fallback", False) or getattr(self.clf, "soft_fallback", False)
            fusion_w = getattr(self.clf, "crop_fusion_weight", 0.15)
            route_out = self.router.route(
                disease_probs=probs,
                crop_result=crop,
                by_id=self.by_id,
                supported_crops=self.supported_crops,
                crop_threshold=self.crop.threshold,
                soft_fallback=soft_fb,
                fusion_weight=fusion_w,
            )
            if route_out.get("is_unsupported_crop"):
                base.update(status="unsupported_crop",
                            top3=[{"class_id": c, "display": self._display(c), "p": round(p, 4)} for c, p in self._top3(probs)],
                            advice=self.adv.fallback_advice("unsupported_crop"))
                return self._finish(base, img, leaf_mask=leaf)

            r["class_id"] = route_out["class_id"]
            r["confidence"] = route_out["confidence"]
            r["top3"] = route_out["top3"]
            top = r["top3"]
            r["scores"]["max_prob"] = top[0][1]
            r["scores"]["margin"] = top[0][1] - (top[1][1] if len(top) > 1 else 0.0)
            r["target_index"] = None if self.clf.simulated else self.clf.keep_idx[self.clf.keep_ids.index(top[0][0])]
            base["hierarchical_meta"] = {
                "routing_mode": route_out["routing_mode"],
                "species_agreement": route_out["species_agreement"],
                "information_gain_bits": route_out.get("information_gain_bits", 0.0),
            }

        sc = r["scores"]
        base["scores"] = {k: (None if v is None else round(float(v), 4)) for k, v in sc.items()}
        top3 = [{"class_id": c, "display": self._display(c), "p": round(p, 4)} for c, p in r["top3"]]

        # ---- uncertainty gates ------------------------------------------------------------------
        ood = r["oos_prob"] > 0.5 or (self.clf.energy_threshold is not None and sc["energy"] is not None
                                       and sc["energy"] > self.clf.energy_threshold)
        if ood:
            base.update(status="unsupported_crop", top3=top3, advice=self.adv.fallback_advice("unsupported_crop"))
            return self._finish(base, img, leaf_mask=leaf)

        cid = r["class_id"]
        c = self.by_id[cid]
        unsure = r["confidence"] < self.clf.threshold or (self.clf.margin_threshold is not None and sc["margin"] < self.clf.margin_threshold)
        status = "low_confidence" if unsure else "ok"
        base.update(status=status, class_id=cid, crop=c["crop"], disease=c["disease"], display=self._display(cid),
                    confidence=round(r["confidence"], 4), top3=top3)
        if status == "ok":
            base["advice"] = self.adv.advice(cid)
            base["advice_tier"] = self.adv.tier(cid)
            e = self.adv.entry(cid)
            base["sources"] = e["sources"] if e else []
            base["scientific_name"] = e.get("scientific_name") if e else None
        else:
            base["advice"] = self.adv.fallback_advice("low_confidence")

        if explain:
            t0 = time.perf_counter()
            if self.clf.simulated or x is None or r["target_index"] is None:
                base["heatmap"] = lesion_proxy_png(lesion)
            else:
                # Phase 6: prefer DINOv2 Grad-CAM++ over occlusion sensitivity
                try:
                    gcam_out = dinov2_gradcam_png(img, leaf_mask=leaf,
                                                   target_class_idx=r["target_index"])
                    # Extract grounding metadata from result (if present)
                    base["leaf_overlap_score"] = gcam_out.pop("leaf_overlap_score", None)
                    base["is_grounded"] = gcam_out.pop("is_grounded", None)
                    base["explainability_note"] = gcam_out.pop("explainability_note", None)
                    base["heatmap"] = gcam_out
                except Exception:
                    # Fall back to occlusion sensitivity if Grad-CAM++ fails
                    base["heatmap"] = occlusion_png(self.clf, x, r["target_index"], self.s.occlusion_grid)
            t["explain"] = (time.perf_counter() - t0) * 1000
        return self._finish(base, img, leaf_mask=leaf)

    @staticmethod
    def _leaf_analytics(img, leaf_mask, affected_pct, confidence):
        """Compute NDVI proxy and vitality metrics from the real leaf image pixels.

        All values are derived from the segmented leaf region so they change
        meaningfully with every new photo — no hardcoded or random data.
        """
        arr = np.asarray(img.convert("RGB"), np.float32) / 255.0

        if leaf_mask is not None and leaf_mask.any():
            # Resize mask to match arr if needed (arr may differ from 256-px mask)
            if leaf_mask.shape[:2] != arr.shape[:2]:
                from PIL import Image as _PIL
                msk_img = _PIL.fromarray((leaf_mask * 255).astype(np.uint8))
                msk_img = msk_img.resize((arr.shape[1], arr.shape[0]), _PIL.NEAREST)
                m = np.asarray(msk_img) > 127
            else:
                m = leaf_mask
            r_px = arr[:, :, 0][m]
            g_px = arr[:, :, 1][m]
            b_px = arr[:, :, 2][m]
            canopy = round(float(m.mean()) * 100, 1)
        else:
            r_px = arr[:, :, 0].flatten()
            g_px = arr[:, :, 1].flatten()
            b_px = arr[:, :, 2].flatten()
            canopy = 0.0

        # NDVI proxy: (G - R) / (G + R + ε), mapped from [-1,1] → [0,1]
        ndvi_raw = float(np.mean((g_px - r_px) / (g_px + r_px + 1e-6)))
        ndvi = round(min(1.0, max(0.0, (ndvi_raw + 1.0) / 2.0)), 3)

        # Chlorophyll SPAD proxy: mean green intensity of leaf pixels → 20–80 SPAD
        chl = round(20.0 + float(np.mean(g_px)) * 60.0, 1)

        # Leaf moisture: inversely correlated with affected area and redness excess
        redness = float(np.mean(r_px - b_px))
        moisture = round(max(10.0, min(98.0, 90.0 - affected_pct * 0.55 - redness * 28.0)), 1)

        # Stress index: weighted combination of lesion area and classification uncertainty
        stress = round(min(95.0, affected_pct * 0.75 + (1.0 - confidence) * 18.0), 1)

        return {
            "ndvi": ndvi,
            "canopy_cover_pct": canopy,
            "leaf_moisture_pct": moisture,
            "chlorophyll_spad": chl,
            "stress_index_pct": stress,
        }

    def _finish(self, out, img, leaf_mask=None):
        out["timings_ms"] = {k: round(v, 1) for k, v in out["timings_ms"].items()}
        out["_thumb"] = self._thumb(img)
        # Attach live leaf analytics (always present, even on unsupported/no_leaf)
        affected_pct = out.get("severity", {}).get("affected_pct", 0.0)
        confidence = out.get("confidence", 0.0)
        out["leaf_analytics"] = self._leaf_analytics(img, leaf_mask, affected_pct, confidence)
        return out
