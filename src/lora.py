"""Low-Rank Adaptation (LoRA) for Vision Transformers (DINOv2).

Implements parameter-efficient fine-tuning on the last few transformer blocks of DINOv2
for 6-8 GB VRAM GPUs (e.g. RTX 4050).

Scientific constraints from published research:
1. LoRA must be trained on the full mixed dataset, NEVER lab-only.
2. Keep LoRA ONLY if leave-one-dataset-out (LODO) cross-domain score improves over
   the frozen baseline, since LoRA's benefit was small and statistically inconclusive
   in prior research (bioengineer.org/frozen-ai-features-enable-robust-plant-disease-detection-from-lab-to-field).
3. Zero inference overhead: weights can be folded directly into original layers via merge().
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from PIL import Image

logger = logging.getLogger("cropguard.lora")


class LoRALinear(nn.Module):
    """Low-Rank Adapter wrapping an existing nn.Linear layer.

    Computes: W_eff * x = (W_orig + (alpha / rank) * B @ A) * x
    Initialized with B = 0 and A ~ N(0, 1/rank), guaranteeing exact identity to the
    frozen linear layer at initialization (step 0).
    """

    def __init__(
        self,
        original_linear: nn.Linear,
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.05,
    ):
        super().__init__()
        self.original_linear = original_linear
        self.in_features = original_linear.in_features
        self.out_features = original_linear.out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank if rank > 0 else 1.0

        # Freeze original linear layer
        self.original_linear.weight.requires_grad = False
        if self.original_linear.bias is not None:
            self.original_linear.bias.requires_grad = False

        if rank > 0:
            self.lora_dropout = nn.Dropout(p=dropout) if dropout > 0.0 else nn.Identity()
            # A: [rank, in_features]
            self.lora_A = nn.Parameter(torch.empty(rank, self.in_features))
            # B: [out_features, rank]
            self.lora_B = nn.Parameter(torch.zeros(self.out_features, rank))
            self.reset_parameters()
        else:
            self.lora_A = None
            self.lora_B = None

        self.merged = False

    def reset_parameters(self):
        """Initialize A with Kaiming uniform / standard normal and B with zeros."""
        if self.rank > 0:
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.merged or self.rank == 0:
            return self.original_linear(x)

        base_out = self.original_linear(x)
        # Low-rank delta: x @ A^T @ B^T * scaling
        dropped = self.lora_dropout(x)
        lora_out = (dropped @ self.lora_A.t()) @ self.lora_B.t() * self.scaling
        return base_out + lora_out

    def merge(self):
        """Merge LoRA weights directly into the original linear weights for zero-overhead inference."""
        if self.merged or self.rank == 0:
            return
        delta = (self.lora_B @ self.lora_A) * self.scaling
        self.original_linear.weight.data += delta.to(self.original_linear.weight.device)
        self.merged = True
        logger.debug("LoRALinear weights merged into base weights.")

    def unmerge(self):
        """Revert merged weights back to original base weights."""
        if not self.merged or self.rank == 0:
            return
        delta = (self.lora_B @ self.lora_A) * self.scaling
        self.original_linear.weight.data -= delta.to(self.original_linear.weight.device)
        self.merged = False
        logger.debug("LoRALinear weights unmerged.")


def apply_lora_to_dinov2(
    model: nn.Module,
    last_n_blocks: int = 2,
    rank: int = 8,
    alpha: float = 16.0,
    dropout: float = 0.05,
    target_modules: Sequence[str] = ("q_proj", "v_proj", "query", "value"),
) -> Tuple[nn.Module, List[nn.Parameter]]:
    """Freeze the full DINOv2 model and inject LoRALinear into the query and value projections
    of the last `last_n_blocks` transformer blocks.

    Compatible with:
    - HuggingFace Transformers (facebook/dinov2-large, facebook/dinov2-base)
    - Torch.hub DINOv2
    - Timm ViT

    Returns:
        (model, list_of_trainable_lora_parameters)
    """
    # 1. Freeze all base parameters
    for param in model.parameters():
        param.requires_grad = False

    # 2. Locate transformer blocks
    blocks = None
    if hasattr(model, "encoder") and hasattr(model.encoder, "layer"):
        # HuggingFace Dinov2Model / AutoModel
        blocks = model.encoder.layer
    elif hasattr(model, "blocks"):
        # timm / torch.hub
        blocks = model.blocks
    elif hasattr(model, "layers"):
        blocks = model.layers

    if blocks is None:
        raise ValueError("Could not locate transformer blocks in model architecture.")

    num_total_blocks = len(blocks)
    start_block_idx = max(0, num_total_blocks - last_n_blocks)
    target_blocks = list(blocks)[start_block_idx:]

    lora_params: List[nn.Parameter] = []
    injected_count = 0

    for b_idx, block in enumerate(target_blocks, start=start_block_idx):
        # Look for attention modules
        attn_module = None
        if hasattr(block, "attention"):
            attn_module = block.attention
        elif hasattr(block, "attn"):
            attn_module = block.attn

        if attn_module is None:
            continue

        # Look for target projection layers inside attention module
        for name, child in list(attn_module.named_children()):
            if any(t in name.lower() for t in target_modules) and isinstance(child, nn.Linear):
                lora_layer = LoRALinear(child, rank=rank, alpha=alpha, dropout=dropout)
                setattr(attn_module, name, lora_layer)
                if lora_layer.lora_A is not None:
                    lora_params.extend([lora_layer.lora_A, lora_layer.lora_B])
                    injected_count += 1
            elif hasattr(child, "named_children"):
                for sub_name, sub_child in list(child.named_children()):
                    if any(t in sub_name.lower() for t in target_modules) and isinstance(sub_child, nn.Linear):
                        lora_layer = LoRALinear(sub_child, rank=rank, alpha=alpha, dropout=dropout)
                        setattr(child, sub_name, lora_layer)
                        if lora_layer.lora_A is not None:
                            lora_params.extend([lora_layer.lora_A, lora_layer.lora_B])
                            injected_count += 1

    total_lora_trainable = sum(p.numel() for p in lora_params)
    logger.info(
        f"Applied LoRA (rank={rank}, alpha={alpha}) to last {last_n_blocks}/{num_total_blocks} blocks. "
        f"Injected into {injected_count} linear projections. "
        f"Total trainable parameters: {total_lora_trainable:,} (~{total_lora_trainable * 4 / 1024:.1f} KB)."
    )

    return model, lora_params


def merge_lora_weights(model: nn.Module) -> None:
    """Traverse model and merge all LoRALinear layers into base weights."""
    merged_count = 0
    for module in model.modules():
        if isinstance(module, LoRALinear):
            module.merge()
            merged_count += 1
    logger.info(f"Successfully merged {merged_count} LoRA modules into base weights.")


class MixedDatasetImageLoader(Dataset):
    """PyTorch Dataset loading images from full mixed dataset for LoRA adaptation."""

    def __init__(self, samples_df, transform):
        self.samples = samples_df.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, str]:
        row = self.samples.iloc[idx]
        img_path = Path(row["image_path"])
        with Image.open(img_path) as img:
            t = self.transform(img.convert("RGB"))
        return t, row.get("canonical_key", "unknown")


class LoRABenchmarkEngine:
    """Manages training and statistical benchmarking of LoRA vs frozen DINOv2 baseline.

    Mandate: Only keep LoRA if leave-one-dataset-out (LODO) cross-domain score strictly improves.
    """

    @staticmethod
    def evaluate_decision_rule(
        frozen_lodo_score: float,
        lora_lodo_score: float,
        min_delta: float = 0.005,
    ) -> Dict[str, Any]:
        """Evaluate whether LoRA provides a statistically meaningful improvement.

        Rule: Keep LoRA ONLY if lora_score >= frozen_score + min_delta.
        Otherwise retain the frozen baseline to prevent lab-overfitting.
        """
        diff = float(lora_lodo_score - frozen_lodo_score)
        accepted = diff >= min_delta

        verdict = "ACCEPTED" if accepted else "REJECTED (Retain Frozen Baseline)"
        reason = (
            f"LoRA LODO score ({lora_lodo_score:.4f}) exceeded frozen baseline ({frozen_lodo_score:.4f}) by {diff:+.4f} (>= {min_delta:.3f})."
            if accepted
            else f"LoRA LODO score ({lora_lodo_score:.4f}) did not achieve required +{min_delta:.1%} improvement over frozen baseline ({frozen_lodo_score:.4f}). Research finding confirmed: frozen features generalize better."
        )

        decision = {
            "verdict": verdict,
            "accepted": accepted,
            "frozen_lodo_score": frozen_lodo_score,
            "lora_lodo_score": lora_lodo_score,
            "score_delta": diff,
            "min_delta_required": min_delta,
            "reason": reason,
        }
        logger.info(f"LoRA Decision: {verdict} - {reason}")
        return decision
