"""Train a plant-disease classifier on the unified dataset (run on Colab or a local NVIDIA GPU) and write an installable model folder.

    python ml/train_union.py --data data/union --out ml/models/union --backbone efficientnet_b0 --epochs 12
        [--holdout-source plantdoc]   # test on a whole dataset the model never saw (honest generalisation estimate)
        [--ood-crops Apple,Grape]     # leave these crops OUT of training and use them to test unknown-crop rejection
        [--no-pretrained] [--quick]   # --quick = tiny smoke test

What it does differently from the first notebook: many sources and crops, leaf/hash-group-aware splits, class-balanced sampling,
scale augmentation (close-ups like a single big lesion), background replacement for lab photos, calibration (temperature),
an energy gate for unfamiliar images, and a confidence threshold chosen for a target precision. Energy and thresholds are computed
without test-time augmentation here; after installing, run  python ml/calibrate_gates.py  on a held-out field folder for the final values.
"""
import argparse
import json
import random
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image, ImageFilter
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
warnings.filterwarnings("ignore", category=UserWarning)


class PadSquare:                       # identical to the backend: keep the WHOLE photo, grey padding
    def __call__(self, im):
        w, h = im.size
        if w == h:
            return im
        s = max(w, h); out = Image.new("RGB", (s, s), (128, 128, 128)); out.paste(im, ((s - w) // 2, (s - h) // 2))
        return out


class BGReplace:                       # lab photos only: paste the leaf on random soil/grass/grey textures
    def __init__(self, p=0.5): self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        a = np.asarray(img).astype(np.float32) / 255
        sat = (a.max(2) - a.min(2)) / (a.max(2) + 1e-6)
        m = ((sat > .18) & (a.max(2) > .12)).astype(np.uint8) * 255
        m = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)[..., None] / 255
        h, w = a.shape[:2]
        base = np.array(random.choice([[.35, .25, .17], [.25, .45, .2], [.6, .6, .6], [.5, .5, .5]])) + np.random.uniform(-.1, .1, 3)
        bg = np.ones((h, w, 3), np.float32) * base
        yy, xx = np.ogrid[:h, :w]
        for _ in range(random.randint(8, 20)):
            cy, cx, r = random.randint(0, h), random.randint(0, w), random.randint(10, 60)
            bg[(yy - cy) ** 2 + (xx - cx) ** 2 < r * r] = np.clip(base + np.random.uniform(-.2, .2, 3), 0, 1)
        bg = np.asarray(Image.fromarray((bg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(random.uniform(2, 8)))).astype(np.float32) / 255
        return Image.fromarray(((a * m + bg * (1 - m)) * 255).astype(np.uint8))


def transforms(img):
    common = [T.RandomResizedCrop(img, scale=(0.25, 1.0), ratio=(0.75, 1.33)), T.RandomHorizontalFlip(), T.RandomVerticalFlip(0.2),
              T.RandomRotation(25), T.ColorJitter(0.3, 0.3, 0.3, 0.05), T.RandomApply([T.GaussianBlur(5, (0.1, 2.0))], p=0.3),
              T.ToTensor(), T.Normalize(MEAN, STD)]
    return (T.Compose([PadSquare(), BGReplace(0.5)] + common), T.Compose([PadSquare()] + common),
            T.Compose([PadSquare(), T.Resize((img, img)), T.ToTensor(), T.Normalize(MEAN, STD)]))


class DS(Dataset):
    def __init__(self, root, frame, tf_lab, tf_field):
        self.root, self.p, self.y, self.s, self.a, self.b = Path(root), frame.path.tolist(), frame.y.tolist(), frame.source.tolist(), tf_lab, tf_field

    def __len__(self): return len(self.p)

    def __getitem__(self, i):
        im = Image.open(self.root / self.p[i]).convert("RGB")
        return (self.a if self.s[i] == "plantvillage" else self.b)(im), self.y[i]


@torch.no_grad()
def get_logits(model, dl, dev):
    model.eval().to(dev); out, ys = [], []
    for x, y in dl:
        with torch.autocast(device_type=dev.type, enabled=dev.type == "cuda"):
            out.append(model(x.to(dev)).float().cpu())
        ys.append(y)
    return torch.cat(out), torch.cat(ys)


def ece(p, y, bins=15):
    conf, pred = p.max(1); acc = (pred == y).float(); e = 0.0
    edges = torch.linspace(0, 1, bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.float().mean().item() * abs(acc[m].mean().item() - conf[m].mean().item())
    return e


def fit_temperature(lg, y):
    t = torch.zeros(1, requires_grad=True); opt = torch.optim.LBFGS([t], lr=0.1, max_iter=100)
    def closure():
        opt.zero_grad(); l = F.cross_entropy(lg / t.exp(), y); l.backward(); return l
    opt.step(closure); return float(t.exp())


def energy(lg): return -torch.logsumexp(lg, 1)


def auroc(pos, neg):
    s = np.concatenate([pos, neg]); r = s.argsort().argsort() + 1
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def export_onnx(model, dummy, path):
    """Newer PyTorch versions changed torch.onnx.export; try the classic exporter first, then the default."""
    kw = dict(input_names=["input"], output_names=["logits"], dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17)
    try:
        torch.onnx.export(model, dummy, path, dynamo=False, **kw)
    except Exception:
        torch.onnx.export(model, dummy, path, **kw)


def train(model, loader, val_loader, epochs, lr, tag, dev):
    model.to(dev)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=max(1, epochs * len(loader)))
    scaler = torch.cuda.amp.GradScaler(enabled=dev.type == "cuda"); crit = nn.CrossEntropyLoss(label_smoothing=0.1); best = (-1, None)
    for ep in range(epochs):
        model.train(); t0 = time.time(); tl = n = 0
        for x, y in loader:
            x, y = x.to(dev), y.to(dev)
            with torch.autocast(device_type=dev.type, enabled=dev.type == "cuda"):
                loss = crit(model(x), y)
            opt.zero_grad(set_to_none=True); scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            tl += loss.item() * len(y); n += len(y)
        lg, ys = get_logits(model, val_loader, dev); va = (lg.argmax(1) == ys).float().mean().item()
        if va > best[0]:
            best = (va, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()})
        print(f"[{tag}] epoch {ep+1}/{epochs} loss {tl/max(n,1):.4f} val_acc {va:.4f} ({time.time()-t0:.0f}s)", flush=True)
    model.load_state_dict(best[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/union"); ap.add_argument("--out", default="ml/models/union")
    ap.add_argument("--backbone", default="efficientnet_b0"); ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--img", type=int, default=224); ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--holdout-source"); ap.add_argument("--ood-crops", default="")
    ap.add_argument("--target-precision", type=float, default=0.9)
    ap.add_argument("--no-pretrained", action="store_true"); ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    if a.quick:
        a.bs = min(a.bs, 8)
    import os, timm
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if dev.type == "cpu":
        print("WARNING: no GPU. Use Colab or --quick.")
    workers = 0 if (os.name == "nt" or a.quick) else 2
    root = Path(a.data); df = pd.read_csv(root / "manifest.csv")
    ood_crops = [c.strip() for c in a.ood_crops.split(",") if c.strip()]
    ood = df[df.label.str.split("___").str[0].isin(ood_crops)]; df = df[~df.index.isin(ood.index)].reset_index(drop=True)
    if a.quick:
        df = df.groupby("label", group_keys=False).apply(lambda g: g.sample(min(len(g), 24), random_state=a.seed)).reset_index(drop=True)
    classes = sorted(df.label.unique()); idx = {c: i for i, c in enumerate(classes)}; df["y"] = df.label.map(idx)
    print(f"{len(df)} images, {len(classes)} classes, {df.label.str.split('___').str[0].nunique()} crops; OOD-only images: {len(ood)}")

    k = 5 if a.quick else 10
    if a.holdout_source:
        te = df[df.source == a.holdout_source]; rest = df[df.source != a.holdout_source]
        folds = [i for _, i in StratifiedGroupKFold(k, shuffle=True, random_state=a.seed).split(rest, rest.y, rest.group)]
        va, tr = rest.iloc[folds[0]], rest.iloc[np.concatenate(folds[1:])]
    else:
        folds = [i for _, i in StratifiedGroupKFold(k, shuffle=True, random_state=a.seed).split(df, df.y, df.group)]
        te, va, tr = df.iloc[folds[0]], df.iloc[folds[1]], df.iloc[np.concatenate(folds[2:])]
    assert not (set(tr.group) & set(te.group)) or a.holdout_source, "group leak between train and test"
    print(f"train {len(tr)} | val {len(va)} | test {len(te)}")

    tf_lab, tf_field, tf_eval = transforms(a.img)
    w = 1.0 / tr.y.map(tr.y.value_counts()).astype(float) ** 0.5            # soften class imbalance
    sampler = WeightedRandomSampler(torch.tensor(w.values, dtype=torch.double), num_samples=len(tr), replacement=True)
    L_tr = DataLoader(DS(root, tr, tf_lab, tf_field), batch_size=a.bs, sampler=sampler, num_workers=workers, drop_last=True)
    mk = lambda f: DataLoader(DS(root, f, tf_eval, tf_eval), batch_size=a.bs, num_workers=workers)
    L_va, L_te = mk(va), mk(te)

    model = timm.create_model(a.backbone, pretrained=not a.no_pretrained, num_classes=len(classes))
    head = list(model.get_classifier().parameters())
    for p in model.parameters(): p.requires_grad = False
    for p in head: p.requires_grad = True
    train(model, L_tr, L_va, 1 if a.quick else 2, 1e-3, "head", dev)
    for p in model.parameters(): p.requires_grad = True
    train(model, L_tr, L_va, 1 if a.quick else a.epochs, 2e-4, "finetune", dev)

    # ---- evaluation and calibration -------------------------------------------------------
    lg_va, y_va = get_logits(model, L_va, dev); lg_te, y_te = get_logits(model, L_te, dev)
    T_ = fit_temperature(lg_va, y_va); pt = F.softmax(lg_te / T_, 1)
    pred = pt.argmax(1).numpy(); y = y_te.numpy()
    res = {"test_accuracy": float((pred == y).mean()), "test_macro_f1": float(f1_score(y, pred, average="macro")),
           "ece_before": ece(F.softmax(lg_te, 1), y_te), "ece_after": ece(pt, y_te), "temperature": T_, "classes": len(classes)}
    te2 = te.assign(ok=(pred == y), crop=te.label.str.split("___").str[0])
    res["accuracy_by_source"] = te2.groupby("source").ok.mean().round(4).to_dict()
    res["accuracy_by_crop"] = te2.groupby("crop").ok.mean().round(4).to_dict()
    pv, yv = F.softmax(lg_va / T_, 1).max(1)[0].numpy(), (lg_va.argmax(1) == y_va).numpy()
    thr = next((float(t) for t in np.arange(0.3, 0.96, 0.05) if (pv >= t).sum() >= 20 and yv[pv >= t].mean() >= a.target_precision), None)
    e_id = energy(lg_va).numpy(); e_thr = float(np.percentile(e_id, 95))
    res.update(confidence_threshold=thr, energy_threshold=e_thr)
    if len(ood):
        o = ood.sample(min(len(ood), 1500), random_state=a.seed).assign(y=0)
        e_ood = energy(get_logits(model, mk(o), dev)[0]).numpy()
        res.update(ood_auroc=auroc(e_ood, e_id), ood_caught=float((e_ood > e_thr).mean()), ood_images=int(len(o)))
    print(json.dumps(res, indent=2))

    # ---- export ----------------------------------------------------------------------------
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    try:
        timm.layers.set_exportable(True)
    except Exception:
        pass
    model.eval().cpu()
    export_onnx(model, torch.randn(1, 3, a.img, a.img), str(out / "model.onnx"))
    cfg = {"name": f"cropguard-{a.backbone}-union", "onnx": "model.onnx", "labels": classes, "input_size": a.img, "mean": MEAN, "std": STD,
           "temperature": T_, "confidence_threshold": thr if thr is not None else 0.6, "energy_threshold": e_thr, "tta": True}
    json.dump(cfg, open(out / "model_config.json", "w", encoding="utf-8"), indent=2)
    json.dump(res, open(out / "metrics.json", "w", encoding="utf-8"), indent=2)
    print(f"\nSaved to {out}.  Next:\n  python ml/switch_model.py {out.name}\n  python ml/datasets/make_class_names.py --manifest {root/'manifest.csv'} --out contracts/class_names.broad.json\n"
          f"  (set CLASSES_PATH=contracts/class_names.broad.json, restart the server, then run ml/calibrate_gates.py)")


if __name__ == "__main__":
    main()
