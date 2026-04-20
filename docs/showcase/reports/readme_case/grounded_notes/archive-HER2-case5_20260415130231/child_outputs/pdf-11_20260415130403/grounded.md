# Document Grounding

## 1. Main Topic / Purpose

This ACM Woodstock conference paper (2025) proposes an adaptive bimodal input prediction framework for HER2 breast cancer expression assessment that flexibly supports both single-modality and dual-modality inputs. The core contribution is achieving H&E-only prediction accuracy of 94.25% (vs. traditional 71.44%) through a dynamic bidirectional reconstruction mechanism, reducing clinical reliance on IHC staining.

## 2. Main Points

- The framework uses a Missing Modality Branch Selector (two-phase classifier based on GoogLeNet) to detect input completeness in real time and dynamically activate the appropriate processing pathway.
- Bidirectional Cross-Modal GAN (CM-GAN) reconstructs missing modality images using pyramid Pix2pix architecture with multi-scale residual blocks and spatial attention.
- Shared-Specific Feature Encoders use ResNet50 as shared encoder and two MobileNetV3 branches as modality-specific encoders.
- Channel Attention Module (CAM) with hidden dimension 125 performs adaptive feature weight assignment based on input quality.
- Classification uses dual-path pooling (global average pooling + 3×3 max pooling) with weighted cross-entropy loss for class imbalance.
- Dataset: BCI Breast Cancer Pathology dataset (4,870 paired H&E/IHC patches, 51 patients).
- Train/test split: 3,896:977 pairs.

## 3. Key Findings / Claims

- H&E-only: 71.44% baseline → 94.25% with CM-GAN reconstruction (+22.81%).
- IHC-only: 77.38% baseline → 90.28% (+12.90%).
- Dual-modality: simple concatenation baseline 92.00% → 95.09% with shared-specific + CAM (+3.09%).
- CAM ablation: accuracy 95.32% (with) vs. 92.41% (without); F1 0.9532 vs. 0.9041 (+4.91%).
- Inference time: ~0.3s (dual-modality), ~0.5s (with CM-GAN generation).

## 4. Constraints / Risks

- All data from single institution; no external validation.
- CM-GAN generation quality is limited for high HER2 expression (3+) cases.
- Pyramid Pix2pix architecture requires pre-training on paired data.
- Class imbalance handling and weighted loss hyperparameters not fully specified.

## 4a. Important Non-Textual Elements

- Table 1: Unimodal vs. Cross-Modal Reconstruction (accuracy/F1 improvements).
- Table 2: Dual-Modal Fusion Strategies (concat vs. shared-specific).
- Table 3: CAM Ablation Experiment (accuracy/F1 with/without CAM).
- Figure 1: Overall framework architecture (HE/IHC incomplete input HER2 model).
- Figure 2: Bidirectional reconstruction module structure.
- Figure 3: Shared-specific feature extraction module.
- Figure 4: Channel Attention-based Dynamic Weight Fusion Module.
- Figure 6: Dual-path pooling classification module.

## 5. Unresolved Issues

- Multi-center external dataset evaluation required.
- Domain adaptation strategies needed for different staining protocols.
- Extension to other multi-modal pathology tasks not yet explored.
- End-to-end joint training potential unexplored.

## 6. Suggested Next Steps

- Conduct multi-center validation to assess cross-institutional generalization.
- Integrate domain adaptation for protocol variation handling.
- Extend dynamic multi-modal approach to H&E + genomic/radiology fusion.
- Investigate end-to-end training of CM-GAN and classifier jointly.
- Apply "on-demand modality activation" concept to other biomarkers.

## 7. Search Keywords

### Problem Keywords
- HER2 prediction H&E only accuracy
- missing modality breast cancer pathology
- immunohistochemistry resource-limited settings
- adaptive multi-modal deep learning pathology

### Method / Solution Keywords
- missing modality branch selector
- CM-GAN cross-modal reconstruction histopathology
- pyramid Pix2pix image translation medical
- shared-specific feature decoupling multimodal
- channel attention adaptive feature fusion

### Domain / Constraint Keywords
- ACM Woodstock HER2 computational pathology
- BCI dataset multimodal histopathology
- dynamic multimodal inference clinical deployment
- missing modality robustness medical imaging
