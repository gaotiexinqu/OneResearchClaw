# Document Grounding

## 1. Main Topic / Purpose

This document presents a flexible multi-modal deep learning framework for HER2 (Human Epidermal Growth Factor Receptor 2) breast cancer expression prediction that dynamically handles both complete and incomplete modality inputs. The core innovation is a "dual-modality optional input" architecture that achieves near-dual-modality performance (~94%) even when only a single H&E (Hematoxylin & Eosin) histopathology image is available, significantly outperforming conventional single-modality models (~71%).

## 2. Main Points

- Current HER2 evaluation relies on IHC (immunohistochemistry) and ISH (in-situ hybridization), both of which have limitations: IHC suffers from inter-observer variability, and ISH is expensive and complex.
- Existing AI models handle H&E or IHC in isolation and cannot gracefully handle missing modalities in real clinical workflows.
- The proposed framework introduces a Missing Modality Branch Selector that detects input configuration at runtime and activates either single-modality reconstruction or dual-modality joint inference.
- A Bidirectional Cross-Modal GAN (CM-GAN) reconstructs missing modality images (H&E→IHC or IHC→H&E) in feature space, enabling single-modality inputs to approach dual-modality performance.
- A shared-specific dual-encoder architecture disentangles modality-common and modality-specific features using domain classification loss (DCO) and distribution alignment loss (DAO/MMD).
- A Channel Attention Module (CAM) performs dynamic feature fusion, adaptively weighting features based on input quality.
- Evaluated on the BCI dataset (4,870 paired H&E/IHC images from 51 patients).

## 3. Key Findings / Claims

- Dual-modality (H&E+IHC) accuracy: 95.09%, F1=0.9532.
- H&E-only with CM-GAN reconstruction (Real H&E + Fake IHC): 94.25% accuracy, F1=0.9609 — a +22.81% improvement over baseline H&E-only (71.44%).
- IHC-only with CM-GAN (Real IHC + Fake H&E): 90.28% accuracy, F1=0.9251 — a +12.90% improvement over baseline IHC-only (77.38%).
- CAM ablation: removing channel attention drops F1 from 0.9532 to 0.9041 (−4.91 percentage points).
- The approach reduces dependence on IHC staining, making HER2 testing more accessible in resource-limited settings.

## 4. Constraints / Risks

- All data sourced from a single institution; no external multi-center validation.
- GAN-generated images are approximations — fine details may be imperfect, particularly for HER2 3+ high-expression cases.
- The model treats generated and real images uniformly at the feature level; generated modality features may carry less reliable information.
- The branch selector and CM-GAN are pre-trained separately; end-to-end training dynamics are not explored.

## 4a. Important Non-Textual Elements

- Table 1: Single-modality baseline vs. cross-modal reconstruction method (accuracy and F1 scores).
- Table 2: Dual-modality fusion strategies comparison (simple concat vs. shared-specific + CAM).
- Table 3: CAM ablation results (with/without channel attention).
- Figure 1: Overall framework architecture.
- Figure 2: Bidirectional reconstruction module structure.
- Figure 6: Examples of GAN-generated IHC/H&E images.
- Figure 7: t-SNE visualization of fused features by HER2 class.

## 5. Unresolved Issues

- External validation on datasets from different institutions/scanners is pending.
- Generalization across varying staining protocols and imaging equipment requires domain adaptation.
- The framework has not been extended to other multi-modal pathology tasks (e.g., H&E + genomic data).
- Whether the approach works for other immunohistochemical markers beyond HER2 remains untested.

## 6. Suggested Next Steps

- Conduct multi-center evaluation to verify generalization across institutions.
- Integrate domain adaptation strategies to handle staining protocol variations.
- Extend the dynamic multi-modal architecture to other pathology tasks (e.g., H&E + radiology images, multi-marker IHC panels).
- Investigate end-to-end joint training of CM-GAN and classifier for potential performance gains.
- Explore applicability to other cancer types with analogous multi-modal imaging needs.

## 7. Search Keywords

### Problem Keywords
- HER2 breast cancer assessment limitations
- immunohistochemistry inter-observer variability
- missing modality in multi-modal deep learning
- single-modality histopathology prediction accuracy ceiling
- HER2-low subtype interpretation challenge

### Method / Solution Keywords
- cross-modal image synthesis histopathology
- conditional GAN Pix2Pix medical imaging
- shared-specific feature modeling multi-modal
- channel attention multimodal fusion
- missing modality branch selection deep learning

### Domain / Constraint Keywords
- BCI breast cancer immunohistochemistry dataset
- H&E IHC image registration alignment
- multimodal histopathology computational pathology
- resource-limited HER2 testing accessibility
