# Multi-modal Learning with Missing Modality via Shared-Specific Feature Modelling (ShaSpec)

**Source:** CVPR 2023, arXiv:2307.14126
**URL:** https://arxiv.org/abs/2307.14126
**Access date:** 2026-04-15

## Abstract

ShaSpec addresses the missing modality issue in multi-modal learning by learning both shared features (modality-agnostic) and specific features (modality-specific) through two auxiliary tasks: domain classification (DCO) and distribution alignment (DAO/MMD). It uses a residual feature fusion procedure and supports both dedicated and non-dedicated training. ShaSpec applies to both classification and segmentation tasks.

## Architecture

- **Shared Encoder:** Captures modality-invariant features across all modalities
- **Specific Encoders:** N modality-specific encoders (one per modality)
- **Residual Fusion:** f = r + proj([s₁; s₂; ...; sₙ]) where r = shared features
- **Auxiliary Tasks:** DCO on specific features, DAO/MMD on shared features

## Key Loss Functions

1. **DCO (Domain Classification Objective):** Binary cross-entropy forcing specific features to be modality-discriminative
2. **DAO (Distribution Alignment Objective):** MMD/KL/CE loss enforcing shared feature modality-invariance
3. **Main Task Loss:** Cross-entropy (classification) or Dice loss (segmentation)

## Results

### BraTS2018 Non-Dedicated Training (Dice Score)

| Modality Combo | Best Competitor | ShaSpec | ShaSpec* |
|---------------|-----------------|---------|----------|
| Avg ET | 59.85 | 61.58 | 63.08 |
| Avg TC | 72.97 | 77.45 | 77.88 |
| Avg WT | 85.92 | 85.92 | 86.26 |

**Improvement over second-best:** +3.23% (ET), +4.91% (TC), +3.32% (WT)

### Audiovision-MNIST (Classification Accuracy)

| Audio Rate | SMIL | ShaSpec |
|------------|------|---------|
| 5% | 92.89% | **93.33%** |
| 20% | 94.44% | **94.67%** |

## Relevance to Current Topic

This paper provides the algorithmic foundation for the shared-specific feature modeling used in the HER2 prediction framework's dual-encoder architecture. The DCO and DAO loss functions are directly referenced and applied in the input documents.

## Limitations

- DCO/DAO hyperparameters (α=0.1, β=0.02) tuned on BraTS; generalization uncertain
- Missing modality feature generation is simple averaging of available modalities
- Evaluated primarily on brain imaging and toy dataset; pathology domain untested
- No end-to-end training with generative models
