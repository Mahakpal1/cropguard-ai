"""ONNX Runtime classifier with two modes:

* real model: loaded from ml/models/model_config.json (our 15-class model, or any 38-class PlantVillage ONNX model).
  A 38-class model is mapped down to our 15 classes; probability mass on other crops is reported as `oos_prob`.
* simulated demo mode (no model present): a deterministic stand-in so the whole app runs end to end.
  Every API response says `model.simulated = true` in this mode.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .class_mapping import build_lookup, map_label


def softmax(z):
    z = z - z.max(-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(-1, keepdims=True)


class Classifier:
    def __init__(self, model_dir, classes, default_threshold=0.6):
        self.classes = classes
        self.ids = [c["id"] for c in classes]
        self.lookup = build_lookup(classes)
        self.sess = None
        self.name = "simulated-demo"
        self.temperature = 1.0
        self.threshold = default_threshold
        self.size, self.mean, self.std = 224, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
        self.tta, self.energy_threshold, self.margin_threshold = True, None, None
        self.missing = []
        self.dinov2_engine = None
        self._load(Path(model_dir))

    @property
    def simulated(self):
        return self.sess is None and getattr(self, "dinov2_engine", None) is None

    def _load(self, d):
        cfgp = d / "model_config.json"
        if not cfgp.exists():
            return
        import onnxruntime as ort
        cfg = json.load(open(cfgp, encoding="utf-8"))

        labels = cfg.get("labels")
        if labels is None and "labels_file" in cfg:
            lp = d / cfg["labels_file"]
            if lp.exists():
                labels = json.load(open(lp, encoding="utf-8"))
        if labels is None and "classes_file" in cfg:
            cp = d / cfg["classes_file"]
            if cp.exists():
                cdata = json.load(open(cp, encoding="utf-8"))
                labels = [c["id"] for c in cdata] if isinstance(cdata, list) else cdata
        if isinstance(labels, dict):
            labels = labels.get("classes") or labels.get("labels")

        # Check for DINOv2 Hierarchical PyTorch checkpoint first
        self.dinov2_engine = None
        ckpt_pt = d / "hierarchical_heads.pt"
        if not ckpt_pt.exists() and "checkpoint" in cfg:
            ckpt_pt = d / cfg["checkpoint"]
        if (ckpt_pt.exists() or cfg.get("model_type") == "dinov2_hierarchical") and ckpt_pt.exists():
            try:
                from src.infer import CropGuardInferenceEngine
                self.dinov2_engine = CropGuardInferenceEngine.from_checkpoint(
                    ckpt_pt,
                    model_name=cfg.get("backbone", "dinov2_vits14"),
                )
                self.name = cfg.get("name", "cropguard-dinov2-hierarchical")
                if "energy_threshold" in cfg:
                    self.energy_threshold = cfg["energy_threshold"]
            except Exception:
                pass

        onnx_rel = cfg.get("onnx", "model.onnx")
        primary_onnx = d / onnx_rel
        candidates = [primary_onnx]
        if self.dinov2_engine is None and d.parent.exists():
            candidates.append(d.parent / "community" / "efficientnet_v2_s_best.onnx")
            for sub in d.parent.iterdir():
                if sub.is_dir() and sub != d:
                    for f in sub.glob("*.onnx"):
                        candidates.append(f)

        sess = None
        for cand in candidates:
            if cand.exists() and cand.stat().st_size > 0:
                try:
                    sess = ort.InferenceSession(str(cand), providers=["CPUExecutionProvider"])
                    break
                except Exception:
                    continue

        if sess is not None:
            shape = sess.get_inputs()[0].shape
            self.size = int(shape[2]) if isinstance(shape[2], int) else int(cfg.get("input_size", 224))
            self.inp, self.out = sess.get_inputs()[0].name, sess.get_outputs()[0].name
        else:
            self.size = int(cfg.get("input_size", 224))
            self.inp, self.out = "input", "output"

        self.mean = cfg.get("mean", self.mean)
        self.std = cfg.get("std", self.std)
        self.temperature = float(cfg.get("temperature", 1.0))
        self.threshold = float(cfg.get("confidence_threshold", self.threshold))
        self.tta = bool(cfg.get("tta", True))
        self.soft_fallback = bool(cfg.get("soft_fallback", False) or cfg.get("fallback_on_crop_rejection", False))
        self.crop_fusion_weight = float(cfg.get("crop_fusion_weight", 0.15))
        self.energy_threshold = cfg.get("energy_threshold")      # None until ml/calibrate_gates.py has run
        self.margin_threshold = cfg.get("margin_threshold")

        if labels:
            mapped = [(i, map_label(lb, self.lookup)) for i, lb in enumerate(labels)]
            self.raw_labels, self.n_out = list(labels), len(labels)
            self.keep_idx = [i for i, c in mapped if c]
            self.keep_ids = [c for i, c in mapped if c]
            if not self.keep_ids:
                self.keep_idx = list(range(len(self.ids)))
                self.keep_ids = list(self.ids)
            self.missing = sorted(set(self.ids) - set(self.keep_ids))
        else:
            self.raw_labels, self.n_out = list(self.ids), len(self.ids)
            self.keep_idx = list(range(len(self.ids)))
            self.keep_ids = list(self.ids)
            self.missing = []

        self.sess, self.name = sess, cfg.get("name", Path(cfg.get("onnx", "model")).stem)
        if self.dinov2_engine is not None:
            self.name = cfg.get("name", "cropguard-dinov2-hierarchical")

    def preprocess(self, img):
        im = img.convert("RGB").resize((self.size, self.size), Image.BILINEAR)
        a = (np.asarray(im, np.float32) / 255.0 - np.array(self.mean, np.float32)) / np.array(self.std, np.float32)
        return a.transpose(2, 0, 1)[None].astype(np.float32)

    def prepare(self, img):
        """Return (x, views): x is the main 1xCxHxW input; views = x plus test-time-augmentation variants."""
        x = self.preprocess(img)
        if not self.tta or self.simulated:
            return x, x
        w, h = img.size
        c = img.crop((int(w * .1), int(h * .1), int(w * .9), int(h * .9)))          # centre 80 %
        views = [x, self.preprocess(c), x[:, :, :, ::-1].copy()]                    # + horizontal flip
        return x, np.concatenate(views, 0)

    def infer(self, x):
        return self.sess.run([self.out], {self.inp: x})[0]

    def probs_all(self, x):
        return softmax(self.infer(x) / self.temperature)

    def predict(self, x=None, hint_pct=0.0, views=None, pil_img=None):
        if self.dinov2_engine is not None and self.sess is None:
            # DINOv2 Hierarchical PyTorch path
            img = pil_img
            if img is None:
                if isinstance(views, Image.Image):
                    img = views
                elif isinstance(x, Image.Image):
                    img = x
                elif x is not None and isinstance(x, np.ndarray):
                    try:
                        arr = ((x[0].transpose(1, 2, 0) * np.array(self.std) + np.array(self.mean)) * 255.0).clip(0, 255).astype(np.uint8)
                        img = Image.fromarray(arr)
                    except Exception:
                        pass

            if img is not None:
                feat = self.dinov2_engine.extractor.extract_image(img)
                if self.energy_threshold is not None:
                    self.dinov2_engine.classifier.energy_threshold = self.energy_threshold
                hp = self.dinov2_engine.classifier.predict(feat)
                canonical = hp.canonical_key
                matched_id = map_label(canonical, self.lookup) or canonical
                top3 = [(matched_id, hp.confidence)]
                if hp.top2_crop and hp.top2_disease:
                    top2_key = f"{hp.top2_crop}___{hp.top2_disease}"
                    top3.append((map_label(top2_key, self.lookup) or top2_key, hp.top2_confidence or 0.0))
                return {
                    "class_id": matched_id,
                    "confidence": hp.confidence,
                    "top3": top3,
                    "oos_prob": 0.0 if hp.is_supported else 1.0,
                    "target_index": 0,
                    "probs": {matched_id: hp.confidence},
                    "scores": {
                        "max_prob": hp.confidence,
                        "margin": hp.confidence - (hp.top2_confidence or 0.0),
                        "energy": hp.energy_score,
                    },
                    "crop_confidence": hp.crop_confidence,
                    "disease_confidence": hp.disease_confidence,
                    "top2_crop": hp.top2_crop,
                    "top2_disease": hp.top2_disease,
                    "top2_confidence": hp.top2_confidence,
                }

        if self.simulated:
            return self._mock(hint_pct)
        logits = self.infer(views if views is not None else x).mean(0)       # average the logits of all views
        p_all = softmax(logits / self.temperature)
        kp = p_all[self.keep_idx]
        oos = float(max(0.0, 1.0 - kp.sum()))
        p = kp / max(kp.sum(), 1e-9)
        order = np.argsort(-p)
        top = [(self.keep_ids[i], float(p[i])) for i in order[:3]]
        energy = float(-(np.log(np.exp(logits - logits.max()).sum()) + logits.max()))   # energy over ALL outputs (T=1)
        return {"class_id": top[0][0], "confidence": top[0][1], "top3": top, "oos_prob": oos,
                "target_index": self.keep_idx[int(order[0])], "probs": {self.keep_ids[i]: float(p[i]) for i in range(len(p))},
                "scores": {"max_prob": top[0][1], "margin": top[0][1] - (top[1][1] if len(top) > 1 else 0.0), "energy": energy}}

    def _mock(self, pct):
        healthy, sick, other = "Tomato_healthy", "Tomato_Early_blight", "Tomato_Late_blight"
        if pct < 4:
            top = [(healthy, 0.97), (sick, 0.02), (other, 0.01)]
        else:
            top = [(sick, 0.94), (other, 0.04), (healthy, 0.02)]
        return {"class_id": top[0][0], "confidence": top[0][1], "top3": top, "oos_prob": 0.0, "target_index": None,
                "probs": dict(top), "scores": {"max_prob": top[0][1], "margin": top[0][1] - top[1][1], "energy": None}}
