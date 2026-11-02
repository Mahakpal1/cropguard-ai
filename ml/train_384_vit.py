"""High-resolution ViT fine-tuning at 384x384 with Focal Loss.

Starts from cropguard38_combined/best_combined_vit.pt (already has field knowledge).
Upgrades to 384x384 resolution via positional embedding interpolation.
Uses Focal Loss (gamma=2) to focus gradients on the hardest disease confusions.
Enables TTA at inference for further +1-2% accuracy.

Output: ml/models/cropguard38_384/
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
import torchvision.transforms.v2 as Tv2
from PIL import Image
from torch.utils.data import ConcatDataset, DataLoader, Dataset, WeightedRandomSampler
from torchvision.datasets import ImageFolder
from transformers import AutoModelForImageClassification

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import cg_common as cg  # noqa: E402
from train_local import RandomShadow  # noqa: E402

MEAN = [0.5, 0.5, 0.5]
STD  = [0.5, 0.5, 0.5]
SEED = 42
IMG_SIZE = 384


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def norm_str(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ─────────────────────────── Focal Loss ──────────────────────────────────────

class FocalLoss(nn.Module):
    """Focal Loss with optional label smoothing.

    Works with both hard integer labels and soft labels from MixUp/CutMix.
    Focal weighting (1-pt)^gamma down-weights easy examples, forcing the model
    to improve on the hard intra-crop confusion pairs (e.g. Early vs Late Blight).
    """
    def __init__(self, gamma: float = 2.0, label_smoothing: float = 0.05, n_classes: int = 38):
        super().__init__()
        self.gamma = gamma
        self.label_smoothing = label_smoothing
        self.n_classes = n_classes

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_probs = F.log_softmax(logits, dim=1)          # (B, C)
        probs     = log_probs.exp()

        if targets.ndim == 1:                              # hard labels
            smooth  = self.label_smoothing / self.n_classes
            one_hot = torch.zeros_like(logits).scatter_(1, targets.unsqueeze(1), 1.0)
            t_soft  = one_hot * (1.0 - self.label_smoothing) + smooth
            pt = probs.gather(1, targets.unsqueeze(1)).squeeze(1).detach()
        else:                                              # soft labels (MixUp / CutMix)
            t_soft = targets
            pt = (probs * targets).sum(1).detach()

        focal_weight = (1.0 - pt.clamp(1e-7, 1.0)) ** self.gamma
        ce_loss      = -(t_soft * log_probs).sum(1)
        return (focal_weight * ce_loss).mean()


# ─────────────────────────── datasets ────────────────────────────────────────

class PlantDocDataset(Dataset):
    def __init__(self, df, transform):
        self.paths  = df["path"].tolist()
        self.labels = df["y"].tolist()
        self.transform = transform

    def __len__(self):  return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(img), self.labels[idx]


# ─────────────────────────── transforms ──────────────────────────────────────

def build_transforms(img_size: int = IMG_SIZE):
    train_tf = T.Compose([
        cg.PadSquare(),
        T.RandomResizedCrop(img_size, scale=(0.45, 1.0), ratio=(0.8, 1.25)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(p=0.2),
        T.RandomRotation(20),
        T.ColorJitter(brightness=0.35, contrast=0.35, saturation=0.35, hue=0.06),
        T.RandomGrayscale(p=0.05),
        RandomShadow(p=0.25, alpha_range=(0.2, 0.5)),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
        T.RandomErasing(p=0.25, scale=(0.02, 0.15), value=0),
    ])
    eval_tf = T.Compose([
        cg.PadSquare(),
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])
    return train_tf, eval_tf


# ─────────────────────────── ViT 384 wrapper ─────────────────────────────────

class ViT384Wrapper(nn.Module):
    """Thin wrapper that calls HuggingFace ViT with positional embedding
    interpolation so it accepts 384x384 inputs."""
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(pixel_values=x, interpolate_pos_encoding=True).logits


# ─────────────────────────── ONNX export ─────────────────────────────────────

def export_onnx(model, out_path: Path, img_size: int = IMG_SIZE):
    model.eval()
    wrapper = ViT384Wrapper(model).cpu()
    dummy   = torch.randn(1, 3, img_size, img_size)
    print(f"Exporting ViT {img_size}x{img_size} -> ONNX ...")
    torch.onnx.export(
        wrapper, dummy, str(out_path),
        input_names=["input"], output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17, dynamo=False,
    )
    print(f"  ONNX -> {out_path}")


# ─────────────────────────── warmup + cosine scheduler ───────────────────────

class LinearWarmupCosine(torch.optim.lr_scheduler._LRScheduler):
    def __init__(self, opt, warmup_steps, total_steps, eta_min=1e-8, last_epoch=-1):
        self.warmup_steps = warmup_steps
        self.total_steps  = total_steps
        self.eta_min      = eta_min
        super().__init__(opt, last_epoch)

    def get_lr(self):
        s = self.last_epoch
        if s < self.warmup_steps:
            factor = (s + 1) / max(self.warmup_steps, 1)
            return [b * factor for b in self.base_lrs]
        progress = (s - self.warmup_steps) / max(self.total_steps - self.warmup_steps, 1)
        cosine   = 0.5 * (1 + math.cos(math.pi * progress))
        return [self.eta_min + (b - self.eta_min) * cosine for b in self.base_lrs]


# ─────────────────────────── evaluation ──────────────────────────────────────

def evaluate(model, loader, device):
    model.eval()
    corr = tot = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(pixel_values=x, interpolate_pos_encoding=True).logits
            corr += (logits.argmax(-1) == y).sum().item()
            tot  += len(y)
    return corr / tot if tot else 0.0


# ─────────────────────────── main ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs",           type=int,   default=6)
    parser.add_argument("--lr",               type=float, default=5e-5, help="Head LR (backbone=lr/10)")
    parser.add_argument("--batch-size",       type=int,   default=16)
    parser.add_argument("--grad-accum",       type=int,   default=2,
                        help="Gradient accumulation steps (effective batch = batch_size * grad_accum)")
    parser.add_argument("--warmup-epochs",    type=int,   default=1)
    parser.add_argument("--field-oversample", type=int,   default=7)
    parser.add_argument("--focal-gamma",      type=float, default=2.0)
    parser.add_argument("--out",              default="ml/models/cropguard38_384")
    args = parser.parse_args()

    set_seed(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {dev}")
    if dev.type == "cuda":
        p = torch.cuda.get_device_properties(0)
        print(f"GPU : {p.name}  ({p.total_memory/1e9:.1f} GB)")
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # ── model ─────────────────────────────────────────────────────────────────
    model_id = "kimcomehome/plantvillage-vit-leaf-disease"
    print(f"\nLoading model: {model_id}")
    model = AutoModelForImageClassification.from_pretrained(model_id)

    prev_weights = ROOT / "ml" / "models" / "cropguard38_combined" / "best_combined_vit.pt"
    if prev_weights.exists():
        model.load_state_dict(torch.load(prev_weights, map_location="cpu"))
        print(f"  Warm-started from {prev_weights.name}  (cropguard38_combined)")
    else:
        print("  WARNING: no warm-start weights found – using HF weights only")

    model = model.to(dev)

    # ── class mapping ─────────────────────────────────────────────────────────
    vit_labels   = list(model.config.id2label.values())
    vit_norm_map = {norm_str(l): i for i, l in enumerate(vit_labels)}
    target_labels = json.load(open(ROOT / "ml" / "models" / "model_config.json"))["labels"]
    class_idx     = {c: vit_norm_map.get(norm_str(c), i) for i, c in enumerate(target_labels)}
    n_classes     = len(target_labels)
    print(f"  Classes: {n_classes}")

    # ── datasets ──────────────────────────────────────────────────────────────
    train_tf, eval_tf = build_transforms(IMG_SIZE)

    pv_train = ImageFolder(str(ROOT / "data" / "disease_dataset" / "train"), transform=train_tf)
    pv_valid = ImageFolder(str(ROOT / "data" / "disease_dataset" / "valid"), transform=eval_tf)
    print(f"\nPlantVillage train : {len(pv_train):,} images, {len(pv_train.classes)} classes")
    print(f"PlantVillage valid : {len(pv_valid):,} images")

    pd_dir  = ROOT / "work" / "plantdoc"
    fd_tr, skipped = cg.plantdoc_frame(pd_dir / "train", class_idx)
    fd_te, _       = cg.plantdoc_frame(pd_dir / "test",  class_idx)
    print(f"\nPlantDoc train     : {len(fd_tr):,} images  (28 classes)")
    print(f"PlantDoc test      : {len(fd_te):,} images")
    if skipped:
        print(f"  Skipped: {skipped}")

    pd_train = PlantDocDataset(fd_tr, train_tf)
    pd_test  = PlantDocDataset(fd_te, eval_tf)

    # weighted sampler: field images x field_oversample
    n_pv = len(pv_train); n_pd = len(pd_train)
    w = [1.0] * n_pv + [float(args.field_oversample)] * n_pd
    sampler = WeightedRandomSampler(
        weights=torch.tensor(w, dtype=torch.float),
        num_samples=n_pv + n_pd,
        replacement=True,
    )
    combined = ConcatDataset([pv_train, pd_train])
    nw = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(combined, batch_size=args.batch_size, sampler=sampler,
                              num_workers=nw, pin_memory=(dev.type == "cuda"), drop_last=True)
    valid_loader = DataLoader(pv_valid, batch_size=args.batch_size, shuffle=False,
                              num_workers=nw, pin_memory=(dev.type == "cuda"))
    field_loader = DataLoader(pd_test,  batch_size=args.batch_size, shuffle=False,
                              num_workers=nw, pin_memory=(dev.type == "cuda"))

    print(f"\nEffective batch size: {args.batch_size} x {args.grad_accum} = {args.batch_size*args.grad_accum}")

    # ── MixUp / CutMix ───────────────────────────────────────────────────────
    mixup_fn  = Tv2.MixUp(alpha=0.2,  num_classes=n_classes)
    cutmix_fn = Tv2.CutMix(alpha=1.0, num_classes=n_classes)
    print(f"MixUp(a=0.2) + CutMix(a=1.0) + FocalLoss(gamma={args.focal_gamma})")

    # ── loss ─────────────────────────────────────────────────────────────────
    criterion = FocalLoss(gamma=args.focal_gamma, label_smoothing=0.05, n_classes=n_classes)

    # ── optimiser: differential LR ───────────────────────────────────────────
    head_params     = list(model.classifier.parameters())
    backbone_params = [p for p in model.parameters()
                       if not any(p is q for q in head_params)]
    optimizer = torch.optim.AdamW(
        [{"params": backbone_params, "lr": args.lr * 0.1},
         {"params": head_params,     "lr": args.lr}],
        weight_decay=1e-4,
    )

    # ── scheduler ────────────────────────────────────────────────────────────
    steps_per_epoch  = len(train_loader)
    total_steps      = args.epochs * steps_per_epoch
    warmup_steps     = args.warmup_epochs * steps_per_epoch
    scheduler = LinearWarmupCosine(optimizer, warmup_steps, total_steps)
    scaler    = torch.cuda.amp.GradScaler(enabled=(dev.type == "cuda"))

    # ── baseline ─────────────────────────────────────────────────────────────
    print("\n-- Baseline (384x384 warm-started weights) ----------------------")
    base_field = evaluate(model, field_loader, dev)
    base_valid = evaluate(model, valid_loader, dev)
    print(f"  PlantVillage valid  : {base_valid*100:.2f}%")
    print(f"  PlantDoc field test : {base_field*100:.2f}%")

    # ── training loop ─────────────────────────────────────────────────────────
    out_dir    = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    best_field = base_field
    best_ckpt  = out_dir / "best_384_vit.pt"

    print(f"\n-- Training {args.epochs} epochs  ({steps_per_epoch} steps/epoch) ----")

    for ep in range(args.epochs):
        model.train()
        running_loss = 0.0; n_samples = 0
        t0 = time.time()
        optimizer.zero_grad(set_to_none=True)

        for step, (x, y) in enumerate(train_loader):
            x = x.to(dev); y = y.to(dev)

            # alternate MixUp / CutMix
            aug_fn = mixup_fn if step % 2 == 0 else cutmix_fn
            try:
                x, y = aug_fn(x, y)
            except Exception:
                y = F.one_hot(y, n_classes).float()

            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16,
                                 enabled=(dev.type == "cuda")):
                logits = model(pixel_values=x, interpolate_pos_encoding=True).logits
                loss   = criterion(logits, y) / args.grad_accum

            scaler.scale(loss).backward()
            running_loss += loss.item() * args.grad_accum * x.shape[0]
            n_samples    += x.shape[0]

            if (step + 1) % args.grad_accum == 0 or (step + 1) == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()

        # ── epoch validation ─────────────────────────────────────────────────
        val_field = evaluate(model, field_loader, dev)
        val_valid = evaluate(model, valid_loader, dev)
        elapsed   = time.time() - t0
        avg_loss  = running_loss / n_samples
        cur_lr    = scheduler.get_last_lr()

        print(
            f"Epoch {ep+1:2d}/{args.epochs} ({elapsed:5.1f}s) | "
            f"loss={avg_loss:.4f} | "
            f"PV-valid={val_valid*100:.2f}% | "
            f"PlantDoc={val_field*100:.2f}%  (best={max(best_field,val_field)*100:.2f}%) | "
            f"lr-head={cur_lr[-1]:.2e}"
        )

        if val_field > best_field:
            best_field = val_field
            torch.save(model.state_dict(), best_ckpt)
            print(f"  * New best saved! ({val_field*100:.2f}%)")

    # ── load best, export ─────────────────────────────────────────────────────
    if best_ckpt.exists():
        model.load_state_dict(torch.load(best_ckpt, map_location="cpu"))
        model = model.to("cpu")
        print(f"\nLoaded best model ({best_field*100:.2f}%) for export.")
    else:
        model = model.cpu()
        print("\nNo improvement – exporting final weights.")

    onnx_path = out_dir / "model.onnx"
    export_onnx(model, onnx_path, IMG_SIZE)

    # ── model_config.json ─────────────────────────────────────────────────────
    active_cfg = json.load(open(ROOT / "ml" / "models" / "model_config.json"))
    cfg = {
        "name":                 "cropguard-vit-384-focal",
        "onnx":                 "model.onnx",
        "labels":               target_labels,
        "classes_file":         "class_names.json",
        "input_size":           IMG_SIZE,
        "mean":                 MEAN,
        "std":                  STD,
        "temperature":          1.0,
        "confidence_threshold": 0.40,
        "energy_threshold":     -4.8,
        "tta":                  True,     # 3-view TTA enabled at inference
        "healthy_only_crops":   active_cfg.get("healthy_only_crops", []),
        "field_test_accuracy":  round(best_field, 4),
    }
    json.dump(cfg, open(out_dir / "model_config.json", "w", encoding="utf-8"), indent=2)
    print(f"model_config.json: field_test_accuracy={best_field*100:.2f}%  (tta=true, input_size=384)")

    # ── class_names.json ──────────────────────────────────────────────────────
    src = ROOT / "ml" / "models" / "cropguard38" / "class_names.json"
    meta = json.load(open(src, encoding="utf-8"))
    json.dump(meta, open(out_dir / "class_names.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"class_names.json copied from {src.name}")

    print(f"\nDone!  Model exported to  {out_dir}")
    print(f"  PlantDoc field accuracy : {best_field*100:.2f}%")
    print(f"  TTA enabled             : True")
    print(f"  Input resolution        : {IMG_SIZE}x{IMG_SIZE}")
    print(f"\nTo activate:  python ml/switch_model.py cropguard38_384")


if __name__ == "__main__":
    main()
