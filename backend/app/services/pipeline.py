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

from PIL import Image, ImageOps

from cv import severity as sev_mod

from .advisory import Advisory
from .class_mapping import load_classes
from .classifier import Classifier
from .crop_id import CropID
from .explain import lesion_proxy_png, occlusion_png
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
        cfgp = Path(settings.model_dir) / "model_config.json"
        if cfgp.exists() and not os.environ.get("CLASSES_PATH"):
            f = json.load(open(cfgp, encoding="utf-8")).get("classes_file")
            if f and (Path(settings.model_dir) / f).exists():
                return Path(settings.model_dir) / f
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
                "timings_ms": t}

        if sev["leaf_fraction"] < self.s.min_leaf_fraction * 0.75:   # padding takes up to 25 % of the frame
            base.update(status="no_leaf", advice=self.adv.fallback_advice("no_leaf"))
            return self._finish(base, img)

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
                return self._finish(base, img)

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
            return self._finish(base, img)

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
                base["heatmap"] = occlusion_png(self.clf, x, r["target_index"], self.s.occlusion_grid)
            t["explain"] = (time.perf_counter() - t0) * 1000
        return self._finish(base, img)

    def _finish(self, out, img):
        out["timings_ms"] = {k: round(v, 1) for k, v in out["timings_ms"].items()}
        out["_thumb"] = self._thumb(img)
        return out
