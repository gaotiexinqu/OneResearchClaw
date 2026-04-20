# CPath-Omni: A Unified Multimodal Foundation Model for Computational Pathology

**Source:** arXiv:2412.12077, 2024
**URL:** https://arxiv.org/abs/2412.12077
**Access date:** 2026-04-15

## Abstract

CPath-Omni is a 15-billion-parameter Large Multimodal Model (LMM) that unifies both patch-level and whole-slide image (WSI) analysis in computational pathology. It integrates diverse tasks including classification, visual question answering (VQA), captioning, and visual referring prompting. CPath-CLIP, its specialized pathology CLIP visual processor, achieves SOTA on 9 zero-shot and 4 few-shot datasets.

## Architecture

- **15B parameters:** Large-scale pathology LMM
- **Unified patch + WSI:** First model to integrate both levels
- **CPath-CLIP:** Pathology-specific CLIP with LLM text encoder
- **39 datasets, 42 tasks:** Classification, VQA, captioning, prompting

## Key Results

- SOTA on 39/42 datasets
- Outperforms task-specific models trained for individual tasks
- Zero-shot and few-shot capabilities through CLIP integration

## Relevance to Current Topic

CPath-Omni provides the broader context of large-scale multimodal foundation models in computational pathology. Its unified approach to patch + WSI analysis addresses the aggregation challenge noted in the biomarker prediction review. Its CLIP-based visual processor could serve as a feature extractor for HER2 prediction.

## Limitations

- 15B parameters = high computational cost
- CLIP-based approach may miss fine-grained biomarker details
- Not specifically validated for HER2 scoring
- WSI-level integration still requires effective aggregation strategies
