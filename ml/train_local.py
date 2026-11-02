"""Train CropGuard on YOUR NVIDIA GPU (built for a 6 GB laptop card such as the RTX 4050) with the dataset in data/disease_dataset.

Run from the project folder, with the virtual environment active:

    python ml/train_local.py --quick      # 5-10 minute smoke test (numbers are meaningless, it only proves everything works)
    python ml/train_local.py --bench      # measures speed, prints the time per epoch and the total, then stops
    python ml/train_local.py              # full training. If it is interrupted (sleep, power cut, Ctrl+C) run it again with:
    python ml/train_local.py --resume     # continues after the last finished epoch

Useful options: --backbone efficientnet_b0 (faster, lighter), --bs 16 (if you see "out of memory"), --epochs 4, --plantdoc (field-photo test).
At the end the model is written to ml/models/cropguard38/ and activated: just restart the server.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import ConcatDataset, DataLoader, Dataset

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cg_common as cg  # noqa: E402

warnings.filterwarnings("ignore", message=".*lr_scheduler.*")
warnings.filterwarnings("ignore", category=FutureWarning)
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


def log(*a):
    print(*a, flush=True)


def get_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/disease_dataset")
    ap.add_argument("--out", default="ml/models/cropguard38")
    ap.add_argument("--backbone", default="convnext_tiny.fb_in22k_ft_in1k")
    ap.add_argument("--epochs", type=int, default=6, help="fine-tuning epochs (after the short head-only phase)")
    ap.add_argument("--epochs-head", type=int, default=2)
    ap.add_argument("--bs", default="auto", help="batch size, or 'auto' = the biggest that fits in GPU memory")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--lr-head", type=float, default=1e-3)
    ap.add_argument("--img", type=int, default=224)
    ap.add_argument("--workers", type=int, default=-1, help="data loading processes (-1 = automatic)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--provided-split", action="store_true", help="use the dataset's own train/valid split (not recommended: it leaks)")
    ap.add_argument("--plantdoc", action="store_true", help="also test (and fine-tune) on real field photos from PlantDoc; needs git and internet")
    ap.add_argument("--no-pretrained", action="store_true", help="for tests only")
    ap.add_argument("--no-mixup", action="store_true")
    ap.add_argument("--no-activate", action="store_true")
    ap.add_argument("--target-precision", type=float, default=0.90)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args(argv)


# ----------------------------------------------------------------------------------------------- small helpers
def autocast(dev):
    return torch.autocast(device_type=dev.type, dtype=torch.float16, enabled=dev.type == "cuda")


def make_scaler(dev):
    try:
        return torch.amp.GradScaler("cuda", enabled=dev.type == "cuda")
    except (AttributeError, TypeError):
        return torch.cuda.amp.GradScaler(enabled=dev.type == "cuda")


class DS(Dataset):
    def __init__(self, frame, tf):
        self.p, self.y, self.tf = frame.path.tolist(), frame.y.tolist(), tf

    def __len__(self):
        return len(self.p)

    def __getitem__(self, i):
        return self.tf(Image.open(self.p[i]).convert("RGB")), self.y[i]


class RandomShadow(torch.nn.Module):
    """Simulate a shadow band cast across the leaf (field lighting condition)."""
    def __init__(self, p=0.3, alpha_range=(0.3, 0.6)):
        super().__init__()
        self.p = p
        self.alpha_range = alpha_range

    def forward(self, img):
        if torch.rand(1).item() > self.p:
            return img
        # img is a PIL Image at this point
        import random
        from PIL import ImageDraw
        w, h = img.size
        alpha = random.uniform(*self.alpha_range)
        overlay = Image.new("RGB", (w, h), (0, 0, 0))
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        # Random horizontal or diagonal band
        y0 = random.randint(0, h // 2)
        y1 = random.randint(h // 2, h)
        if random.random() < 0.5:
            # Horizontal band
            draw.rectangle([0, y0, w, y1], fill=int(255 * alpha))
        else:
            # Diagonal polygon
            skew = random.randint(-w // 3, w // 3)
            pts = [(0, y0), (w, y0 + skew), (w, y1 + skew), (0, y1)]
            draw.polygon(pts, fill=int(255 * alpha))
        return Image.composite(overlay, img, mask)

    def __repr__(self):
        return f"RandomShadow(p={self.p}, alpha_range={self.alpha_range})"


def make_transforms(img):
    train = T.Compose([
        cg.PadSquare(), cg.BGReplace(0.5),
        T.RandomResizedCrop(img, scale=(0.25, 1.0), ratio=(0.75, 1.33)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(0.2),
        T.RandomRotation(30),
        # Field lighting: stronger color and shadow augmentation
        T.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.5, hue=0.12),
        RandomShadow(p=0.3, alpha_range=(0.25, 0.55)),
        # Simulate overexposure / sun glare
        T.RandomApply([T.RandomSolarize(threshold=192)], p=0.15),
        # Simulate slight defocus / camera shake
        T.RandomApply([T.GaussianBlur(kernel_size=5, sigma=(0.1, 2.5))], p=0.35),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
        # Simulate partial obstruction (finger, debris, edge cropping)
        T.RandomErasing(p=0.25, scale=(0.02, 0.15), ratio=(0.3, 3.3), value=0),
    ])
    ev = T.Compose([cg.PadSquare(), T.Resize((img, img)), T.ToTensor(), T.Normalize(MEAN, STD)])
    return train, ev


def make_loader(frame, tf, shuffle, bs, workers):
    kw = dict(num_workers=workers, pin_memory=torch.cuda.is_available())
    if workers > 0:
        kw.update(persistent_workers=True, prefetch_factor=4)
    return DataLoader(DS(frame, tf), batch_size=bs, shuffle=shuffle, drop_last=shuffle, **kw)


@torch.no_grad()
def predict(model, dl, dev):
    model.eval()
    lg, ys = [], []
    for x, y in dl:
        x = x.to(dev, non_blocking=True).contiguous(memory_format=torch.channels_last)
        with autocast(dev):
            out = model(x)
        lg.append(out.float().cpu())
        ys.append(y)
    return torch.cat(lg), torch.cat(ys)


def pick_batch(model, img, nc, dev, requested):
    """Largest batch whose memory use stays below ~78 % of the GPU (the rest is headroom for the optimiser and the data)."""
    if requested != "auto":
        return max(2, int(requested) // 2 * 2)
    if dev.type != "cuda":
        return 16
    total = torch.cuda.get_device_properties(0).total_memory
    state = {k: v.clone() for k, v in model.state_dict().items()}       # the trial would otherwise disturb BatchNorm statistics
    model.train()
    chosen = 8
    for b in (64, 48, 32, 24, 16, 12, 8):
        try:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            x = torch.randn(b, 3, img, img, device=dev).contiguous(memory_format=torch.channels_last)
            y = torch.randint(0, nc, (b,), device=dev)
            with autocast(dev):
                loss = F.cross_entropy(model(x), y)
            loss.backward()
            torch.cuda.synchronize()
            peak = torch.cuda.max_memory_allocated()
            model.zero_grad(set_to_none=True)
            del x, y, loss
            if peak < 0.78 * total:
                chosen = b
                break
        except RuntimeError as e:
            if "out of memory" not in str(e).lower():
                raise
            model.zero_grad(set_to_none=True)
    torch.cuda.empty_cache()
    model.load_state_dict(state)
    return chosen


# ----------------------------------------------------------------------------------------------- data
def build_data(args, out):
    from sklearn.model_selection import StratifiedGroupKFold
    root = Path(args.data)
    tr_dir, va_dir = cg.find_split_dirs(root)
    if tr_dir is None:
        sys.exit(f"Could not find train/ and valid/ folders with class sub-folders under {root.resolve()}")
    log("train folder:", tr_dir, "\nvalid folder:", va_dir)
    df = pd.DataFrame(cg.scan(tr_dir, "train") + (cg.scan(va_dir, "valid") if va_dir else []), columns=["path", "raw", "orig_split"])
    if args.quick:
        df = df.sample(frac=1, random_state=args.seed).groupby("raw").head(40).reset_index(drop=True)
    raw_classes = sorted(df.raw.unique())
    class_idx = {c: i for i, c in enumerate(raw_classes)}
    df["y"] = df.raw.map(class_idx)
    df["crop"] = df.raw.map(lambda r: cg.parse_class(r)[0])
    classes, healthy_only = cg.build_meta(raw_classes)
    log(f"{len(df)} images | {len(raw_classes)} classes | {df.crop.nunique()} crops | healthy-only crops: {healthy_only or 'none'}")

    t0 = time.time()
    hashes = cg.compute_hashes(df.path, cache_file=None if args.quick else out / "_cache" / "hashes.npz", log=log)
    df["group"] = cg.group_ids(df.y.values, hashes)
    log(f"grouping done in {time.time()-t0:.0f}s: {df.group.nunique()} groups for {len(df)} images")
    leak = None
    if df.orig_split.nunique() > 1:
        sp = df.groupby("group").orig_split.agg(set)
        leaky = set(sp[sp.map(lambda s: len(s) > 1)].index)
        leak = float(100 * df[df.orig_split == "valid"].group.isin(leaky).mean())
        log(f">>> {leak:.1f}% of the dataset's own `valid` images have a near-duplicate (flip/rotation/brightness copy) in `train` (a lower bound).")
    if args.provided_split:
        tr, va = df[df.orig_split == "train"], df[df.orig_split == "valid"]
        te = va
    else:
        k = 5 if args.quick else 10
        folds = [i for _, i in StratifiedGroupKFold(k, shuffle=True, random_state=args.seed).split(df, df.y, df.group)]
        te, va, tr = df.iloc[folds[0]], df.iloc[folds[1]], df.iloc[np.concatenate(folds[2:])]
        assert not (set(tr.group) & set(te.group)) and not (set(tr.group) & set(va.group)), "group leak between splits"
    log(f"train {len(tr)} | val {len(va)} | test {len(te)}")
    return df, tr, va, te, class_idx, classes, healthy_only, leak


# ----------------------------------------------------------------------------------------------- training
def train_all(model, L_tr, L_va, args, dev, ckpt_dir, nc):
    from timm.data import Mixup
    from timm.loss import SoftTargetCrossEntropy
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    last, bestp = ckpt_dir / "last.pt", ckpt_dir / "best.pt"
    phases = [("head", args.epochs_head, args.lr_head, False), ("finetune", args.epochs, args.lr, not args.no_mixup)]
    total = sum(p[1] for p in phases)
    done, best_acc, saved = 0, -1.0, None
    if args.resume and last.exists():
        saved = torch.load(last, map_location="cpu")
        model.load_state_dict(saved["model"])
        done, best_acc = saved["done"], saved["best_acc"]
        log(f"Resuming after epoch {done}/{total}")
    elif last.exists():
        log("(an older checkpoint exists and is ignored; add --resume to continue it)")
    scaler = make_scaler(dev)
    pos = 0
    for name, n_ep, lr, use_mix in phases:
        if pos + n_ep <= done:
            pos += n_ep
            continue
        head = list(model.get_classifier().parameters())
        for p in model.parameters():
            p.requires_grad = name == "finetune"
        for p in head:
            p.requires_grad = True
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.05)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=max(1, n_ep * len(L_tr)))
        start = max(0, done - pos)
        if saved is not None and start > 0 and saved.get("phase") == name:
            opt.load_state_dict(saved["opt"])
            scaler.load_state_dict(saved["scaler"])
        for _ in range(start * len(L_tr)):
            sched.step()
        mix = Mixup(mixup_alpha=0.2, cutmix_alpha=1.0, prob=0.6, switch_prob=0.5, label_smoothing=0.1, num_classes=nc) if use_mix else None
        crit = SoftTargetCrossEntropy() if use_mix else nn.CrossEntropyLoss(label_smoothing=0.1)
        for ep in range(start, n_ep):
            model.train()
            t0, tl, n = time.time(), 0.0, 0
            for i, (x, y) in enumerate(L_tr, 1):
                x, y = x.to(dev, non_blocking=True), y.to(dev, non_blocking=True)
                if mix is not None:
                    x, y = mix(x, y)
                x = x.contiguous(memory_format=torch.channels_last)
                with autocast(dev):
                    loss = crit(model(x), y)
                opt.zero_grad(set_to_none=True)
                scaler.scale(loss).backward()
                scaler.unscale_(opt)
                nn.utils.clip_grad_norm_(model.parameters(), 2.0)
                scaler.step(opt)
                scaler.update()
                sched.step()
                tl += loss.item() * len(x)
                n += len(x)
                if i % 100 == 0 or i == len(L_tr):
                    el = time.time() - t0
                    log(f"  [{name}] epoch {pos+ep+1}/{total}  step {i}/{len(L_tr)}  loss {tl/n:.4f}  {n/el:.0f} img/s  eta {(len(L_tr)-i)*el/i/60:.1f} min")
            lg, ys = predict(model, L_va, dev)
            va_acc = (lg.argmax(1) == ys).float().mean().item()
            if va_acc > best_acc:
                best_acc = va_acc
                torch.save(model.state_dict(), bestp)
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "scaler": scaler.state_dict(), "done": pos + ep + 1,
                        "phase": name, "best_acc": best_acc}, last)
            log(f"[{name}] epoch {pos+ep+1}/{total} finished in {(time.time()-t0)/60:.1f} min | val accuracy {va_acc:.4f} | best {best_acc:.4f} | checkpoint saved")
        pos += n_ep
        saved = None
    if bestp.exists():
        model.load_state_dict(torch.load(bestp, map_location="cpu"))


def bench(model, L_tr, args, dev, nc):
    log("Benchmark: 25 training steps on real data ...")
    model.train()
    for p in model.parameters():
        p.requires_grad = True
    opt = torch.optim.AdamW(model.parameters(), lr=1e-5)
    scaler = make_scaler(dev)
    t0, imgs = None, 0
    for i, (x, y) in enumerate(L_tr):
        if i == 5:
            torch.cuda.synchronize() if dev.type == "cuda" else None
            t0 = time.time()
        x, y = x.to(dev).contiguous(memory_format=torch.channels_last), y.to(dev)
        with autocast(dev):
            loss = F.cross_entropy(model(x), y)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        if i >= 5:
            imgs += len(x)
        if i == 24:
            break
    torch.cuda.synchronize() if dev.type == "cuda" else None
    ips = imgs / (time.time() - t0)
    ep = len(L_tr) * L_tr.batch_size / ips / 60
    log(f"speed: {ips:.0f} images/s -> about {ep:.1f} min per epoch, about {ep * (args.epochs + args.epochs_head) / 60:.1f} hours for the full run "
        f"({args.epochs_head} head + {args.epochs} fine-tune epochs). If that is too long: --backbone efficientnet_b0 or --epochs 4.")
    if dev.type == "cuda":
        log(f"peak GPU memory: {torch.cuda.max_memory_allocated()/1e9:.1f} GB of {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")


# ----------------------------------------------------------------------------------------------- evaluation helpers
def ece(p, y, bins=15):
    conf, pred = p.max(1)
    acc = (pred == y).float()
    e, edges = 0.0, torch.linspace(0, 1, bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.float().mean().item() * abs(acc[m].mean().item() - conf[m].mean().item())
    return e


def fit_temperature(lg, y):
    t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([t], lr=0.1, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(lg / t.exp(), y)
        loss.backward()
        return loss
    opt.step(closure)
    return float(t.exp())


def pick_threshold(conf, ok, target):
    for t in np.round(np.arange(0.3, 0.96, 0.05), 2):
        m = conf >= t
        if m.sum() >= 20 and ok[m].mean() >= target:
            return float(t)
    return None


def metrics_of(lg, ys):
    from sklearn.metrics import accuracy_score, f1_score
    p, y = lg.argmax(1).numpy(), ys.numpy()
    return {"accuracy": float(accuracy_score(y, p)), "macro_f1": float(f1_score(y, p, average="macro")),
            "top3": float((lg.topk(3, 1).indices == ys[:, None]).any(1).float().mean())}


def export_onnx(model, img, path):
    kw = dict(input_names=["input"], output_names=["logits"], dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17)
    dummy = torch.randn(1, 3, img, img)
    try:
        torch.onnx.export(model, dummy, str(path), dynamo=False, **kw)
    except Exception:
        torch.onnx.export(model, dummy, str(path), **kw)


# ----------------------------------------------------------------------------------------------- main
def main(argv=None):
    args = get_args(argv)
    if args.quick:
        args.epochs, args.epochs_head = 1, 1
    try:
        import timm
    except ImportError:
        sys.exit("timm is missing. Run:  pip install timm scikit-learn pandas matplotlib onnx onnxruntime")
    import random
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if dev.type == "cuda":
        pr = torch.cuda.get_device_properties(0)
        log(f"GPU: {pr.name}, {pr.total_memory/1e9:.1f} GB")
        torch.backends.cudnn.benchmark = True
    else:
        log("WARNING: no CUDA GPU found: training on the CPU would take days. Check docs/TRAIN_ON_LAPTOP_RTX4050.md (PyTorch CUDA install).")
        if not (args.quick or args.bench):
            sys.exit("Stopping. Use --quick to test on the CPU anyway.")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df, tr, va, te, class_idx, classes, healthy_only, leak = build_data(args, out)
    nc = len(classes)

    model = timm.create_model(args.backbone, pretrained=not args.no_pretrained, num_classes=nc)
    model = model.to(dev, memory_format=torch.channels_last)
    log(f"{args.backbone}: {sum(p.numel() for p in model.parameters())/1e6:.1f} M parameters")
    bs = pick_batch(model, args.img, nc, dev, args.bs)
    workers = args.workers if args.workers >= 0 else (2 if args.quick else max(2, min(8, (os.cpu_count() or 4) - 2)))
    log(f"batch size {bs} | data workers {workers}")
    tf_train, tf_eval = make_transforms(args.img)
    L_tr = make_loader(tr, tf_train, True, bs, workers)
    L_va, L_te = make_loader(va, tf_eval, False, bs * 2, workers), make_loader(te, tf_eval, False, bs * 2, workers)
    if args.bench:
        bench(model, L_tr, args, dev, nc)
        return

    train_all(model, L_tr, L_va, args, dev, out / "_ckpt", nc)

    # ---- held-out test, calibration, gates ----
    lg_te, y_te = predict(model, L_te, dev)
    lab = metrics_of(lg_te, y_te)
    log("TEST (held-out, group-aware):", {k: round(v, 4) for k, v in lab.items()})
    pred, y = lg_te.argmax(1).numpy(), y_te.numpy()
    te_df = te.assign(ok=(pred == y))
    by_crop = te_df.groupby("crop").ok.mean().round(4).to_dict()
    log("test accuracy by crop:", by_crop)
    cmx = None
    try:
        from sklearn.metrics import confusion_matrix
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        cm = confusion_matrix(y, pred, labels=list(range(nc)), normalize="true")
        names = [c["id"].replace("___", " ")[:24] for c in classes]
        plt.figure(figsize=(11, 10))
        plt.imshow(cm, cmap="Greens")
        plt.xticks(range(nc), names, rotation=90, fontsize=6)
        plt.yticks(range(nc), names, fontsize=6)
        plt.title("Confusion matrix (row-normalised), test split")
        plt.tight_layout()
        plt.savefig(out / "confusion_matrix.png", dpi=150)
        plt.close()
        pairs = sorted(((cm[i, j], classes[i]["id"], classes[j]["id"]) for i in range(nc) for j in range(nc) if i != j and cm[i, j] > 0.02), reverse=True)[:8]
        cmx = [(round(float(a), 3), b, c) for a, b, c in pairs]
        log("most confused (share, true -> predicted):", *[f"\n   {a:.2f} {b} -> {c}" for a, b, c in cmx])
    except Exception as e:
        log("confusion matrix skipped:", e)

    lg_va, y_va = predict(model, L_va, dev)
    temp = fit_temperature(lg_va, y_va)
    pv = F.softmax(lg_va / temp, 1)
    cv_, pr_ = pv.max(1)
    thr = pick_threshold(cv_.numpy(), (pr_ == y_va).numpy(), args.target_precision)
    e_thr = float(np.percentile((-torch.logsumexp(lg_va, 1)).numpy(), 95))
    ece_b, ece_a = ece(F.softmax(lg_te, 1), y_te), ece(F.softmax(lg_te / temp, 1), y_te)
    log(f"temperature {temp:.3f} | ECE {ece_b:.4f} -> {ece_a:.4f} | confidence threshold {thr} | energy threshold {e_thr:.3f}")

    field_rows = []
    if args.plantdoc:
        if shutil.which("git") is None:
            log("git not found: skipping PlantDoc (install Git for Windows)")
        else:
            pd_dir = Path("work") / "plantdoc"
            if not pd_dir.exists():
                subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/pratikkayal/PlantDoc-Dataset", str(pd_dir)], check=True)
            fd_tr, sk1 = cg.plantdoc_frame(pd_dir / "train", class_idx)
            fd_te, sk2 = cg.plantdoc_frame(pd_dir / "test", class_idx)
            fd_val = fd_tr.sample(frac=0.2, random_state=args.seed)
            fd_tr = fd_tr.drop(fd_val.index)
            log(f"PlantDoc mapped: train {len(fd_tr)} | field-val {len(fd_val)} | field-test {len(fd_te)} | skipped folders: {sorted(set(sk1 + sk2))}")
            L_fte, L_fva = make_loader(fd_te, tf_eval, False, bs * 2, workers), make_loader(fd_val, tf_eval, False, bs * 2, workers)
            lg0, yf = predict(model, L_fte, dev)
            f0 = metrics_of(lg0, yf)
            log(f"LAB test accuracy {lab['accuracy']:.3f} -> FIELD test accuracy {f0['accuracy']:.3f} (gap {100*(lab['accuracy']-f0['accuracy']):.1f} points)")
            field_rows.append({"model": "lab-trained", "lab_acc": lab["accuracy"], "field_acc": f0["accuracy"]})
            replay = tr.sample(frac=1, random_state=args.seed).groupby("y").head(80)
            mix_ds = ConcatDataset([DS(fd_tr, tf_train)] * 3 + [DS(replay, tf_train)])
            L_mix = DataLoader(mix_ds, batch_size=bs, shuffle=True, num_workers=workers, pin_memory=dev.type == "cuda", drop_last=True)
            base_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            for p in model.parameters():
                p.requires_grad = True
            opt = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.05)
            scaler = make_scaler(dev)
            for ep in range(1 if args.quick else 4):
                model.train()
                for x, yb in L_mix:
                    x, yb = x.to(dev, non_blocking=True).contiguous(memory_format=torch.channels_last), yb.to(dev, non_blocking=True)
                    with autocast(dev):
                        loss = F.cross_entropy(model(x), yb, label_smoothing=0.1)
                    opt.zero_grad(set_to_none=True)
                    scaler.scale(loss).backward()
                    scaler.step(opt)
                    scaler.update()
                log(f"  field fine-tune epoch {ep+1} done")
            lg1, _ = predict(model, L_fte, dev)
            f1m = metrics_of(lg1, yf)
            lab2 = metrics_of(predict(model, L_te, dev)[0], y_te)
            field_rows.append({"model": "+ field fine-tune", "lab_acc": lab2["accuracy"], "field_acc": f1m["accuracy"]})
            log("lab vs field:", field_rows)
            lgv_new, yv_ = predict(model, L_fva, dev)
            acc_new = (lgv_new.argmax(1) == yv_).float().mean().item()
            ft_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            model.load_state_dict(base_state)
            acc_old = (predict(model, L_fva, dev)[0].argmax(1) == yv_).float().mean().item()
            if acc_new >= acc_old:                                   # chosen on field-val, never on the test split
                model.load_state_dict(ft_state)
                log("using the field fine-tuned model (better on field-val)")
            lgv, yv_ = predict(model, L_fva, dev)
            temp = fit_temperature(lgv, yv_)
            pf = F.softmax(lgv / temp, 1)
            cf_, prf = pf.max(1)
            thr = pick_threshold(cf_.numpy(), (prf == yv_).numpy(), args.target_precision) or thr
            e_thr = float(np.percentile((-torch.logsumexp(lgv, 1)).numpy(), 95))
            log(f"final temperature {temp:.3f} | threshold {thr} | energy threshold {e_thr:.3f}")

    # ---- export ----
    model.eval().cpu()
    export_onnx(model, args.img, out / "model.onnx")
    import onnx
    import onnxruntime as ort
    onnx.checker.check_model(onnx.load(str(out / "model.onnx")))
    sess = ort.InferenceSession(str(out / "model.onnx"), providers=["CPUExecutionProvider"])
    xb = torch.randn(2, 3, args.img, args.img)
    with torch.no_grad():
        ref = model(xb).numpy()
    log("max |torch - onnx| =", float(np.abs(ref - sess.run(None, {"input": xb.numpy()})[0]).max()))
    cfg = {"name": f"cropguard-{args.backbone.split('.')[0]}-{nc}class", "onnx": "model.onnx", "labels": [c["id"] for c in classes],
           "classes_file": "class_names.json", "input_size": args.img, "mean": MEAN, "std": STD, "temperature": temp,
           "confidence_threshold": thr if thr is not None else 0.6, "energy_threshold": e_thr, "tta": True, "healthy_only_crops": healthy_only}
    json.dump(cfg, open(out / "model_config.json", "w", encoding="utf-8"), indent=2)
    json.dump({"version": 3, "input_size": args.img, "mean": MEAN, "std": STD, "classes": classes}, open(out / "class_names.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    summary = {"backbone": args.backbone, "classes": nc, "crops": int(df.crop.nunique()), "images": len(df),
               "split": "dataset-provided" if args.provided_split else "group-aware", "dataset_valid_leak_pct": leak, "test": lab,
               "test_accuracy_by_crop": by_crop, "most_confused": cmx, "ece_before": ece_b, "ece_after": ece_a, "temperature": temp,
               "confidence_threshold": thr, "energy_threshold": e_thr, "healthy_only_crops": healthy_only, "lab_vs_field": field_rows,
               "quick_run": args.quick, "seed": args.seed}
    json.dump(summary, open(out / "metrics.json", "w", encoding="utf-8"), indent=2, default=float)
    (out / "MODEL_CARD.md").write_text(
        f"# CropGuard model card (auto-generated)\n* Backbone {args.backbone} | {nc} classes | {df.crop.nunique()} crops\n"
        f"* Split: {summary['split']}; leak of the dataset's own valid folder: {leak} %\n"
        f"* Test: accuracy {lab['accuracy']:.4f}, macro-F1 {lab['macro_f1']:.4f}, top-3 {lab['top3']:.4f}\n"
        f"* Calibration: temperature {temp:.3f}, ECE {ece_b:.4f} -> {ece_a:.4f}; confidence threshold {thr}\n"
        f"* Field (PlantDoc): {field_rows or 'not run'}\n* Crops with only healthy images: {healthy_only}\n"
        f"* Limits: lab-style training photos, {df.crop.nunique()} crops, severity not predicted by this model.\n"
        + ("* THIS WAS A --quick SMOKE TEST: numbers are meaningless.\n" if args.quick else ""), encoding="utf-8")
    log(f"\nSaved to {out.resolve()}")
    if not args.no_activate and out.parent.name == "models":
        from switch_model import activate
        activate(out.parent, out.name)
        log(f"Activated '{out.name}'. Now restart the server:  python -m uvicorn backend.app.main:app --port 8000")
    else:
        log(f"Activate it with:  python ml/switch_model.py {out.name}")


if __name__ == "__main__":
    main()
