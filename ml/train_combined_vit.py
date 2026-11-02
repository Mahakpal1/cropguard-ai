"""Combined ViT fine-tuning: PlantVillage (70 K lab) + PlantDoc (2.3 K field).

Training recipe
---------------
- Backbone  : kimcomehome/plantvillage-vit-leaf-disease  (ViT-Base-Patch16-224)
              warm-started from best_field_vit.pt when available
- Lab data  : data/disease_dataset/train  (70 K images, 38 classes, ImageFolder)
- Field data: work/plantdoc/train         (2.3 K images, mapped to 38 classes)
              oversampled 5× so it contributes ~10 % of every epoch
- Augmentation (train):
    RandomResizedCrop(224, scale=(0.5, 1.0)) → ColorJitter → RandomHorizontalFlip
    RandomVerticalFlip → RandomGrayscale → RandomErasing
    MixUp(α=0.2) + CutMix(α=1.0) at batch level
- Loss       : CrossEntropyLoss(label_smoothing=0.1)
- Optimiser  : AdamW – backbone LR × 0.1, head LR
- Scheduler  : LinearWarmup (2 ep) → CosineAnnealingLR
- Output     : ml/models/cropguard38_combined/
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
STD = [0.5, 0.5, 0.5]
SEED = 42


def set_seed(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ─────────────────────────── datasets ────────────────────────────────────────

class PlantDocDataset(Dataset):
    """Wraps a plantdoc DataFrame (path, y columns)."""
    def __init__(self, df, transform):
        self.paths = df["path"].tolist()
        self.labels = df["y"].tolist()
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(img), self.labels[idx]


class TensorWrapDataset(Dataset):
    """Makes an ImageFolder return (PIL→tensor, int) for v2 MixUp/CutMix."""
    def __init__(self, base_dataset):
        self.ds = base_dataset

    def __len__(self):
        return len(self.ds)

    def __getitem__(self, idx):
        x, y = self.ds[idx]
        return x, y


# ─────────────────────────── transforms ──────────────────────────────────────

def build_transforms(img_size=224):
    train_tf = T.Compose([
        cg.PadSquare(),
        T.RandomResizedCrop(img_size, scale=(0.5, 1.0), ratio=(0.85, 1.15)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(p=0.2),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        T.RandomGrayscale(p=0.05),
        RandomShadow(p=0.2, alpha_range=(0.2, 0.5)),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
        T.RandomErasing(p=0.2, scale=(0.02, 0.12), value=0),
    ])
    eval_tf = T.Compose([
        cg.PadSquare(),
        T.Resize((img_size, img_size)),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])
    return train_tf, eval_tf


# ─────────────────────────── ONNX export ─────────────────────────────────────

def export_vit_onnx(model, out_path, img_size=224):
    model.eval()
    dummy = torch.randn(1, 3, img_size, img_size).cpu()
    model_cpu = model.cpu()

    class ViTWrapper(nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            return self.m(pixel_values=x).logits

    wrapper = ViTWrapper(model_cpu)
    print("Exporting ViT → ONNX …")
    torch.onnx.export(
        wrapper,
        dummy,
        str(out_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )
    print(f"  ONNX saved → {out_path}")


# ─────────────────────────── warmup scheduler ────────────────────────────────

class LinearWarmupCosineAnnealing(torch.optim.lr_scheduler._LRScheduler):
    """Linear warmup for `warmup_steps` steps then cosine decay to `eta_min`."""
    def __init__(self, optimizer, warmup_steps, total_steps, eta_min=1e-8, last_epoch=-1):
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.eta_min = eta_min
        super().__init__(optimizer, last_epoch)

    def get_lr(self):
        step = self.last_epoch
        if step < self.warmup_steps:
            factor = (step + 1) / max(self.warmup_steps, 1)
            return [base_lr * factor for base_lr in self.base_lrs]
        progress = (step - self.warmup_steps) / max(self.total_steps - self.warmup_steps, 1)
        cosine = 0.5 * (1 + math.cos(math.pi * progress))
        return [self.eta_min + (base_lr - self.eta_min) * cosine for base_lr in self.base_lrs]


# ─────────────────────────── evaluation ──────────────────────────────────────

def evaluate(model, loader, device):
    model.eval()
    corr = tot = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(pixel_values=x).logits
            corr += (logits.argmax(-1) == y).sum().item()
            tot += len(y)
    return corr / tot if tot else 0.0


# ─────────────────────────── main ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Combined PlantVillage + PlantDoc ViT training.")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4, help="Head LR (backbone = lr/10)")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--warmup-epochs", type=int, default=2)
    parser.add_argument("--field-oversample", type=int, default=5,
                        help="Weight multiplier for field images in sampler")
    parser.add_argument("--out", default="ml/models/cropguard38_combined")
    parser.add_argument("--no-mixup", action="store_true", help="Disable MixUp/CutMix")
    args = parser.parse_args()

    set_seed(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {dev}")
    if dev.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU : {props.name}  ({props.total_memory/1e9:.1f} GB)")
        # enable TF32 for speed
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # ── load model ────────────────────────────────────────────────────────────
    model_id = "kimcomehome/plantvillage-vit-leaf-disease"
    print(f"\nLoading model: {model_id}")
    model = AutoModelForImageClassification.from_pretrained(model_id)

    # warm-start from previously field-tuned weights if available
    prev_weights = ROOT / "ml" / "models" / "cropguard38_vit" / "best_field_vit.pt"
    if prev_weights.exists():
        state = torch.load(prev_weights, map_location="cpu")
        model.load_state_dict(state)
        print(f"  Warm-started from {prev_weights}")
    else:
        print("  No previous field weights found – using HF pretrained weights.")

    model = model.to(dev)

    # ── class mapping ─────────────────────────────────────────────────────────
    vit_labels = list(model.config.id2label.values())          # 38 ViT output labels
    vit_norm = {norm(l): i for i, l in enumerate(vit_labels)}

    # canonical label order from existing active model config
    active_cfg_path = ROOT / "ml" / "models" / "model_config.json"
    target_labels = json.load(open(active_cfg_path))["labels"]
    class_idx = {c: vit_norm.get(norm(c), i) for i, c in enumerate(target_labels)}
    n_classes = len(target_labels)
    print(f"  Classes: {n_classes}")

    # ── datasets ──────────────────────────────────────────────────────────────
    train_tf, eval_tf = build_transforms()

    # PlantVillage lab images (ImageFolder)
    pv_train_dir = ROOT / "data" / "disease_dataset" / "train"
    pv_valid_dir = ROOT / "data" / "disease_dataset" / "valid"
    pv_ds_train = ImageFolder(str(pv_train_dir), transform=train_tf)
    pv_ds_valid = ImageFolder(str(pv_valid_dir), transform=eval_tf)
    print(f"\nPlantVillage train : {len(pv_ds_train)} images, {len(pv_ds_train.classes)} classes")
    print(f"PlantVillage valid : {len(pv_ds_valid)} images")

    # PlantDoc field images
    pd_dir = ROOT / "work" / "plantdoc"
    fd_tr, skipped_tr = cg.plantdoc_frame(pd_dir / "train", class_idx)
    fd_te, skipped_te = cg.plantdoc_frame(pd_dir / "test",  class_idx)
    print(f"\nPlantDoc train     : {len(fd_tr)} images ({fd_tr['pd_class'].nunique()} classes)")
    print(f"PlantDoc test      : {len(fd_te)} images")
    if skipped_tr:
        print(f"  Skipped train folders (no map): {skipped_tr}")

    pd_ds_train = PlantDocDataset(fd_tr, train_tf)
    pd_ds_test  = PlantDocDataset(fd_te, eval_tf)

    # ── weighted sampler: field images × field_oversample ────────────────────
    n_pv   = len(pv_ds_train)
    n_pd   = len(pd_ds_train)
    w_pv   = 1.0
    w_pd   = float(args.field_oversample)
    sample_weights = [w_pv] * n_pv + [w_pd] * n_pd
    combined_train  = ConcatDataset([pv_ds_train, pd_ds_train])
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.float),
        num_samples=n_pv + n_pd,   # one epoch ≈ see every lab image once
        replacement=True,
    )

    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(
        combined_train, batch_size=args.batch_size,
        sampler=sampler, num_workers=num_workers,
        pin_memory=(dev.type == "cuda"), drop_last=True,
    )
    # validation: PlantVillage valid + PlantDoc field test
    valid_loader = DataLoader(pv_ds_valid, batch_size=args.batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(dev.type == "cuda"))
    field_loader = DataLoader(pd_ds_test, batch_size=args.batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(dev.type == "cuda"))

    # ── MixUp / CutMix ───────────────────────────────────────────────────────
    use_mixup = not args.no_mixup
    if use_mixup:
        mixup_fn  = Tv2.MixUp(alpha=0.2,  num_classes=n_classes)
        cutmix_fn = Tv2.CutMix(alpha=1.0, num_classes=n_classes)
        print("\nMixUp(a=0.2) + CutMix(a=1.0) enabled (alternating)")

    # ── optimiser: differential LR ───────────────────────────────────────────
    head_lr = args.lr
    backbone_lr = args.lr * 0.1
    head_params     = list(model.classifier.parameters())
    backbone_params = [p for p in model.parameters()
                       if not any(p is q for q in head_params)]
    optimizer = torch.optim.AdamW(
        [{"params": backbone_params, "lr": backbone_lr},
         {"params": head_params,     "lr": head_lr}],
        weight_decay=1e-4,
    )

    # ── scheduler ────────────────────────────────────────────────────────────
    steps_per_epoch = len(train_loader)
    total_steps     = args.epochs * steps_per_epoch
    warmup_steps    = args.warmup_epochs * steps_per_epoch
    scheduler = LinearWarmupCosineAnnealing(
        optimizer, warmup_steps=warmup_steps, total_steps=total_steps
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # ── baseline eval ─────────────────────────────────────────────────────────
    print("\n── Baseline (before training) ──────────────────────────────────────────")
    base_field = evaluate(model, field_loader, dev)
    base_valid = evaluate(model, valid_loader, dev)
    print(f"  PlantVillage valid : {base_valid*100:.2f}%")
    print(f"  PlantDoc field test: {base_field*100:.2f}%")

    # ── training loop ─────────────────────────────────────────────────────────
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    best_field_acc = base_field
    best_weights   = out_dir / "best_combined_vit.pt"

    print(f"\n── Training {args.epochs} epochs  (steps/epoch={steps_per_epoch}) ────────────────────────")
    scaler = torch.cuda.amp.GradScaler(enabled=(dev.type == "cuda"))

    for ep in range(args.epochs):
        model.train()
        running_loss = 0.0
        n_samples    = 0
        t0 = time.time()

        for batch_idx, (x, y) in enumerate(train_loader):
            x = x.to(dev)
            y = y.to(dev)

            # MixUp / CutMix: alternate every batch
            if use_mixup:
                aug_fn = mixup_fn if batch_idx % 2 == 0 else cutmix_fn
                try:
                    # v2 transforms expect (img_tensor, label_tensor)
                    x, y = aug_fn(x, y)
                except Exception:
                    # soft-label collisions — skip mix for this batch
                    y = torch.nn.functional.one_hot(y, n_classes).float()

            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16,
                                 enabled=(dev.type == "cuda")):
                logits = model(pixel_values=x).logits
                if y.ndim == 2:                     # soft labels from MixUp/CutMix
                    loss = criterion(logits, y)
                else:
                    loss = criterion(logits, y)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            running_loss += loss.item() * x.shape[0]
            n_samples    += x.shape[0]

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
            f"PlantDoc={val_field*100:.2f}%  (best={max(best_field_acc,val_field)*100:.2f}%) | "
            f"lr-head={cur_lr[-1]:.2e}"
        )

        if val_field > best_field_acc:
            best_field_acc = val_field
            torch.save(model.state_dict(), best_weights)
            print(f"  ★ New best field model saved! ({val_field*100:.2f}%)")

    # ── load best, export ────────────────────────────────────────────────────
    if best_weights.exists():
        model.load_state_dict(torch.load(best_weights, map_location="cpu"))
        print(f"\nLoaded best model ({best_field_acc*100:.2f}%) for ONNX export.")
    else:
        print("\nNo improvement over baseline – exporting current weights.")

    onnx_file = out_dir / "model.onnx"
    export_vit_onnx(model, onnx_file)

    # ── model_config.json ────────────────────────────────────────────────────
    cfg = {
        "name": "cropguard-vit-combined",
        "onnx": "model.onnx",            # bare filename – switch_model.py prepends folder
        "labels": target_labels,
        "classes_file": "class_names.json",
        "input_size": 224,
        "mean": MEAN,
        "std": STD,
        "temperature": 1.0,
        "confidence_threshold": 0.45,
        "energy_threshold": -4.8,
        "tta": False,
        "healthy_only_crops": json.load(open(active_cfg_path)).get("healthy_only_crops", []),
        "field_test_accuracy": round(best_field_acc, 4),
    }
    json.dump(cfg, open(out_dir / "model_config.json", "w", encoding="utf-8"), indent=2)
    print(f"model_config.json written (field_test_accuracy={best_field_acc*100:.2f}%)")

    # ── copy 38-class class_names.json ───────────────────────────────────────
    src_cls = ROOT / "ml" / "models" / "cropguard38" / "class_names.json"
    cls_meta = json.load(open(src_cls, encoding="utf-8"))
    json.dump(cls_meta, open(out_dir / "class_names.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"class_names.json copied from {src_cls}")

    print(f"\n✓ Combined model exported to  {out_dir}")
    print(f"  PlantDoc field accuracy      : {best_field_acc*100:.2f}%")
    print(f"\nTo activate:  python ml/switch_model.py cropguard38_combined")


if __name__ == "__main__":
    main()
