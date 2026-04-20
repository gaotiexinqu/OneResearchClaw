# Deep Learning-Based Prediction of Molecular Tumor Biomarkers from H&E: A Practical Review

**Source:** Journal of Personalized Medicine, 2022 (PMC9784641)
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9784641/
**Access date:** 2026-04-15

## Abstract

Review of deep learning methods for predicting molecular biomarkers from H&E-stained histopathology whole slide images. Covers four types of biomarkers: (1) protein biomarkers, (2) genomic subtypes and expression, (3) molecular alterations, (4) virus presence. Reviews methodologies from bottom-up to pathologist-driven to hybrid approaches.

## Key Frameworks

1. **Bottom-up approaches:** Learn features directly from pixels using CNNs/Transformers pretrained on ImageNet
2. **Pathologist-driven approaches:** Use pathologist-annotated features
3. **Hybrid approaches:** Combine bottom-up and pathologist-driven
4. **Strongly supervised models:** When spatially-localized ground truth is available

## Tile Aggregation Methods

- Mean prediction / majority vote
- Second-stage classifier on tile statistics
- Quantile functions
- Attention-weighted pooling (DeepMIL)
- RNN on tile sequences

## Key Findings for HER2

1. **HER2 protein biomarker prediction** is a leading application area
2. La Barbera et al. used second-stage classifier on tile predictions for HER2 status
3. Self-supervised pretraining (fingerprinting) improved HER2 receptor prediction
4. Contrastive learning (cross-entropy + contrastive objectives) increases intra-class similarity

## Challenges

- Small training sets
- Weak supervision (patient-level labels only)
- WSI processing (100,000×100,000 pixels)
- Model explainability
- Cross-institution generalization

## Clinical Relevance

"Biomarker prediction models may yield a screening method to determine when to run molecular tests or an alternative when molecular tests are not possible."
