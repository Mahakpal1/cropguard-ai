"""Optional stage 1: export a BioCLIP image encoder to ONNX and pre-compute text embeddings for your crop list.
Needs PyTorch and open_clip (run on Colab or a PC, not in the backend container):

    pip install torch open_clip_torch onnx onnxruntime
    python ml/export_crop_id.py --crops ml/datasets/crops.json --out ml/models/crop_id

The backend then loads ml/models/crop_id/ automatically (services/crop_id.py). Add a crop by adding a line to crops.json and re-running.
BioCLIP (imageomics/bioclip) is a ViT-B/16 trained on the Tree of Life; check the licence of whichever BioCLIP version you use.
The `threshold` in config.json is a starting point: test it on real photos of supported and unsupported crops.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import open_clip
import torch
import torch.nn.functional as F

TEMPLATES = ["a photo of {latin}.", "a photo of {name}, a plant.", "a close-up photo of a {name} leaf.", "a photo of a diseased {name} leaf."]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", default="ml/datasets/crops.json"); ap.add_argument("--out", default="ml/models/crop_id")
    ap.add_argument("--model", default="hf-hub:imageomics/bioclip"); ap.add_argument("--threshold", type=float, default=0.5)
    a = ap.parse_args()
    crops = json.load(open(a.crops, encoding="utf-8"))
    model, _, _ = open_clip.create_model_and_transforms(a.model)
    tok = open_clip.get_tokenizer(a.model)
    model.eval()
    model.requires_grad_(False)
    with torch.no_grad():
        embs = []
        for c in crops:
            t = model.encode_text(tok([s.format(name=c["name"].lower(), latin=c["latin"]) for s in TEMPLATES]))
            t = F.normalize(t, dim=-1).mean(0)
            embs.append(F.normalize(t, dim=-1).numpy())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    np.save(out / "crop_embeddings.npy", np.stack(embs).astype(np.float32))

    class Enc(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.visual = m.visual
        def forward(self, x):
            return F.normalize(self.visual(x), dim=-1)

    enc = Enc(model)
    dummy = torch.randn(1, 3, 224, 224)
    exported = False

    # Try dynamo exporter with utf-8 encoding safe output (PyTorch >= 2.5 preferred path for ViT)
    try:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        torch.onnx.export(enc, dummy, str(out / "crop_encoder.onnx"), dynamo=True)
        exported = True
        print("Exported via dynamo exporter")
    except Exception as e1:
        print(f"Dynamo exporter failed ({e1}), trying TorchScript exporter...")

    if not exported:
        kw = dict(input_names=["input"], output_names=["emb"], dynamic_axes={"input": {0: "batch"}, "emb": {0: "batch"}}, opset_version=17)
        try:
            torch.onnx.export(enc, dummy, str(out / "crop_encoder.onnx"), dynamo=False, **kw)
            exported = True
        except Exception as e2:
            print(f"TorchScript exporter also failed ({e2})")
            raise RuntimeError("Could not export BioCLIP encoder to ONNX.") from e2
    sess = ort.InferenceSession(str(out / "crop_encoder.onnx"), providers=["CPUExecutionProvider"])
    # Use the actual input name from the session (dynamo and TorchScript may differ)
    inp_name = sess.get_inputs()[0].name
    ort_out = sess.run(None, {inp_name: dummy.numpy()})[0]
    diff = float(np.abs(enc(dummy).detach().numpy() - ort_out).max())
    print("max |torch - onnx| =", diff)
    cfg = {"onnx": "crop_encoder.onnx", "embeddings": "crop_embeddings.npy", "crops": [c["name"] for c in crops],
           "mean": [0.48145466, 0.4578275, 0.40821073], "std": [0.26862954, 0.26130258, 0.27577711], "size": 224,
           "logit_scale": float(model.logit_scale.exp()), "threshold": a.threshold}
    json.dump(cfg, open(out / "config.json", "w", encoding="utf-8"), indent=2)
    print(f"Saved {len(crops)} crops to {out}. Restart the server; /api/v1/health will show crop_id: true")


if __name__ == "__main__":
    main()
