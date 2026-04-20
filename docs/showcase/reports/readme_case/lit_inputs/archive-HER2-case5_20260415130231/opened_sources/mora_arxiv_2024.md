# MoRA: LoRA Guided Multi-Modal Disease Diagnosis with Missing Modality

**Source:** arXiv:2408.09064
**URL:** https://arxiv.org/html/2408.09064
**Access date:** 2026-04-15

## Abstract

MoRA (Modality-aware Low-Rank Adaptation) projects each input to a low intrinsic dimension but uses different modality-aware up-projections for modality-specific adaptation when modalities are missing. It requires less than 1.6% of trainable parameters compared to full model training while outperforming existing methods on disease diagnosis tasks with missing modalities.

## Core Mechanism

Based on Low-Rank Adaptation (LoRA):
- Freeze pre-trained multi-modal model weights
- Inject trainable rank decomposition matrices: W = W₀ + BA
- Modality-aware up-projections for each modality

## Key Advantages

1. **Parameter efficiency:** Only 1.6% of parameters vs full fine-tuning
2. **Robustness to missing modalities:** Different up-projections for different missing scenarios
3. **Plug-and-play:** Integrates into first block of pre-trained model

## Relevance to Current Topic

MoRA provides an alternative parameter-efficient approach to missing modality handling in multi-modal medical imaging, complementing both ShaSpec (feature-level) and CM-GAN (generation-level) approaches in the input documents.

## Code Available

https://github.com/zhiyiscs/MoRA

## Limitations

- Designed for fine-tuning pre-trained models; not applicable from scratch
- Evaluated on general medical image datasets; pathology-specific validation absent
- Two-modality assumption in problem formulation
