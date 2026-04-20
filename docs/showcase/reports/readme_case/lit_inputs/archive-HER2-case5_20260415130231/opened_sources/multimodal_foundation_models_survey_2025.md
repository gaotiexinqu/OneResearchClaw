# Multi-Modal Foundation Models for Computational Pathology: A Survey

**Source:** arXiv:2503.09091, 2025
**URL:** https://arxiv.org/abs/2503.09091
**Access date:** 2026-04-15

## Abstract

Comprehensive survey of 32 multi-modal foundation models in computational pathology, categorizing them into three paradigms: (1) vision-language, (2) vision-knowledge graph, (3) vision-gene expression. Analyzes 28 multi-modal datasets and identifies key challenges and future directions.

## Taxonomy

1. **Vision-Language Models:** Integrate text/reports with histopathology images
   - Non-LLM-based (CLIP-style)
   - LLM-based (GPT-style)
2. **Vision-Knowledge Graph:** Integrate structured domain knowledge
3. **Vision-Gene Expression:** Integrate molecular profiles (RNA, genomics)

## Key Findings

1. **Trend:** Early foundation models were uni-modal; recent models increasingly multi-modal
2. **Training:** Most models use ImageNet pretrained backbones + pathology-specific pretraining
3. **Datasets:** 28 multi-modal datasets available (image-text, instruction, image-other modality)
4. **Tasks:** Classification, VQA, captioning, segmentation, retrieval

## Key Challenges

- Data heterogeneity (WSI scale vs text scale)
- Annotation cost and quality
- Cross-modal alignment (different modalities have different granularity)
- Domain shift across institutions
- Interpretability and clinical validation

## Relevance to Current Topic

This survey provides the broader landscape for understanding where the HER2 prediction framework fits in the field - it falls primarily into the vision-gene expression paradigm (H&E+IHC+RNA), with elements of vision-language (clinical reports). The survey identifies key challenges that directly affect clinical deployment.
