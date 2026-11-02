"""Stage 1 (optional): which CROP is in the photo? Image embedding model (e.g. BioCLIP exported to ONNX) + text embeddings.

Folder ml/models/crop_id/ with: config.json, <onnx>, <embeddings .npy>. Made by ml/export_crop_id.py.
The result (a) lets us reject crops we have no disease model for and (b) restricts the disease probabilities to that crop.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .classifier import softmax


class CropID:
    def __init__(self, model_dir):
        d = Path(model_dir) / "crop_id"
        self.sess = None
        if not (d / "config.json").exists():
            return
        try:
            cfg = json.load(open(d / "config.json", encoding="utf-8"))
            onnx_path = d / cfg.get("onnx", "crop_encoder.onnx")
            if not onnx_path.exists():
                return
            emb_path = d / cfg.get("embeddings", "crop_embeddings.npy")
            if not emb_path.exists():
                return
            import onnxruntime as ort
            self.sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
            self.inp, self.out = self.sess.get_inputs()[0].name, self.sess.get_outputs()[0].name
            self.crops = cfg["crops"]
            self.emb = np.load(emb_path).astype(np.float32)
            self.emb /= np.linalg.norm(self.emb, axis=1, keepdims=True)
            self.size = int(cfg.get("size", 224))
            self.mean = np.array(cfg.get("mean", [0.4815, 0.4578, 0.4082]), np.float32)
            self.std = np.array(cfg.get("std", [0.2686, 0.2613, 0.2758]), np.float32)
            self.scale = float(cfg.get("logit_scale", 100.0))
            self.threshold = float(cfg.get("threshold", 0.5))
        except Exception:
            self.sess = None

    @property
    def available(self):
        return self.sess is not None

    def predict(self, img):
        im = img.convert("RGB").resize((self.size, self.size), Image.BICUBIC)
        x = ((np.asarray(im, np.float32) / 255.0 - self.mean) / self.std).transpose(2, 0, 1)[None].astype(np.float32)
        e = self.sess.run([self.out], {self.inp: x})[0][0].astype(np.float32)
        e /= np.linalg.norm(e) + 1e-9
        p = softmax(self.scale * (self.emb @ e))
        i = int(p.argmax())
        return {"name": self.crops[i], "p": float(p[i]), "probs": {c: float(v) for c, v in zip(self.crops, p)}}
