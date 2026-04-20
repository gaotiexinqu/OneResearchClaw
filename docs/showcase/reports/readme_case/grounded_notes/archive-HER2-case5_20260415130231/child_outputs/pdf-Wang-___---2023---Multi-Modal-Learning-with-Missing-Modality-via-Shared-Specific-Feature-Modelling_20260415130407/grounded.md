# Document Grounding

## 1. Main Topic / Purpose

This CVPR 2023 paper proposes ShaSpec (Shared-Specific Feature Modelling), a simple yet effective method for multi-modal learning with missing modality. It learns shared features (modality-agnostic) and specific features (modality-specific) via two auxiliary tasks — domain classification (DCO) and distribution alignment (DAO) — and fuses them through a residual procedure. ShaSpec handles missing modalities in both training and evaluation, supports dedicated and non-dedicated training, and applies to both classification and segmentation tasks.

## 2. Main Points

- The missing modality problem: existing multi-modal models require complete modalities for training/testing, limiting real-world applicability.
- ShaSpec architecture: shared encoder + N modality-specific encoders + projection layer + decoder.
- DCO (Domain Classification Objective): binary cross-entropy on specific features to encourage modality-discriminative representations.
- DAO (Distribution Alignment Objective): L1/KL/CE/MSE loss between shared features to enforce modality-invariance via MMD (Maximum Mean Discrepancy).
- Residual fusion: shared features + projected concatenated features → fused modality embedding.
- Missing modality feature generation: for absent modality n, fuse features from all available modalities.
- Non-dedicated training: one model handles all missing modality combinations.
- Validated on BraTS2018 (brain tumor segmentation, 4 MRI modalities) and Audiovision-MNIST (image+audio classification).

## 3. Key Findings / Claims

- On BraTS2018 non-dedicated training: ShaSpec achieves best/second-best in 45/48 results across modality combinations and tumor types.
- Average improvement over second-best: +3.23% (enhancing tumor), +4.91% (tumor core), +3.32% (whole tumor).
- On BraTS2018 dedicated training: best in 11/12 cases; average improvement +2.46% (ET), +1.54% (TC), +0.58% (WT).
- On Audiovision-MNIST (5% audio rate): 93.33% accuracy vs. 92.89% (second-best SMIL).
- Computational efficiency: 0.22M parameters, 0.0257s/training iteration, 1421MiB GPU — superior to SMIL (0.33M, 0.1309s, OOM).
- Ablation confirms both DCO and DAO contribute; removing either degrades performance.
- t-SNE visualization shows shared features cluster by tumor region, specific features separate by modality.

## 4. Constraints / Risks

- DCO and DAO hyperparameter weights (α=0.1, β=0.02) were tuned on one dataset; generalization to others uncertain.
- Distribution alignment objective options (L1/KL/CE/MSE) perform similarly but not identically — no single best choice established.
- Applied to medical imaging (brain tumor) and toy CV dataset (MNIST); generalization to other domains (e.g., pathology) untested.
- Missing modality feature generation is a simple average of available modalities — more sophisticated imputation could improve results.

## 4a. Important Non-Textual Elements

- Table 1: BraTS2018 non-dedicated training Dice scores (15 modality combinations × 3 tumor types).
- Table 2: BraTS2018 dedicated training Dice scores.
- Table 3: Audiovision-MNIST classification accuracy at varying audio rates.
- Table 4: Ablation of DAO loss types (CE/KL/L1/MSE) on T1-only BraTS2018.
- Figure 1: Full-modality training/evaluation architecture.
- Figure 2: Missing-modality training/evaluation architecture.
- Figure 3: Model performance vs. varying missing modality rates.
- Figure 4: Sensitivity analysis of α and β hyperparameters.
- Figure 5: t-SNE visualization of shared and specific features.

## 5. Unresolved Issues

- Optimal DAO loss type remains dataset-dependent (L1 best on BraTS, others untested).
- Generalization from brain imaging to other modalities (pathology, radiology) requires validation.
- Whether the method scales to larger, more diverse datasets is unknown.
- Integration with generative models for missing modality reconstruction (vs. feature-level generation) unexplored.
- Prediction smoothness enhancement (ShaSpec*) is a post-processing step — could be integrated into the model.

## 6. Suggested Next Steps

- Validate ShaSpec on other multi-modal medical imaging tasks (e.g., H&E+IHC pathology, mammography+radiology).
- Investigate combining ShaSpec with generative approaches (VAE/GAN) for more sophisticated missing modality imputation.
- Explore integration with the HER2 multi-modal framework (ShaSpec for feature extraction + CM-GAN for modality reconstruction).
- Extend to more than 2 modalities and larger-scale datasets.
- Investigate alternative distribution alignment objectives (e.g., CORAL, Centered Kernel Alignment).

## 7. Search Keywords

### Problem Keywords
- missing modality multimodal learning
- incomplete multimodal medical imaging
- modality dropout robustness deep learning
- multi-modal brain tumor segmentation missing MRI

### Method / Solution Keywords
- shared-specific feature modeling multimodal
- domain classification modality-specific features
- distribution alignment MMD multimodal
- residual feature fusion missing modality
- ShaSpec multimodal classification segmentation

### Domain / Constraint Keywords
- BraTS2018 brain tumor multimodal MRI
- Audiovision-MNIST multimodal classification
- dedicated vs non-dedicated missing modality training
- feature disentanglement medical imaging
- multimodal learning robustness incomplete data
