# Novel deep learning-based prediction of HER2 expression in breast cancer using multimodal MRI, nomogram, and decision curve analysis

**Source:** Frontiers in Oncology, 2025
**URL:** https://www.frontiersin.org/journals/oncology/articles/10.3389/fonc.2025.1593033/full
**Access date:** 2026-04-15

## Abstract

This study developed an automated framework for predicting HER2 expression in breast cancer by integrating multi-sequence breast MRI (T1, T2, DCE) with deep learning feature extraction and clinical data. Using ResNet50, VGG16, EfficientNet-B0, and ViT-Small, with ICC filtering and LASSO regression, the model achieved AUC of 0.94 on 2,400 patients from 4 centres. A nomogram integrating deep learning features with clinical variables demonstrated strong predictive accuracy.

## Methodology

1. **Dataset:** 6,438 patients screened, 2,400 included (1,286 HER2+, 1,114 HER2-) from 4 centres (2006-2024)
2. **MRI sequences:** T1, T2, and contrast-enhanced (DCE) at 3T
3. **Feature extraction:** ResNet50 (2048-dim), VGG16 (4096-dim), EfficientNet-B0 (1280-dim), ViT-Small (384-dim)
4. **Feature selection:** ICC filtering (≥0.9) + LASSO regression
5. **Classification:** Nomogram integrating deep scores + clinical features (lymph node status, enhancement curve, peritumoral edema, microcalcifications)

## Key Results

| Model | AUC |
|-------|-----|
| Individual models (best) | 0.88-0.89 |
| + Clinical data | **0.94** |

**Key clinical predictors identified:**
- Axillary lymph node involvement
- MRI enhancement curve (washout pattern)
- Peritumoral edema
- Microcalcifications

## Limitations

- HER2+ prevalence (53.6%) higher than general population (15-20%)
- No external validation reported
- Selection bias possible despite mitigation efforts
- Internal validation only (1000 bootstrap resamples)

## Relevance to Current Topic

This work demonstrates that deep learning on multi-sequence MRI can predict HER2 status with AUC=0.94, comparable to but independent from the H&E+IHC pathology approaches in the source documents. It provides cross-modal evidence that combining multiple imaging modalities improves HER2 prediction.
