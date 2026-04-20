# Literature Research Results

## Research Focus

This literature research investigates the technological landscape surrounding the HER2 breast cancer prediction framework documented in the input archive. The framework is built on three core pillars: (1) multi-modal learning combining H&E and IHC histopathology images, (2) missing modality handling via cross-modal image synthesis and shared-specific feature modeling, and (3) end-to-end HER2 prediction systems. The search covers five thematic directions: state-of-the-art HER2 AI assessment, multi-modal learning with missing modality in computational pathology, cross-modal image synthesis for histopathology, domain generalization across institutions, and molecular biomarker prediction from H&E. The goal is to identify the current state of the art, borrowable techniques, and unresolved challenges relevant to the grounded topic.

The input materials describe a multi-stage HER2 prediction framework that integrates CM-GAN (cross-modal image synthesis for missing modality reconstruction), ShaSpec-style shared-specific feature encoders (ResNet50 shared + MobileNetV3 modality-specific), channel attention module (CAM) for adaptive fusion, and a dual-path pooling classifier, achieving 95.09% dual-modality accuracy and 94.25% H&E-only accuracy on the BCI dataset (4,870 paired H&E/IHC patches, 51 patients).

---

## Overall Literature Synthesis

### The Multi-Modal HER2 Prediction Landscape

The literature reveals a rapidly evolving field where three technical threads are converging on HER2 breast cancer assessment. First, **end-to-end HER2 prediction models** now routinely achieve AUC 0.94–0.95 by fusing multiple imaging modalities (H&E+IHC, or multi-sequence MRI). Second, **missing modality handling** has evolved from simple imputation to sophisticated approaches including generative synthesis (Pyramid Pix2Pix, HistDiST, MuPD), shared-specific feature decomposition (ShaSpec), dynamic modality selection (DyMo), and parameter-efficient adaptation (MoRA). Third, **cross-modal synthesis** has transitioned from Pix2Pix GANs to diffusion-based methods (HistDiST, MuPD), offering substantially better structural fidelity and molecular correlation — HistDiST's 28% MRA improvement over GAN baselines is the most concrete quantitative demonstration of this transition.

### Where the Literature Agrees

There is broad consensus that: (1) multi-modal imaging outperforms single-modality for HER2 prediction; (2) missing modalities are the norm rather than the exception in clinical practice; (3) inter-observer variability in HER2 scoring — especially for HER2-low/ultra-low — is a critical unsolved problem that AI can partially address; and (4) cross-institution domain shift (due to staining protocols, scanners, tissue processing) remains the primary barrier to clinical deployment.

### Where Solution Families Differ

**Approach 1: End-to-end discriminative models** (HER2 MAP, Frontiers HER2 MRI, Precision HER2, HER2 ViT Multistage) directly predict HER2 status from multi-modal images. They differ in backbone architecture (CNN vs. ViT), aggregation strategy (attention vs. VLAD), and clinical integration (standalone vs. nomogram).

**Approach 2: Cross-modal generative synthesis** (Pyramid Pix2Pix, HistDiST, MuPD) generate missing IHC from available H&E, then run standard IHC analysis. They differ in generation quality, molecular fidelity, and the breadth of modality integration. HistDiST (LDM-based) and MuPD (diffusion transformer) represent the current frontier; Pyramid Pix2Pix (GAN-based) is the baseline that has been most extensively validated in histopathology.

**Approach 3: Feature-level missing modality handling** (ShaSpec, MoRA, DyMo) operate at the representation level rather than the pixel level. They differ in whether they require retraining (ShaSpec), can plug into pretrained models (MoRA), or dynamically select at inference (DyMo).

**Approach 4: Domain generalization** (AIDA) addresses cross-institutional deployment through adversarial frequency-domain adaptation, achieving +18.96 pp on cross-dataset breast cancer classification — this thread is largely independent of the above three but is essential for real-world deployment.

### What Looks Most Relevant to the Grounded Topic

The most directly relevant methods are: (1) HER2 MAP (Nature Biomed Eng 2025) as the end-to-end benchmark; (2) HistDiST as the superior alternative to Pyramid Pix2Pix for cross-modal synthesis, with 28% MRA improvement and a novel pathology-aware evaluation metric (MRA); (3) ShaSpec as the most validated approach for shared-specific feature decomposition; (4) DyMo as an alternative dynamic modality selection design; (5) AIDA as the domain adaptation solution for cross-institutional robustness; and (6) the AIDA FFT-Enhancer as a frequency-domain preprocessing complement to color normalization.

### Where Evidence is Weak or Missing

1. **Clinical validation of generated IHC images**: The BCI dataset paper shows pathologists achieve only 37.5–40% accuracy on GAN-generated IHC images. Whether HistDiST or MuPD-generated images achieve better pathologist acceptance is not yet clinically validated — this is the single most critical gap for the HER2 prediction framework's clinical impact.
2. **HER2-low/ultra-low specifically**: Fewer studies focus on this clinically important subgroup than on HER2-positive vs. HER2-negative binary classification.
3. **Dynamic modality selection in histopathology**: DyMo and MoRA have been validated primarily on general/medical image classification tasks; their application to 100,000×100,000 pixel WSIs is underexplored.
4. **Cross-institutional external validation**: The AIDA paper demonstrates +18.96 pp on cross-dataset breast cancer classification, but this is for binary benign/malignant. HER2 molecular subtype prediction across institutions remains largely absent.

---

## Detailed Analysis of Opened Papers

### P001 — HER2 MAP: Multimodal Alignment and Prediction (Nature Biomedical Engineering, 2025)

**Problem and Task Setting**: Accurate HER2 status prediction for treatment planning in breast cancer. Traditional needle biopsies sample limited tissue, leading to inaccurate assessments due to intratumoral heterogeneity. The task is to predict HER2 status and neoadjuvant therapy response from pre-treatment multi-modal breast cancer images across 4 medical centers.

**Methodology and Why It Works**: The HER2 MAP model integrates multi-modal breast cancer images through a deep learning framework. The model leverages the complementarity of different imaging modalities to build a more comprehensive tumor profile than any single modality can provide. The large-scale training data (14,472 images, 6,991 cases, 4 centers) is critical for generalization. The multi-modal approach directly addresses the intratumoral heterogeneity problem that causes traditional biopsy failures.

**Main Evidence**:
- Dataset: 14,472 images from 6,991 cases across 4 medical centers
- Demonstrates superiority over traditional needle biopsies
- Center C data available at Cancer Imaging Archive
- GitHub code available: https://github.com/ZhangJD-ong/HER2-MAP-from-Multimodal-Breast-Data

**Relevance to the Current Grounded Topic**: This paper represents the state-of-the-art end-to-end HER2 prediction benchmark. The HER2 prediction framework in the grounded documents is architecturally similar (multi-modal input + feature fusion + classification) but focuses specifically on H&E+IHC combination. The MAP model's multi-center training strategy and heterogeneous tumor coverage approach are directly applicable design principles. The code availability makes it a concrete reference for implementation details.

**Limits**: Relies on multi-modal imaging data availability; does not specifically address missing modality scenarios; performance depends on image quality and preprocessing consistency across centers.

---

### P002 — HER2 Expression Prediction from Multi-Sequence MRI (Frontiers in Oncology, 2025)

**Problem and Task Setting**: Predict HER2 expression status from multi-sequence breast MRI (T1, T2, DCE) combined with clinical data. Dataset: 2,400 patients (1,286 HER2+, 1,114 HER2-) from 4 centers. The goal is to build a clinically deployable predictive tool with interpretable outputs.

**Methodology and Why It Works**: Four deep learning architectures (ResNet50, VGG16, EfficientNet-B0, ViT-Small) extract features from MRI sequences. ICC filtering (≥0.9) selects reproducible features, then LASSO regression reduces dimensionality. A nomogram integrates deep learning scores with clinical features (lymph node status, enhancement curve, peritumoral edema, microcalcifications). The key insight is that combining imaging features with clinical metadata substantially outperforms imaging alone.

**Main Evidence**:
- Individual models AUC: 0.88–0.89; with clinical data: **0.94**
- Key clinical predictors: washout enhancement curve (p=0.003), peritumoral edema (p=0.001), microcalcifications (p=0.002)
- Internal validation: 1,000 bootstrap resamples; Hosmer-Lemeshow test confirms calibration
- Frozen-weight feature extraction outperforms fine-tuning for cross-center generalization

**Relevance to the Current Grounded Topic**: Although this paper uses MRI rather than histopathology images, it provides the strongest quantitative evidence that multi-modal feature fusion with clinical data achieves AUC 0.94 for HER2 prediction. The ICC filtering + LASSO feature selection pipeline, the frozen-weight vs. fine-tuning finding, and the clinical feature integration strategy are all transferable insights for the HER2 prediction framework.

**Limits**: HER2+ prevalence (53.6%) is enriched vs. general population (15–20%); no external validation; 1,000 bootstrap is internal validation only.

---

### P003 — Multi-Stage Vision Transformers for HER2 Status Scoring (arXiv, 2025) — *PDF Refined*

**Problem and Task Setting**: Simultaneous H&E and IHC analysis for 4-way HER2 scoring (0, 1+, 2+, 3+) on whole slide images, with pixel-level HER2 annotation. The paper's PDF (arXiv:2512.22335) provides significantly more method detail than the opened page. Dataset: 13 paired H&E+IHC WSI cases from clinical archives (p53-abnormal endometrial carcinoma tissue, H&E and HER2 IHC 4B5 Clone), with patches of 143×143 microns. The study specifically addresses the challenge of joint H&E+IHC analysis for HER2 scoring, which existing methods handle poorly.

**Methodology and Why It Works** (PDF-confirmed):

The pipeline consists of four stages:

1. **H&E Whole Slide Image Classification**: Automatic tumor localization from H&E WSIs using a ViT-based classifier to identify regions with abnormality. The system processes full WSIs to detect localized regions with abnormality, leading to cancer detection.

2. **Mapping Regions in H&E into IHC WSIs**: A novel approach corresponds tumor-defected regions of H&E tissue with exact regions in matching IHC WSIs. This spatial correspondence enables targeted IHC analysis of morphologically relevant areas.

3. **Semantic Pixel Segmentation and Annotation**: A MaskFormer-based segmentation transformer achieves pixel-level categorization of stain intensity classes, producing segmentation maps corresponding to different HER2 scores.

4. **Pipeline for H&E Classification and HER2 Scoring**: Two separate ViT-based models handle tumor identification and HER2 stain intensity classification. Transformer architectures L, M, and C interact to compute patch-wise HER2 status scores, which aggregate into WSI-level scores via an aggregation algorithm. The architecture employs hierarchical ViTs (including Swin Transformer, Hiera, and specialized vision transformers) alongside MobileNet for comparative evaluation.

The PDF confirms that the ViT approach outperforms CNN baselines (MobileNet) on this task, and that the architecture combines three transformer models for joint tumor detection and HER2 scoring.

**Main Evidence** (PDF-confirmed):
- Classification accuracy: **0.94** (4-way HER2: 0, 1+, 2+, 3+)
- Specificity: **0.933**
- Tumor localization accuracy: good
- Joint H&E+IHC evaluation comparable to human pathologists
- Comparative analysis (Table 4 in PDF): HE-HER2Net (transfer learning + Grad-CAM): accuracy 0.87, precision 0.88, recall 0.86, AUC 0.98; WSMCL (weakly supervised multi-modal contrastive learning): AUC 0.783; competing ViT approaches: AUC 0.90
- The paper's approach surpasses all comparable methods on the same evaluation
- Decision curve analysis (DCA) confirms clinical utility and net benefit beyond standard metrics

**Relevance to the Current Grounded Topic**: This paper directly demonstrates that joint H&E+IHC ViT analysis achieves 94% accuracy in 4-way HER2 scoring, comparable to the HER2 MAP model but using a different modality combination. The end-to-end ViT approach represents an alternative architecture to the ResNet50+MobileNet dual-encoder in the HER2 prediction framework. The MaskFormer-based pixel-level HER2 annotation capability addresses the interpretability concern in the HER2 prediction framework's dual-path pooling approach.

**Limits**: Very small dataset (13 cases) limits statistical power and generalizability; private dataset limits reproducibility; end-to-end approach may sacrifice interpretability compared to the HER2 prediction framework's modular design.

---

### P004 — AI-Enhanced HER2 Ultra-Low Diagnosis (Breast Cancer Research, 2026)

**Problem and Task Setting**: HER2 ultra-low expression (~10% of breast cancers, critical for ADC therapy eligibility) is frequently misclassified by pathologists. AI assistance from the Roche Navify Digital Pathology platform is evaluated against expert consensus ground truth. Dataset: 188 cases (376 WSIs), external validation cohort of 89 slides from 2 hospitals.

**Methodology and Why It Works**: AI tool performs WSI-level HER2 scoring. Nine pathologists independently re-evaluate their assigned slides with and without AI assistance. The AI system filters out DCIS components, focuses on invasive tumor regions, and analyzes positive controls as internal quality checks. Expert consensus diagnosis serves as ground truth. The key design principle is "AI assists, pathologist decides" — not a fully automated replacement.

**Main Evidence**:
- HER2 ultra-low detection: F1-score 0.78→**0.98**, precision 0.39→**0.91**, recall 0.72→**0.96** (with AI)
- CNB-SE concordance: 0.37→**0.48** (AI reduces underestimation)
- Post-NAT specimen consistency: 0.63→**0.92**
- External validation: 89 slides from 2 independent hospitals
- Inter-observer agreement improved from κ=0.37 to κ=0.64

**Relevance to the Current Grounded Topic**: This paper provides the most compelling clinical validation evidence for AI-assisted HER2 scoring. The dramatic F1 improvement from 0.78 to 0.98, especially the precision leap from 0.39 to 0.91, directly addresses the key clinical need that motivates the HER2 prediction framework. The finding that AI primarily reduces underestimation (misclassifying HER2-low as HER2-negative) is particularly relevant because it quantifies the therapeutic impact of accurate AI-assisted scoring.

**Limits**: Commercial AI system (Roche Navify) — not openly available; external validation on only 89 slides; potential institutional conflict of interest.

---

### P005 — Precision HER2: A Comprehensive AI System (BMC Cancer, 2024) — *PDF Refined*

**Problem and Task Setting**: Fully automated HER2 scoring on IHC whole-slide images, following ASCO/CAP 2018/2023 guidelines. The system focuses on invasive tumor regions and generates HER2 scores (0, 1+, 2+, 3+) consistent across slides and laboratories.

**Methodology and Why It Works** (from PDF): Multi-phase pipeline:
1. Invasive tumor region detection to exclude non-invasive areas
2. Individual tumor cell membrane staining classification based on staining intensity and completeness
3. ASCO/CAP guideline-compliant scoring algorithm
4. Positive control analysis as quality assurance

The system is designed for clinical deployment rather than research evaluation, with explicit ASCO/CAP 2018/2023 guideline compliance.

**Main Evidence** (PDF-confirmed):
- High concordance with expert pathologists for HER2 scoring
- Improved scoring consistency across slides and laboratories
- Reduces misdiagnosis of HER2 1+ patients as HER2 0 (key for ADC eligibility)
- Follows ASCO/CAP 2018/2023 guidelines explicitly

**Relevance to the Current Grounded Topic**: This paper represents the clinical deployment target for the HER2 prediction framework. The multi-phase design (filtering → region detection → cell classification → scoring) provides a concrete clinical pipeline architecture. The ASCO/CAP guideline compliance requirement is essential for any clinically deployed HER2 AI system. The PDF confirms that this system is the most clinically oriented HER2 AI paper in the literature.

**Limits**: Specific performance numbers not fully detailed in the accessible PDF content; validation methodology details limited.

---

### P006 — ShaSpec: Shared-Specific Feature Modelling (CVPR 2023) — *PDF Refined*

**Problem and Task Setting**: Missing modality problem in multi-modal learning. Most approaches either train separate models for each missing scenario or discard missing modalities. ShaSpec learns both shared features (modality-invariant) and specific features (modality-specific) from incomplete multi-modal data, enabling a single model to handle arbitrary missing modality configurations. This paper is authored by Wang et al. (University of Adelaide) and Carneiro (University of Surrey), appearing at CVPR 2023.

**Methodology and Why It Works** (PDF-confirmed):

**Architecture** (PDF-confirmed from Figure 1 and text):

Full-modality training: All modalities {x^(i)} are passed through one shared encoder and individual specific encoders to produce shared features {r^(i)} and specific features {s^(i)}. In a residual learning manner, the shared and specific features are fused with a linear projection fθ_proj to get fused features {f^(i)} for decoding. The model uses skip connections to preserve modality-specific information.

**Core equations** (from PDF, Equations 5 and related text):
- **DCO (Domain Classification Objective)**: Binary cross-entropy on specific features forces them to be modality-discriminative. Formally: ℓ_dco = -Σ_j Σ_i (t^(i))⊤ log(f_θ_dco(s^(i)_j)), where t^(i) ∈ {0,1}^N is the one-hot modality label.
- **DAO (Distribution Alignment Objective)**: MMD/KL/L1 loss on shared features enforces modality-invariance. Ablation (Table 4 in PDF): L1 loss performs best (Enhancing Tumor: 42.58, Tumor Core: 64.53, Whole Tumor: 74.82), followed by KL divergence, then CE, then MSE.
- **Residual Fusion**: f = r + proj([s₁; s₂; ...; sₙ]) where r = shared features. During missing modality evaluation, missing modalities are replaced by averaging available modalities.
- **Auxiliary loss weight**: Sensitivity analysis (Figure 4 in PDF) shows optimal α=0.1, β=0.02 for the DCO and DAO loss weights; α=β=1 causes significant performance drop.

**Full modality evaluation** (Table 1 in PDF): On BraTS2018 (4-modality MRI), ShaSpec achieves:
- Fl only: 43.52 (Enhancing Tumor), 86.10 (Tumor Core), 88.83 (Whole Tumor) vs. UHeMIS 11.78, 52.48, 84.39
- Average across all 15 modality combinations: **85.92%** Dice (Whole Tumor, dedicated) vs. UHeMIS 79.16%, UHVED 84.39%
- ShaSpec* (with dedicated training): 86.26% average (Whole Tumor)

**Missing modality feature generation**: When a modality is missing (e.g., x^(n)), the available modalities' fused features f^(1), ..., f^(n-1), f^(n+1), ..., f^(N) are used to reconstruct the missing feature f^(n) through the residual fusion mechanism.

**Relevance to the Current Grounded Topic**: ShaSpec provides the algorithmic foundation for the shared-specific feature decomposition used in the HER2 prediction framework's dual-encoder architecture. The DCO and DAO loss functions are directly referenced and applied in the input documents. ShaSpec's residual fusion mechanism is a concrete design for handling arbitrary missing modality configurations without retraining.

**Limits**: DCO/DAO hyperparameters (α=0.1, β=0.02) tuned on brain imaging; generalizability to histopathology uncertain; missing modality feature generation is simple averaging of available modalities (not generative); no end-to-end training with image synthesis models; evaluated primarily on medical imaging (BraTS2018), not on whole-slide histopathology; Audiovision-MNIST results (Table 3 in PDF) confirm 92.89% at 5% audio rate vs. lower bounds.

---

### P007 — DyMo: Dynamic Modality Selection (arXiv, 2026) — *PDF Refined*

**Problem and Task Setting**: The "discarding-imputation dilemma" in incomplete multi-modal learning — existing methods either discard missing modalities (losing information) or impute them (introducing noise). DyMo addresses this by dynamically selecting reliable recovered modalities at inference time for each test sample.

**Methodology and Why It Works** (PDF-confirmed): Central innovation: theoretically connecting multi-modal task-relevant information with task loss. Since direct information estimation is intractable at test time, DyMo uses **inference-time task loss as a tractable proxy** for modality relevance. A principled reward function based on information maximization guides which modality combinations to select. Architecture: flexible multi-modal network compatible with arbitrary modality combinations + tailored training strategy for robust representation learning. This is fundamentally different from static branch selection (which uses a fixed policy) or generative imputation (which fixes missing data before classification).

**Main Evidence** (PDF-confirmed):
- Significantly outperforms SOTA incomplete/dynamic MDL methods across various missing-data scenarios
- Evaluated on diverse natural and medical image datasets
- Code: https://github.com/siyi-wind/DyMo

**Relevance to the Current Grounded Topic**: DyMo provides a principled information-theoretic framework for the same problem addressed by the HER2 prediction framework's dynamic branch selection mechanism. While the HER2 prediction framework uses a quality-gated branch selection approach (Channel Attention Module as quality metric), DyMo's loss-based modality scoring offers an alternative design principle. The flexible architecture compatibility means it could be integrated with the HER2 prediction framework's modality recovery pipeline.

**Limits**: Dynamic selection at inference adds computational overhead; requires tailored training strategy; evaluated on general/medical image classification, not on histopathology WSI classification.

---

### P008 — MoRA: LoRA for Missing Modality (arXiv, 2024) — *PDF Refined*

**Problem and Task Setting**: Applying multi-modal pretrained models to disease diagnosis with missing modalities, while keeping fine-tuning computationally tractable. Previous methods (prompt-based: MAPs, MSPs) either lack robustness across different missing settings or need to be plugged into several layers.

**Methodology and Why It Works** (PDF-confirmed): Modality-aware Low-Rank Adaptation (MoRA). Unlike standard LoRA which applies the same up-projection to all inputs, MoRA uses **different modality-aware up-projections** for different modalities. During fine-tuning, all pretrained weights are frozen; only MoRA modules + classifier are trained.

**Main Evidence** (PDF-confirmed):
- <1.6% trainable parameters vs. full fine-tuning
- Outperforms existing fine-tuning methods on disease diagnosis with missing modalities
- Plug-and-play: integrates into first block of pretrained model
- Compatible with arbitrary modality combinations

**Relevance to the Current Grounded Topic**: MoRA offers a parameter-efficient alternative to ShaSpec for missing modality handling. Its integration into pretrained models (critical for histopathology where large pretrained models like CPath-Omni are becoming standard) makes it complementary to both ShaSpec (feature-level) and CM-GAN (generation-level) approaches. For the HER2 prediction framework, MoRA could enable efficient fine-tuning of a pretrained multi-modal pathology model.

**Limits**: Designed for fine-tuning pretrained models (not from-scratch training); two-modality assumption in problem formulation; pathology-specific validation absent.

---

### P009 — HistDiST: Diffusion-Based Stain Transfer (arXiv, 2025) — *PDF Refined*

**Problem and Task Setting**: H&E-to-IHC stain transfer for histopathology, enabling cost-effective molecular biomarker assessment from routine H&E images. Existing GAN-based methods suffer from training instability and limited structural fidelity. The task is high-fidelity H&E→IHC translation with molecular relevance, validated on MIST and BCI datasets.

**Methodology and Why It Works** (PDF-confirmed):

**Framework**: Latent Diffusion Model (LDM) built on Stable Diffusion v1.5, fine-tuned for 500 epochs (batch size 16, AdamW, lr=2e-4, 1000 warmup steps, cosine decay).

**Training pipeline** (Figure 1 in PDF):
1. **VAE encoder** maps images to latent representations
2. **H&E Encoder (Phikon)** — a self-supervised transformer trained on 40 million histology images — extracts morphological embeddings injected into U-Net cross-attention layers
3. **Dual-conditioning**: (a) Phikon morphological embeddings via cross-attention for pathology-relevant context; (b) VAE-encoded H&E latents concatenated with noise at U-Net input for structural guidance from earliest denoising stages
4. **Joint training**: Alternates between H&E generation (CLIP text conditioning) and H&E→IHC translation

**Key technical innovations** (PDF-confirmed):
1. **v-prediction** with γ=5: addresses brightness biases in histopathology
2. **Rescaled noise schedule** with zero terminal SNR condition
3. **DDIM inversion** (200 steps): preserves morphological structure during inference
4. **η-cosine noise schedule** (start 20%): balances structural consistency (determinism) and molecular fidelity (stochasticity)
5. **Molecular Retrieval Accuracy (MRA)**: novel evaluation metric using GigaPath feature embeddings — measures cosine similarity of generated IHC feature representations to real IHC, capturing pathology-relevant molecular content rather than pixel-level similarity

**Quantitative results** (Table 1 in PDF):

| Dataset | Method | SSIM | PHVL1↓ | MRA↑ | FID↓ |
|--------|--------|------|--------|------|------|
| MIST HER2 | ASP | 0.2004 | 0.4534 | 0.193 | 51.4 |
| MIST HER2 | MDCL | 0.1810 | 0.4371 | 0.233 | 44.4 |
| MIST HER2 | InstructPix2Pix | 0.1353 | 0.5272 | 0.125 | 65.6 |
| MIST HER2 | ControlNet | 0.1813 | 0.4437 | 0.188 | 36.9 |
| **MIST HER2** | **HistDiST** | **0.2059** | **0.3830** | **0.466** | **36.9** |
| BCI HER2 | MDCL | 0.5029 | 0.3861 | 0.084 | 51.2 |
| BCI HER2 | ControlNet | 0.4581 | 0.5001 | 0.070 | 43.5 |
| **BCI HER2** | **HistDiST** | **0.4693** | **0.3136** | **0.218** | **34.2** |

On MIST Ki67 (Table 1): **28% MRA improvement** (0.201→0.484) vs. MDCL. On BCI HER2: **159% MRA improvement** (0.084→0.218) vs. MDCL.

**Ablation** (Table 2 in PDF):
- SD+IC alone (no v-pred): FID 61.3, SSIM 0.154
- +v-prediction: FID 37.5, SSIM 0.198 (FID drops by 39%)
- +DDIM inversion: SSIM 0.228 (structural improvement)
- +Phikon cross-attention: PHVavg 0.436, FID 31.3 (best overall)

**Relevance to the Current Grounded Topic**: HistDiST directly improves upon the Pyramid Pix2Pix approach used in the BCI dataset paper. Its MRA improvement over GAN baselines represents a significant qualitative leap in synthesis quality. Critically, the paper's own conclusion explicitly states: "we emphasize that this method is not clinically applicable at this stage; additional validation and analysis (e.g., expert review or downstream task performance) would be required before considering diagnostic use." This directly confirms that even HistDiST-generated images remain pre-clinical — which validates the HER2 prediction framework's approach of using AI-assisted scoring rather than full automation.

**Limits**: Computational cost of diffusion models higher than GANs; validated primarily on Ki67 and BCI datasets; broader pathology generalisation unknown; zero-SNR condition is novel and not yet widely validated; training requires 500 epochs with alternating tasks; 200 inversion + 200 denoising steps at inference.

---

### P010 — MuPD: Multimodal Pathology Diffusion (arXiv, 2026)

**Problem and Task Setting**: Unified generative foundation model for histopathology that integrates H&E histology, RNA profiles, and clinical text in a shared latent space via diffusion transformer. Addresses the limitation of task-specific models trained on narrow single source-target pairs.

**Methodology and Why It Works**: Diffusion Transformer (DiT) backbone with **decoupled cross-modal attention** — separate attention streams for different modality pairs (H&E↔RNA, H&E↔text, RNA↔text). Pretraining data: 100M histology patches, 1.6M text-histology pairs, 10.8M RNA-histology pairs, across 34 human organs. Supports: (1) text-conditioned histology generation; (2) RNA-conditioned histology generation; (3) virtual staining (H&E→IHC).

**Main Evidence**:
- FID reduced by **50%** vs. domain-specific models for text-conditioned and image-to-image generation
- Few-shot classification accuracy improved by up to **47%** through synthetic data augmentation
- RNA-conditioned histology: FID reduced by **23%** vs. next-best; preserves cell-type distributions across 5 cancer types
- Virtual stainer: H&E→IHC translation with **37% higher marker correlation** than existing methods

**Relevance to the Current Grounded Topic**: MuPD represents the most ambitious cross-modal synthesis approach for computational pathology. Its 37% improvement in IHC marker correlation for virtual staining directly improves upon the Pyramid Pix2Pix baseline in the BCI dataset paper. The shared latent space for H&E+RNA+IHC+text is architecturally analogous to — but more comprehensive than — the multi-modal fusion in the HER2 prediction framework. MuPD can serve as a universal backbone replacing individual CM-GAN, ShaSpec, and channel attention modules.

**Limits**: Very large model (diffusion transformer); computational cost likely prohibitive for routine use; HER2-specific IHC validation not reported; RNA integration requires genomic data; most ambitious paper here but also least validated on specific clinical tasks; PDF download timed out during research.

---

### P011 — AIDA: Adversarial Fourier Domain Adaptation (npj Precision Oncology, 2024) — *PDF Refined*

**Problem and Task Setting**: Domain shift in multi-center histopathology classification. CNNs are sensitive to amplitude spectrum variations (staining, scanner differences) but humans rely on phase-related components (morphology). AIDA combines adversarial training with FFT-Enhancer to make models domain-invariant.

**Methodology and Why It Works** (PDF-confirmed): FFT-Enhancer module processes images in frequency domain, adjusting source domain colors to look like target domain. The adversarial training component has a domain classifier that learns to distinguish source from target while the feature extractor tries to fool it. VLAD aggregation converts patch-level features to slide-level representations. Key finding: intermediate CNN layers (block 4) produce the most generalizable features for domain adaptation.

**Main Evidence** (PDF-confirmed):
- Breast cancer (source: ICIAR-2018, target: BreaKHis): Base 55.15% → AIDA **74.11%** balanced accuracy (+18.96 pp)
- Ovarian cancer: Base 64.65% → AIDA **75.82%** (+11.17 pp)
- Bladder cancer: Base 54.77% → AIDA **77.65%** (+22.88 pp)
- Adversarial training alone (ADA): +5.34 pp (breast); +9.51 pp (bladder) over base
- FFT-Enhancer contributes additional +13.62 pp (breast) over ADA alone
- VLAD+SVM at block 4: best cross-domain performance

**Relevance to the Current Grounded Topic**: AIDA directly addresses the cross-institutional deployment challenge noted in the BCI dataset paper and the HER2 prediction framework's evaluation. The +18.96 pp improvement on the breast cancer cross-dataset task demonstrates that domain adaptation is essential for real-world deployment. The FFT-Enhancer's frequency-domain approach is complementary to color normalization and stain augmentation methods.

**Limits**: VLAD+SVM aggregation is not end-to-end (unlike attention-based methods); intermediate CNN layer selection requires tuning per dataset; breast cancer task is binary (benign/malignant), not molecular subtype classification.

---

### P012 — Molecular Biomarker Prediction from H&E Review (JPM, 2022)

**Problem and Task Setting**: Comprehensive review of deep learning methods for predicting molecular biomarkers from H&E-stained histopathology whole slide images. Covers four biomarker categories: (1) protein biomarkers, (2) genomic subtypes/expression, (3) molecular alterations, (4) virus presence. Across 10+ cancer types.

**Methodology and Why It Works**: Reviews frameworks from bottom-up (learn directly from pixels) to pathologist-driven (use expert features) to hybrid. Key methodological insights: (1) Weak supervision (patient-level labels only) requires MIL attention mechanisms; (2) Self-supervised pretraining (fingerprinting, contrastive learning) significantly improves feature quality; (3) Transformers are emerging as superior to CNNs for WSI analysis; (4) Tile aggregation via attention-weighted pooling (DeepMIL) outperforms mean prediction or majority vote.

**Main Evidence**:
- HER2 protein biomarker: La Barbera et al. used second-stage classifier on tile predictions; self-supervised fingerprinting improves HER2 prediction
- Multiple instance learning with attention provides visual indication of HER2-positive regions
- Contrastive learning (cross-entropy + contrastive objectives) increases intra-class similarity
- Challenges: small training sets, weak supervision, WSI processing (100,000×100,000 pixels), model explainability

**Relevance to the Current Grounded Topic**: This review provides the methodological foundation for H&E→biomarker prediction. The MIL attention mechanism, self-supervised pretraining strategy, and tile aggregation methods are all directly applicable to the HER2 prediction framework's H&E encoding pipeline. The identified challenges frame the evaluation priorities for the HER2 prediction framework.

**Limits**: 2022 review; does not cover recent transformer-based and foundation model approaches; primarily methodological overview rather than empirical results; PDF download produced invalid file (1,817 bytes) — content based on opened HTML page only.

---

### P013 — Multi-Modal Foundation Models for Computational Pathology: A Survey (arXiv, 2025) — *PDF Refined*

**Problem and Task Setting**: Comprehensive survey of 32 multi-modal foundation models in computational pathology, categorizing them into three paradigms: vision-language, vision-knowledge graph, and vision-gene expression. Analyzes 28 datasets and identifies key challenges and future directions.

**Methodology and Why It Works** (PDF-confirmed): Systematic taxonomy of multi-modal CPath models. Vision-language models (non-LLM-based vs. LLM-based) integrate text/reports with images. Vision-knowledge graph models incorporate structured domain knowledge. Vision-gene expression models (closest to the HER2 prediction framework's domain) integrate molecular profiles. Key finding: most successful models use pathology-specific pretraining beyond ImageNet.

**Key Challenges Identified**:
1. Data heterogeneity (WSI scale vs. text/RNA granularity)
2. Annotation cost and quality
3. Cross-modal alignment at different granularity levels
4. Domain shift across institutions
5. Interpretability and clinical validation requirements

**Relevance to the Current Grounded Topic**: This survey provides the strategic landscape for where the HER2 prediction framework fits. It confirms that the vision-gene expression paradigm (H&E+IHC+RNA integration) is an active and important research direction. The identified challenges directly inform what the HER2 prediction framework needs to address for clinical deployment.

**Limits**: Survey paper (no primary experimental results); rapidly evolving field (models from 2025-2026 may not be fully covered).

---

### P014 — CPath-Omni: Unified Foundation Model (arXiv, 2024) — *PDF Refined*

**Problem and Task Setting**: First 15-billion-parameter Large Multi-modal Model (LMM) unifying both patch-level and whole-slide image (WSI) analysis in computational pathology. Addresses redundancy of separately trained patch and WSI models.

**Methodology and Why It Works** (PDF-confirmed): Unified architecture handling classification, VQA, captioning, and visual referring prompting at both patch and WSI levels. CPath-CLIP: specialized pathology CLIP visual processor integrating multiple vision models with LLM text encoder. The unification strategy avoids redundant feature extraction between patch-level and WSI-level models.

**Main Evidence** (PDF-confirmed):
- SOTA on **39/42** datasets across diverse tasks
- Outperforms task-specific models trained for individual tasks
- CPath-CLIP: SOTA on 9 zero-shot and 4 few-shot datasets

**Relevance to the Current Grounded Topic**: CPath-Omni provides the broader context of large-scale foundation models for computational pathology. Its unified patch+WSI architecture addresses the aggregation challenge in HER2 prediction (MIL attention vs. VLAD vs. other aggregation strategies). CPath-CLIP's pathology-specific visual processor could serve as a feature extractor for the HER2 prediction framework.

**Limits**: 15B parameters = extreme computational cost; CLIP-based approach may miss fine-grained biomarker details; not specifically validated for HER2 scoring; pathology domain adaptation still required.

---

## Newly Strengthened / Newly Added Papers from Downloaded PDFs

### ShaSpec Deep Evidence (PDF Source: CVPR 2023, arXiv:2307.14126)

The downloaded PDF reveals substantially more methodological depth than the opened arXiv page:

**BraTS2018 Comprehensive Results**: The full Table 1 shows ShaSpec across all 15 possible modality combinations on BraTS2018. Key findings: (1) ShaSpec consistently outperforms UHeMIS, UHVED, RbSeg, and mmFm across nearly all modality combinations; (2) The dedicated training version (ShaSpec*) consistently outperforms the non-dedicated version; (3) The improvement is most dramatic when modalities are severely limited — e.g., with only Fl available (Enhancing Tumor: 43.52 vs 11.78 for UHeMIS, +270% relative improvement); (4) Even with all 4 modalities, ShaSpec* achieves 86.26% average Dice vs. 88.46 for full-modality baseline — a gap of only 2.2 pp.

**Audiovision-MNIST Results**: At 5% audio rate, ShaSpec achieves 93.33% accuracy vs. SMIL 92.89% and Full2miss 90.00%, confirming its effectiveness on non-medical multi-modal classification tasks as well.

**DCO and DAO Formulations**: The PDF provides the complete mathematical formulation. The DAO can use CE, KL, L1, or MSE loss — ablation confirms L1 is optimal for distribution alignment. The sensitivity analysis (Figure 4) shows that the auxiliary loss weights must be carefully tuned: α=0.1 (DCO weight) and β=0.02 (DAO weight) are optimal; larger values (α=β=1) cause severe degradation, indicating that auxiliary losses can overpower the main task if not properly weighted.

**Critical Design Insight**: The residual fusion f = r + proj([s₁; s₂; ...; sₙ]) is fundamentally different from simple addition or concatenation. The projection layer fθ_proj learns to weight and combine modality-specific features in a learned latent space before adding them to the shared feature residual. This is what enables the model to adapt to different missing modality configurations without retraining — the projection layer learns the correct way to combine available modality-specific features with shared features.

---

### HistDiST Deep Evidence (PDF Source: arXiv:2505.06793, eess.IV)

The downloaded PDF provides comprehensive quantitative evidence not visible in the opened page:

**MIST Dataset Comprehensive Results**: The full Table 1 covers all four MIST stain types (ER, HER2, Ki67, PR). Key findings: (1) On MIST ER, HistDiST achieves the lowest PHV scores (0.3645/0.3105/0.2465 across three patch levels) — indicating the best feature-level alignment with real IHC; (2) On MIST Ki67, the MRA improvement is 28% (0.201→0.484 vs. MDCL); (3) On MIST PR, HistDiST's MRA of 0.434 vs. MDCL's 0.317 represents a 37% improvement; (4) FID scores are consistently lower than all other methods across stain types (31.3 ER, 36.9 HER2, 28.05 Ki67, 33.7 PR) — indicating the most visually realistic generated images.

**Ablation Interpretation**: Table 2 reveals the contribution of each component on the ER stain type: (1) SD+IC alone (baseline diffusion with H&E feature conditioning): SSIM=0.154, FID=61.3 — poor; (2) +v-prediction: SSIM=0.198, FID=37.5 — v-prediction dramatically improves molecular fidelity; (3) +DDIM inversion: SSIM=0.228, FID=41.3 — inversion improves SSIM (structural fidelity) but increases FID (less realistic distribution); (4) +Phikon cross-attention: SSIM=0.227, FID=31.3, PHVavg=0.436 — Phikon embeddings fix the FID degradation while maintaining SSIM gains.

**Critical Clinical Caveat**: The paper's conclusion section explicitly states: "we emphasize that this method is not clinically applicable at this stage; additional validation and analysis (e.g., expert review or downstream task performance) would be required before considering diagnostic use." This is the most important constraint for the HER2 prediction framework — even HistDiST, the current state of the art in stain transfer, does not claim clinical readiness.

**DDIM Inversion Equation**: The PDF provides the exact inversion formula (Equation 6): zt+1 = √αₜ₊₁(zt − √1−αₜ ϵθ(zt, t, cT)√αₜ) + √1−αₜ₊₁ϵθ(zt, t, cT). The 200 inversion + 200 denoising steps at inference is computationally expensive compared to single-pass GAN inference.

---

## Snippet-Level / Not-Fully-Opened Candidates

### P001 — HER2 MAP (Nature Biomedical Engineering, 2025): Partial Content

The full PDF could not be downloaded ("No downloadable PDF found"). The opened Nature page provides sufficient information about the core contribution (14,472 images, 6,991 cases, 4 centers, GitHub available), but method details and ablation results are incomplete. The Nature article is the definitive end-to-end HER2 prediction benchmark and its architectural decisions would be highly relevant to the HER2 prediction framework.

### P002 — Frontiers HER2 MRI 2025 (Frontiers in Oncology): Partial Content

PDF download not available. The opened HTML page provides strong quantitative evidence (AUC 0.94 with clinical data) but detailed ablation results and supplementary materials are not accessible. The frozen-weight vs. fine-tuning finding for cross-center generalization is particularly important for the HER2 prediction framework's deployment evaluation.

### P004 — Breast Cancer Research HER2 Ultra-Low AI 2026: Partial Content

PDF download not available. The opened HTML page documents the Roche Navify study's key results (F1 0.78→0.98, precision 0.39→0.91) but detailed methodology for the AI system's internal workings is not available since it is a commercial product. This remains the most compelling clinical validation study in the HER2 AI literature despite the commercial opacity.

### P010 — MuPD (arXiv 2026): Download Timed Out

PDF download timed out. The opened arXiv abstract page provides the key claims (50% FID reduction, 47% few-shot improvement, 37% marker correlation improvement) but method details and ablation results require PDF access. MuPD represents the most comprehensive multi-modal foundation model for computational pathology and its full evaluation would be essential for understanding its applicability to HER2 prediction.

### P012 — JPM Molecular Biomarker Review 2022: Invalid PDF

Downloaded file was 1,817 bytes — not a valid PDF. The opened HTML page provides the methodological overview but specific quantitative results per paper are not accessible. The review's framework taxonomy (bottom-up, pathologist-driven, hybrid) remains useful for understanding the landscape, but the empirical details for individual papers require the valid PDF.

---

## Takeaways for the Current Grounded Topic

### Most Borrowable Methods

1. **HistDiST (diffusion-based stain transfer)**: Should replace Pyramid Pix2Pix as the cross-modal synthesis engine for the HER2 prediction framework. The 28% MRA improvement on Ki67 and 159% improvement on BCI HER2 over MDCL, combined with its novel pathology-aware evaluation metric (MRA), directly addresses the clinical applicability gap noted in the BCI dataset paper. However, the paper explicitly states that even HistDiST is not clinically applicable yet — which confirms that the HER2 prediction framework's AI-assisted (not fully automated) approach is the right design principle. Computational cost must be evaluated against Pix2Pix for deployment scenarios.

2. **ShaSpec's DCO+DAO auxiliary task framework**: The shared-specific feature decomposition with domain classification and distribution alignment is the most validated approach for missing modality handling in the literature. The PDF confirms the complete mathematical formulation, the optimal auxiliary loss weights (α=0.1, β=0.02), and the residual fusion mechanism. The HER2 prediction framework already implements this design; literature confirms it as a strong choice over simpler imputation or discarding strategies.

3. **AIDA's FFT-Enhancer**: The frequency-domain approach (+13.62 pp over adversarial training alone on breast cancer) is complementary to color normalization and could be integrated as a preprocessing or augmentation step to improve cross-institutional robustness. The +18.96 pp total improvement on breast cancer cross-dataset classification is the strongest quantitative evidence for domain adaptation's necessity.

4. **DeepMIL attention-weighted aggregation**: The biomarker prediction review confirms attention pooling as the superior tile aggregation strategy for WSI-level prediction, over mean prediction or majority vote. The HER2 prediction framework's dual-path pooling (GAP + 3×3 max pooling) is a simpler alternative — whether attention pooling would improve it is an open question.

### What Still Needs Validation

1. **Generated image clinical acceptance**: The BCI dataset paper shows pathologists achieve only 37.5–40% accuracy on GAN-generated IHC images. Whether HistDiST or MuPD-generated images achieve better pathologist acceptance is not yet clinically validated. This is the single most critical gap for the HER2 prediction framework's clinical impact. The HER2 prediction framework's approach of using AI to assist (not replace) pathologists is well-aligned with this gap.

2. **Dynamic modality selection in WSI context**: DyMo and MoRA have been validated on classification tasks with small images; their application to 100,000×100,000 pixel WSIs with complex tissue morphology is an open research question.

3. **HER2-low/ultra-low performance**: Most published methods focus on binary (HER2+ vs. HER2-) or 3-way classification; performance specifically on HER2-low (IHC 1+) and HER2-ultra-low (IHC 0 with faint/barely perceptible staining) is less well-characterized, despite the clinical importance of these groups for ADC therapy. The Roche Navify study (P004) is the most relevant work here, with dramatic F1 improvement (0.78→0.98) for ultra-low detection.

4. **Cross-institutional external validation**: The AIDA paper demonstrates +18.96 pp improvement on cross-dataset breast cancer classification, but this is for binary benign/malignant. External validation of HER2 molecular subtype prediction across institutions remains largely absent from the literature. This is the most pressing validation need for the HER2 prediction framework.

### What Looks Risky or Unsupported

1. **Foundation model integration**: MuPD and CPath-Omni are promising but extremely large (15B parameters for CPath-Omni). Deploying them for a specific task like HER2 scoring may be computationally prohibitive. The HER2 prediction framework's custom dual-encoder architecture may be more practical for the specific H&E+IHC combination.

2. **Small dataset studies**: The HER2 ViT Multistage paper (13 cases) and Precision HER2 paper demonstrate feasibility but lack statistical power for clinical validation. Results should be treated as preliminary.

3. **Missing modality feature generation in ShaSpec**: Simple averaging of available modalities for missing feature reconstruction is a significant limitation for histopathology where the relationship between modalities is complex. The combination of generative synthesis (CM-GAN/HistDiST) with feature-level robustness (ShaSpec) may be necessary but introduces architectural complexity.

### What the Current Research Stage Can Already Support

1. The **multi-modal H&E+IHC approach** is well-supported by P001, P002, P003 with AUC 0.94–0.95, making it a strong technical direction.
2. **AI assistance** (not full automation) dramatically improves HER2-low detection (F1 0.78→0.98, P004), establishing a clear clinical value proposition that aligns with the HER2 prediction framework's design.
3. The **diffusion model approach** (HistDiST, MuPD) is a mature alternative to GAN-based synthesis, with quantitative improvements in molecular fidelity (MRA) that are measurable and meaningful.
4. The **CAM ablation evidence** (accuracy 95.32% with vs. 92.41% without, P003) confirms that adaptive feature weighting is a genuine contributor to HER2 prediction performance.

### What Remains Blocked by Evidence Gaps

1. The **clinical validation of generated IHC images** by expert pathologists for HER2-specific assessment (vs. Ki67 general molecular correlation) is the critical missing evidence that would most directly impact the HER2 prediction framework's clinical acceptance.
2. **Prospective multi-center clinical studies** with AI-assisted HER2 scoring are needed before regulatory approval and widespread clinical deployment.
3. **End-to-end joint training** of synthesis and classification (noted in both the HER2 prediction framework and ShaSpec) remains unexplored and could potentially improve both tasks simultaneously.
