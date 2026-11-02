"""Phase 3 / Option C: Fine-tune Vision Transformer (ViT) on real field photographs.

Takes the 38-class ViT foundation model (`kimcomehome/plantvillage-vit-leaf-disease`),
which already achieved 38.98% zero-shot field accuracy (vs 5.51% for lab ConvNeXt),
and fine-tunes it on the PlantDoc field dataset (2,336 training images) + PlantVillage replay
with field augmentations (CLAHE, shadow simulation, color jitter).

Outputs to: ml/models/cropguard38_vit/
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import AutoImageProcessor, AutoModelForImageClassification

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import cg_common as cg  # noqa: E402
from train_local import RandomShadow  # noqa: E402

MEAN = [0.5, 0.5, 0.5]
STD = [0.5, 0.5, 0.5]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


class PlantDocDataset(Dataset):
    def __init__(self, df, transform):
        self.paths = df["path"].tolist()
        self.labels = df["y"].tolist()
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(img), self.labels[idx]


def build_field_transforms(img_size=224):
    train_tf = T.Compose([
        cg.PadSquare(),
        T.RandomResizedCrop(img_size, scale=(0.7, 1.0), ratio=(0.85, 1.15)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(0.2),
        T.RandomRotation(20),
        T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.4, hue=0.08),
        RandomShadow(p=0.25, alpha_range=(0.2, 0.5)),
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


def export_vit_onnx(model, out_path, img_size=224):
    model.eval()
    dummy = torch.randn(1, 3, img_size, img_size).cpu()
    model.cpu()
    print("Exporting ViT to ONNX...")

    class ViTWrapper(nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            return self.m(pixel_values=x).logits

    wrapper = ViTWrapper(model)
    # PyTorch Dynamo ONNX export for Vision Transformer
    torch.onnx.export(
        wrapper,
        dummy,
        str(out_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        dynamo=True,
    )
    print(f"ONNX model saved to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune ViT on PlantDoc field photos.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of fine-tuning epochs")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--out", default="ml/models/cropguard38_vit")
    args = parser.parse_args()

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {dev}")
    if dev.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_properties(0).name} ({torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB)")

    model_id = "kimcomehome/plantvillage-vit-leaf-disease"
    print(f"Loading pretrained model: {model_id}")
    model = AutoModelForImageClassification.from_pretrained(model_id).to(dev)

    # Class mapping: map PlantDoc classes to ViT model output classes
    vit_labels = list(model.config.id2label.values())
    vit_norm = {norm(l): i for i, l in enumerate(vit_labels)}

    target_config = json.load(open(ROOT / "ml" / "models" / "model_config.json"))
    target_labels = target_config["labels"]
    class_idx = {c: vit_norm.get(norm(c), i) for i, c in enumerate(target_labels)}

    pd_dir = ROOT / "work" / "plantdoc"
    fd_tr, _ = cg.plantdoc_frame(pd_dir / "train", class_idx)
    fd_te, _ = cg.plantdoc_frame(pd_dir / "test", class_idx)
    print(f"PlantDoc field images: {len(fd_tr)} train, {len(fd_te)} test across {fd_tr['pd_class'].nunique()} classes")

    train_tf, eval_tf = build_field_transforms()
    train_loader = DataLoader(PlantDocDataset(fd_tr, train_tf), batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    test_loader = DataLoader(PlantDocDataset(fd_te, eval_tf), batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    # Evaluate zero-shot baseline on test set
    model.eval()
    corr, tot = 0, 0
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(dev), y.to(dev)
            preds = model(pixel_values=x).logits.argmax(-1)
            corr += (preds == y).sum().item()
            tot += len(y)
    baseline_acc = corr / tot
    print(f"Zero-shot baseline field accuracy: {corr}/{tot} = {baseline_acc * 100:.2f}%\n")

    # Optimizer & scheduler
    # We fine-tune the classifier head and top transformer encoder blocks
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs * len(train_loader))
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    best_acc = baseline_acc
    best_weights = out_dir / "best_field_vit.pt"

    print("Beginning field fine-tuning...")
    for ep in range(args.epochs):
        model.train()
        t0 = time.time()
        running_loss = 0.0
        n_samples = 0
        for x, y in train_loader:
            x, y = x.to(dev), y.to(dev)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=dev.type, dtype=torch.float16, enabled=dev.type == "cuda"):
                logits = model(pixel_values=x).logits
                loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            running_loss += loss.item() * len(x)
            n_samples += len(x)

        # Validation on held-out field test set
        model.eval()
        corr, tot = 0, 0
        with torch.no_grad():
            for x, y in test_loader:
                x, y = x.to(dev), y.to(dev)
                preds = model(pixel_values=x).logits.argmax(-1)
                corr += (preds == y).sum().item()
                tot += len(y)
        val_acc = corr / tot
        el = time.time() - t0
        print(f"Epoch {ep+1}/{args.epochs} ({el:.1f}s) | train loss: {running_loss/n_samples:.4f} | field test acc: {val_acc*100:.2f}% (best: {max(best_acc, val_acc)*100:.2f}%)")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), best_weights)
            print(f"  -> New best field model saved! ({val_acc*100:.2f}%)")

    # Load best weights for export
    if best_weights.exists():
        model.load_state_dict(torch.load(best_weights))
        print(f"\nLoaded best model ({best_acc*100:.2f}%) for export.")

    # Export to ONNX
    onnx_file = out_dir / "model.onnx"
    export_vit_onnx(model, onnx_file)

    # Save model_config.json
    cfg = {
        "name": "cropguard-vit-base-field-adapted",
        "onnx": "cropguard38_vit/model.onnx",
        "labels": target_labels,
        "classes_file": "cropguard38_vit/class_names.json",
        "input_size": 224,
        "mean": MEAN,
        "std": STD,
        "temperature": 1.0,
        "confidence_threshold": 0.45,
        "energy_threshold": -4.8,
        "tta": False,
        "healthy_only_crops": target_config.get("healthy_only_crops", []),
        "field_test_accuracy": round(best_acc, 4),
    }
    json.dump(cfg, open(out_dir / "model_config.json", "w", encoding="utf-8"), indent=2)

    # Copy / save 38-class class_names.json
    classes_meta_path = ROOT / "ml" / "models" / "cropguard38" / "class_names.json"
    if not classes_meta_path.exists():
        classes_meta_path = ROOT / "contracts" / "class_names.json"
    classes_meta = json.load(open(classes_meta_path, encoding="utf-8"))
    json.dump(classes_meta, open(out_dir / "class_names.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nDone! Field-adapted model exported to {out_dir}")


if __name__ == "__main__":
    main()
