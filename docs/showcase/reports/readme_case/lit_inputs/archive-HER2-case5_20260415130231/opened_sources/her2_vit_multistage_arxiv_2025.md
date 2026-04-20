# Feature Learning with Multi-Stage Vision Transformers on Inter-Modality HER2 Status Scoring

**Source:** arXiv:2512.22335, 2025
**URL:** https://arxiv.org/abs/2512.22335
**Access date:** 2026-04-15

## Abstract

A single end-to-end pipeline using multi-stage vision transformers for simultaneous H&E and IHC analysis on whole slide images, achieving 0.94 classification accuracy and 0.933 specificity for 4-way HER2 scoring (0, 1+, 2+, 3+). Includes tumor localization, H&E→IHC region mapping, and pixel-level HER2 annotation.

## Key Features

1. **Patch-wise H&E processing** for tumor localization
2. **Novel mapping function** to identify corresponding IHC regions from H&E malignant areas
3. **Clinically inspired HER2 scoring** embedded in pipeline
4. **Automatic pixel-level annotation** of 4-way HER2 scoring

## Results

- Classification accuracy: **0.94** (4-way HER2: 0, 1+, 2+, 3+)
- Specificity: **0.933**
- Tumor localization accuracy: good
- Joint H&E+IHC evaluation comparable to human pathologists

## Dataset

- Privately curated from 13 different WSI cases of paired H&E and IHC

## Relevance to Current Topic

Directly relevant to the HER2 prediction framework - this paper demonstrates that joint H&E+IHC ViT analysis achieves 94% accuracy in 4-way HER2 scoring, which is comparable to the HER2 MAP model's performance and represents an alternative architecture approach.

## Limitations

- Small dataset (13 cases); generalizability uncertain
- Private dataset; reproducibility limited
- End-to-end approach may lack interpretability
