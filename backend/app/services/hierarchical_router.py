"""Two-Stage Hierarchical Routing Service.

Stage 1: Taxonomic Crop Router (BioCLIP ViT zero-shot embeddings over 45 crops)
Stage 2: Pathogen / Disease Classifier (Fine-tuned ViT-Base-Patch16-224)

Performs hierarchical crop-conditioned inference:
1. Validates that the detected crop passes the required confidence threshold.
2. If the crop is unsupported by CropGuard, triggers an early safe rejection.
3. If the crop is supported, restricts disease hypotheses to that host species
   and renormalizes conditional probabilities, eliminating cross-crop hallucinations.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


class HierarchicalRouter:
    def __init__(self, default_threshold: float = 0.5):
        self.default_threshold = default_threshold

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.lower().replace(" ", "").replace("_", "").replace("-", "")

    def route(
        self,
        disease_probs: Dict[str, float],
        crop_result: Optional[Dict[str, Any]],
        by_id: Dict[str, Any],
        supported_crops: List[str],
        crop_threshold: float = 0.5,
        soft_fallback: bool = False,
        fusion_weight: float = 0.15,
    ) -> Dict[str, Any]:
        """Hierarchical crop-conditioned routing.

        Stage 1: Validates crop species and threshold.
        Stage 2: Conditions disease hypothesis space to the confirmed crop
                 or performs soft Bayesian fusion when soft_fallback=True.
        """
        if not crop_result or not crop_result.get("probs"):
            order = sorted(disease_probs.items(), key=lambda kv: -kv[1])
            return {
                "probs": disease_probs,
                "top3": [(c, p) for c, p in order[:3]],
                "class_id": order[0][0] if order else None,
                "confidence": order[0][1] if order else 0.0,
                "routing_mode": "flat_fallback",
                "species_agreement": 1.0,
                "is_unsupported_crop": False,
            }

        top_crop_name = crop_result.get("name", "Unknown")
        top_crop_prob = float(crop_result.get("p", 0.0))
        thr = float(crop_result.get("threshold", crop_threshold))
        norm_supported = {self._normalize_name(c): c for c in supported_crops}
        norm_top_crop = self._normalize_name(top_crop_name)
        is_supported = norm_top_crop in norm_supported

        # ---- Soft Bayesian Evidence Fusion Mode ----
        if soft_fallback:
            # Marginal ViT probability mass per crop species
            vit_crop_mass: Dict[str, float] = {}
            for cid, p in disease_probs.items():
                c_name = by_id.get(cid, {}).get("crop", {}).get("en", "")
                nc = self._normalize_name(c_name)
                vit_crop_mass[nc] = vit_crop_mass.get(nc, 0.0) + p
            best_vit_norm_crop = max(vit_crop_mass, key=vit_crop_mass.get) if vit_crop_mass else ""
            best_vit_mass = vit_crop_mass.get(best_vit_norm_crop, 0.0)

            # True rejection 1: BioCLIP strongly flags unsupported crop AND ViT is uncertain
            if not is_supported and top_crop_prob >= thr and best_vit_mass < 0.40:
                return {
                    "probs": disease_probs,
                    "top3": sorted(disease_probs.items(), key=lambda kv: -kv[1])[:3],
                    "class_id": None,
                    "confidence": 0.0,
                    "routing_mode": "unsupported_crop_rejection",
                    "species_agreement": 0.0,
                    "is_unsupported_crop": True,
                    "rejected_crop": top_crop_name,
                    "crop_prob": top_crop_prob,
                }

            # True rejection 2: Both BioCLIP and ViT are low-confidence
            if top_crop_prob < 0.30 and best_vit_mass < 0.40:
                return {
                    "probs": disease_probs,
                    "top3": sorted(disease_probs.items(), key=lambda kv: -kv[1])[:3],
                    "class_id": None,
                    "confidence": 0.0,
                    "routing_mode": "low_crop_confidence_rejection",
                    "species_agreement": 0.0,
                    "is_unsupported_crop": True,
                    "rejected_crop": top_crop_name,
                    "crop_prob": top_crop_prob,
                }

            # If strong agreement on a supported crop with high BioCLIP confidence:
            if is_supported and norm_top_crop == best_vit_norm_crop and top_crop_prob >= thr:
                target_supported_name = norm_supported[norm_top_crop]
                keep = {
                    c: p
                    for c, p in disease_probs.items()
                    if self._normalize_name(by_id.get(c, {}).get("crop", {}).get("en", ""))
                    == norm_top_crop
                }
                if keep and sum(keep.values()) > 0:
                    z = sum(keep.values())
                    fused_probs = {c: p / z for c, p in keep.items()}
                    sorted_fused = sorted(fused_probs.items(), key=lambda kv: -kv[1])
                    top_cid, top_p = sorted_fused[0]
                    return {
                        "probs": fused_probs,
                        "top3": [(c, float(p)) for c, p in sorted_fused[:3]],
                        "class_id": top_cid,
                        "confidence": float(top_p),
                        "routing_mode": "hierarchical_crop_conditioned",
                        "species_agreement": 1.0,
                        "is_unsupported_crop": False,
                        "detected_crop": target_supported_name,
                        "crop_confidence": top_crop_prob,
                    }

            # Soft Bayesian Evidence Fusion (weight crop prior)
            crop_probs = crop_result.get("probs", {})
            fused_probs = {}
            for cid, p in disease_probs.items():
                c_name = by_id.get(cid, {}).get("crop", {}).get("en", "")
                norm_c = self._normalize_name(c_name)
                cp = 0.05
                for bio_name, bp in crop_probs.items():
                    if self._normalize_name(bio_name) == norm_c:
                        cp = max(cp, float(bp))
                        break
                fused_probs[cid] = p * (cp ** fusion_weight)

            z = sum(fused_probs.values())
            fused_probs = {c: p / z for c, p in fused_probs.items()}
            order = sorted(fused_probs.items(), key=lambda kv: -kv[1])
            top_cid, top_p = order[0]
            chosen_crop = by_id.get(top_cid, {}).get("crop", {}).get("en", "")
            agreement = 1.0 if self._normalize_name(chosen_crop) == norm_top_crop else 0.5
            return {
                "probs": fused_probs,
                "top3": [(c, float(p)) for c, p in order[:3]],
                "class_id": top_cid,
                "confidence": float(top_p),
                "routing_mode": "hierarchical_crop_conditioned" if agreement == 1.0 else "bayesian_fusion_fallback",
                "species_agreement": agreement,
                "is_unsupported_crop": False,
                "detected_crop": chosen_crop,
                "crop_confidence": top_crop_prob,
            }

        # ---- Strict Legacy Mode (Default) ----

        # Threshold check: below threshold -> unsupported_crop
        if top_crop_prob < thr:
            return {
                "probs": disease_probs,
                "top3": sorted(disease_probs.items(), key=lambda kv: -kv[1])[:3],
                "class_id": None,
                "confidence": 0.0,
                "routing_mode": "low_crop_confidence_rejection",
                "species_agreement": 0.0,
                "is_unsupported_crop": True,
                "rejected_crop": top_crop_name,
                "crop_prob": top_crop_prob,
            }

        # Check if crop is supported
        if norm_top_crop not in norm_supported:
            return {
                "probs": disease_probs,
                "top3": sorted(disease_probs.items(), key=lambda kv: -kv[1])[:3],
                "class_id": None,
                "confidence": 0.0,
                "routing_mode": "unsupported_crop_rejection",
                "species_agreement": 0.0,
                "is_unsupported_crop": True,
                "rejected_crop": top_crop_name,
                "crop_prob": top_crop_prob,
            }

        # Restrict disease candidates to the detected crop
        target_supported_name = norm_supported[norm_top_crop]
        keep = {
            c: p
            for c, p in disease_probs.items()
            if self._normalize_name(by_id.get(c, {}).get("crop", {}).get("en", ""))
            == norm_top_crop
        }

        if not keep or sum(keep.values()) <= 0:
            return {
                "probs": disease_probs,
                "top3": sorted(disease_probs.items(), key=lambda kv: -kv[1])[:3],
                "class_id": None,
                "confidence": 0.0,
                "routing_mode": "no_diseases_for_crop_rejection",
                "species_agreement": 0.0,
                "is_unsupported_crop": True,
                "rejected_crop": top_crop_name,
                "crop_prob": top_crop_prob,
            }

        z = sum(keep.values())
        fused_probs = {c: p / z for c, p in keep.items()}
        sorted_fused = sorted(fused_probs.items(), key=lambda kv: -kv[1])
        top_cid, top_p = sorted_fused[0]

        return {
            "probs": fused_probs,
            "top3": [(c, float(p)) for c, p in sorted_fused[:3]],
            "class_id": top_cid,
            "confidence": float(top_p),
            "routing_mode": "hierarchical_crop_conditioned",
            "species_agreement": 1.0,
            "is_unsupported_crop": False,
            "detected_crop": target_supported_name,
            "crop_confidence": top_crop_prob,
        }
