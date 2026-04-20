# AIDA: Adversarial Fourier-based Domain Adaptation for Multi-Center Histopathology

**Source:** npj Precision Oncology, 2024
**URL:** https://www.nature.com/articles/s41698-024-00652-4
**Access date:** 2026-04-15

## Abstract

AIDA addresses domain shift in multi-center histopathology by combining adversarial training with an FFT-Enhancer module that makes CNNs less sensitive to amplitude spectrum variations (color/staining) and more attentive to phase-related components (shape/morphology). Evaluated on ovarian, pleural, bladder, and breast cancer datasets from multiple centers.

## Key Innovation

- **FFT-Enhancer module:** Processes images in frequency domain; adjusts source domain colors to look like target domain
- **Adversarial domain adaptation:** Domain classifier + label predictor
- **Frequency domain insight:** CNNs are sensitive to amplitude spectrum; humans rely on phase-related components for object recognition
- **VLAD aggregation:** Patch-level features aggregated to slide-level using Vector of Locally Aggregated Descriptors

## Results

### Balanced Accuracy on Target Domain

| Dataset | Ovarian | Pleural | Bladder | Breast |
|---------|---------|---------|---------|--------|
| Base | 64.65% | 76.70% | 54.77% | 55.15% |
| HED Aug | 67.07% | 76.80% | 57.66% | 57.57% |
| Macenko | 73.49% | 80.96% | 66.42% | 58.91% |
| CNorm | 72.14% | 79.55% | 73.73% | 65.06% |
| ADA | 74.16% | 79.72% | 73.15% | 60.49% |
| **AIDA** | **75.82%** | **82.56%** | **77.65%** | **74.11%** |

## Dataset Details

- Ovarian: 1053 WSIs (source, 523 patients) + 60 WSIs (target, 60 patients)
- Pleural: 194 WSIs (source) + 53 WSIs (target)
- Bladder: 262 WSIs (source, 86 patients) + 160 WSIs (target, 72 patients)
- Breast: ICIAR-2018 (source, 400 images, 257 patients) + BreaKHis (target, 7909 images)

## Limitations

- Patch-level classification aggregated via VLAD+SVM; end-to-end deep learning alternatives may be more scalable
- Intermediate CNN layer (block 4) was optimal for domain discriminator; requires tuning per dataset
- Breast cancer dataset only binary (benign/malignant); not molecular subtype
