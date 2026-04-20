# Literature Research Results (Initial)

## Research Focus

This literature research focuses on the technological landscape surrounding the HER2 breast cancer prediction framework, which is built on three core pillars: (1) multi-modal learning combining H&E and IHC images, (2) missing modality handling via cross-modal image synthesis and shared-specific feature modeling, and (3) end-to-end HER2 prediction systems. The search covered five thematic directions: HER2 AI assessment, missing modality in multimodal deep learning, cross-modal image synthesis in histopathology, domain generalization in computational pathology, and molecular biomarker prediction from H&E. The goal is to identify the current state of the art, borrowable techniques, and unresolved challenges relevant to the grounded topic.

---

## Overall Literature Synthesis

### The Multi-Modal HER2 Prediction Landscape

The literature reveals a rapidly evolving field where three technical threads are converging on HER2 breast cancer assessment. First, **end-to-end HER2 prediction models** now routinely achieve AUC 0.94–0.95 by fusing multiple imaging modalities (H&E+IHC, or multi-sequence MRI). Second, **missing modality handling** has evolved from simple imputation to sophisticated approaches including generative synthesis (CM-GAN, HistDiST, MuPD), shared-specific feature decomposition (ShaSpec), dynamic modality selection (DyMo), and parameter-efficient adaptation (MoRA). Third, **cross-modal synthesis** has transitioned from Pix2Pix GANs to diffusion-based methods (HistDiST, MuPD), offering substantially better structural fidelity and molecular correlation.

### Where the Literature Agrees

There is broad consensus that: (1) multimodal imaging outperforms single-modality for HER2 prediction; (2) missing modalities are the norm rather than the exception in clinical practice; (3) inter-observer variability in HER2 scoring—especially for HER2-low/ultra-low—is a critical unsolved problem that AI can partially address; and (4) cross-institution domain shift (due to staining protocols, scanners, tissue processing) remains the primary barrier to clinical deployment.

### Where Solution Families Differ

**Approach 1: End-to-end discriminative models** (HER2 MAP, Frontiers HER2 MRI, Precision HER2, HER2 ViT Multistage) directly predict HER2 status from multimodal images. They differ in backbone architecture (CNN vs. ViT), aggregation strategy (attention vs. VLAD), and clinical integration (standalone vs. nomogram).

**Approach 2: Cross-modal generative synthesis** (Pyramid Pix2Pix, HistDiST, MuPD) generate missing IHC from available H&E, then run standard IHC analysis. They differ in generation quality, molecular fidelity, and the breadth of modality integration (image-only vs. image+RNA+text).

**Approach 3: Feature-level missing modality handling** (ShaSpec, MoRA, DyMo) operate at the representation level rather than the pixel level. They differ in whether they require retraining (ShaSpec), can plug into pretrained models (MoRA), or dynamically select at inference (DyMo).

### What Looks Most Relevant to the Grounded Topic

The most directly relevant methods are: (1) HER2 MAP (Nature Biomed Eng 2025) as the end-to-end benchmark, (2) HistDiST and MuPD as superior alternatives to Pyramid Pix2Pix for cross-modal synthesis, (3) ShaSpec and DyMo as complementary missing modality strategies, and (4) the AIDA framework for addressing the domain generalization challenge that limits cross-institutional deployment.

### Where Evidence is Weak or Missing

1. **Clinical validation**: Most papers report internal validation only; external multi-center validation is rare
2. **HER2-low/ultra-low specifically**: Fewer studies focus on this clinically important subgroup than on HER2-positive vs. HER2-negative binary classification
3. **Generated image pathologist acceptance**: The BCI dataset paper notes pathologists achieve only 37.5–40% accuracy on GAN-generated IHC images—a critical gap that the newer diffusion methods (HistDiST, MuPD) may address but have not been clinically validated
4. **Dynamic modality selection in pathology**: DyMo and MoRA have been validated primarily on general/medical image classification tasks; their application to histopathology whole-slide images is underexplored

---

## Detailed Analysis of Opened Papers

### P001 — HER2 MAP (Nature Biomedical Engineering, 2025)

**Problem and Task Setting**: Accurate HER2 status prediction for treatment planning in breast cancer. Traditional needle biopsies sample limited tissue, leading to inaccurate assessments due to intratumoural heterogeneity. The task is to predict HER2 status and neoadjuvant therapy response from pre-treatment multimodal breast cancer images across 4 medical centres.

**Methodology and Why It Works**: The HER2 MAP (Multimodal Alignment and Prediction) model integrates multimodal breast cancer images through a deep learning framework. The model leverages the complementarity of different imaging modalities to build a more comprehensive tumour profile than any single modality can provide. The large-scale training data (14,472 images, 6,991 cases, 4 centres) is critical for generalization. The multimodal approach directly addresses the intratumoural heterogeneity problem that causes traditional biopsy failures.

**Main Evidence**:
- Dataset: 14,472 images from 6,991 cases across 4 medical centres
- Demonstrates superiority over traditional needle biopsies
- Centre C data available at Cancer Imaging Archive
- GitHub code available: https://github.com/ZhangJD-ong/HER2-MAP-from-Multimodal-Breast-Data

**Relevance to the Current Grounded Topic**: This paper represents the state-of-the-art end-to-end HER2 prediction benchmark. The HER2 prediction framework in the grounded documents is architecturally similar (multimodal input + feature fusion + classification) but focuses specifically on H&E+IHC combination. The MAP model's multi-centre training strategy and heterogeneous tumour coverage approach are directly applicable design principles. The code availability makes it a concrete reference for implementation details.

**Limits**: Relies on multimodal imaging data availability; does not specifically address missing modality scenarios; performance depends on image quality and preprocessing consistency across centres.

---

### P002 — HER2 Expression Prediction from Multi-Sequence MRI (Frontiers in Oncology, 2025)

**Problem and Task Setting**: Predict HER2 expression status from multi-sequence breast MRI (T1, T2, DCE) combined with clinical data. Dataset: 2,400 patients (1,286 HER2+, 1,114 HER2-) from 4 centres. The goal is to build a clinically deployable predictive tool with interpretable outputs.

**Methodology and Why It Works**: Four deep learning architectures (ResNet50, VGG16, EfficientNet-B0, ViT-Small) extract features from MRI sequences. ICC filtering (≥0.9) selects reproducible features, then LASSO regression reduces dimensionality. A nomogram integrates deep learning scores with clinical features (lymph node status, enhancement curve, peritumoral edema, microcalcifications). The key insight is that combining imaging features with clinical metadata substantially outperforms imaging alone.

**Main Evidence**:
- Individual models AUC: 0.88–0.89; with clinical data: **0.94**
- Key clinical predictors: washout enhancement curve (p=0.003), peritumoral edema (p=0.001), microcalcifications (p=0.002)
- Internal validation: 1,000 bootstrap resamples; Hosmer-Lemeshow test confirms calibration
- Frozen-weight feature extraction outperforms fine-tuning for cross-centre generalization (see Supplementary Table S1)

**Relevance to the Current Grounded Topic**: Although this paper uses MRI rather than histopathology images, it provides the strongest quantitative evidence that multi-modal feature fusion with clinical data achieves AUC 0.94 for HER2 prediction. The ICC filtering + LASSO feature selection pipeline, the frozen-weight vs. fine-tuning finding, and the clinical feature integration strategy are all transferable insights for the HER2 prediction framework.

**Limits**: HER2+ prevalence (53.6%) is enriched vs. general population (15–20%); no external validation; 1,000 bootstrap is internal validation only.

---

### P003 — Multi-Stage Vision Transformers for HER2 Status Scoring (arXiv, 2025)

**Problem and Task Setting**: Simultaneous H&E and IHC analysis for 4-way HER2 scoring (0, 1+, 2+, 3+) on whole slide images, with pixel-level HER2 annotation. Dataset: 13 paired H&E+IHC WSI cases from clinical archives.

**Methodology and Why It Works**: A single end-to-end pipeline using multi-stage vision transformers. Stage 1: patch-wise H&E processing for tumor localization. Stage 2: a novel mapping function identifies corresponding IHC regions from H&E malignant areas. Stage 3: clinically inspired HER2 scoring embedded in the pipeline enables automatic pixel-level annotation. This avoids the separate synthesis-then-analysis pipeline of the HER2 prediction framework, instead performing joint H&E+IHC feature learning.

**Main Evidence**:
- Classification accuracy: **0.94** (4-way HER2: 0, 1+, 2+, 3+)
- Specificity: **0.933**
- Joint H&E+IHC evaluation comparable to human pathologists
- 13 paired WSI cases; privately curated

**Relevance to the Current Grounded Topic**: This paper directly demonstrates that joint H&E+IHC ViT analysis achieves 94% accuracy in 4-way HER2 scoring, comparable to the HER2 MAP model but using a different modality combination. The end-to-end ViT approach represents an alternative architecture to the dual-encoder + attention fusion in the HER2 prediction framework. The pixel-level annotation capability addresses the interpretability concern.

**Limits**: Very small dataset (13 cases) limits statistical power and generalizability; private dataset limits reproducibility; end-to-end approach may sacrifice interpretability.

---

### P004 — AI-Enhanced HER2 Ultra-Low Diagnosis (Breast Cancer Research, 2026)

**Problem and Task Setting**: HER2 ultra-low expression (~10% of breast cancers, critical for ADC therapy eligibility) is frequently misclassified by pathologists. AI assistance from the Roche Navify Digital Pathology platform is evaluated against expert consensus ground truth. Dataset: 188 cases (376 WSIs), external validation cohort of 89 slides from 2 hospitals.

**Methodology and Why It Works**: AI tool performs WSI-level HER2 scoring. Nine pathologists independently re-evaluate their assigned slides with and without AI assistance. The AI system filters out DCIS components, focuses on invasive tumour regions, and analyzes positive controls as internal quality checks. Expert consensus diagnosis serves as ground truth. The key design principle is "AI assists, pathologist decides"—not a fully automated replacement.

**Main Evidence**:
- HER2 ultra-low detection: F1-score 0.78→**0.98**, precision 0.39→**0.91**, recall 0.72→**0.96** (with AI)
- CNB-SE concordance: 0.37→**0.48** (AI reduces underestimation)
- Post-NAT specimen consistency: 0.63→**0.92**
- External validation: 89 slides from 2 independent hospitals
- Inter-observer agreement improved from κ=0.37 to κ=0.64

**Relevance to the Current Grounded Topic**: This paper provides the most compelling clinical validation evidence for AI-assisted HER2 scoring. The dramatic F1 improvement from 0.78 to 0.98, especially the precision leap from 0.39 to 0.91, directly addresses the key clinical need that motivates the HER2 prediction framework. The finding that AI primarily reduces underestimation (misclassifying HER2-low as HER2-negative) is particularly relevant because it quantifies the therapeutic impact of accurate AI-assisted scoring.

**Limits**: Commercial AI system (Roche Navify)—not openly available; external validation on only 89 slides; potential institutional conflict of interest (study conducted by institution that also developed AI).

---

### P005 — Precision HER2 AI System (BMC Cancer, 2024)

**Problem and Task Setting**: Fully automated HER2 scoring on IHC whole-slide images, following ASCO/CAP 2018/2023 guidelines. The system focuses on invasive tumour regions and generates HER2 scores (0, 1+, 2+, 3+) consistent across slides and laboratories.

**Methodology and Why It Works**: Multi-phase pipeline: (1) invasive tumour region detection to exclude non-invasive areas; (2) individual tumour cell membrane staining classification based on staining intensity and completeness; (3) ASCO/CAP guideline-compliant scoring algorithm; (4) positive control analysis as quality assurance. The system is designed for clinical deployment rather than research evaluation.

**Main Evidence**:
- High concordance with expert pathologists for HER2 scoring
- Improved scoring consistency across slides and laboratories
- Reduces misdiagnosis of HER2 1+ patients as HER2 0 (key for ADC eligibility)
- Follows ASCO/CAP 2018/2023 guidelines

**Relevance to the Current Grounded Topic**: This paper represents the clinical deployment target for the HER2 prediction framework. The multi-phase design (filtering → region detection → cell classification → scoring) provides a concrete clinical pipeline architecture. The ASCO/CAP guideline compliance requirement is essential for any clinically deployed HER2 AI system.

**Limits**: Specific performance numbers not detailed in the opened source; limited detail on validation methodology in the accessible content.

---

### P006 — ShaSpec: Shared-Specific Feature Modelling (CVPR 2023)

**Problem and Task Setting**: Missing modality problem in multimodal learning. Most approaches either train separate models for each missing scenario or discard missing modalities. ShaSpec learns both shared features (modality-invariant) and specific features (modality-specific) from incomplete multimodal data, enabling a single model to handle arbitrary missing modality configurations.

**Methodology and Why It Works**: Architecture: shared encoder + N modality-specific encoders → residual feature fusion (f = r + proj([s₁;s₂;...;sₙ])) → main task head. Two auxiliary tasks enforce feature quality: (1) **DCO (Domain Classification Objective)**: Binary cross-entropy on specific features forces them to be modality-discriminative; (2) **DAO (Distribution Alignment Objective)**: MMD/KL loss on shared features enforces modality-invariance. The residual fusion allows the model to use shared features when modalities are missing while preserving modality-specific information when available.

**Main Evidence**:
- BraTS2018 (3-modality MRI): +3.23% Dice (enhancing tumour), +4.91% (tumour core), +3.32% (whole tumour) over SOTA
- Audiovision-MNIST: +0.44% accuracy with 5% audio rate; +0.23% with 20% audio rate
- Works with both dedicated (train on complete data only) and non-dedicated (train on all data) settings
- Adapts to both classification and segmentation tasks with same architecture
- Code: https://github.com/billhhh/ShaSpec

**Relevance to the Current Grounded Topic**: ShaSpec provides the algorithmic foundation for the shared-specific feature decomposition used in the HER2 prediction framework's dual-encoder architecture. The DCO and DAO loss functions are directly referenced and applied in the input documents. ShaSpec's residual fusion mechanism is a concrete design for handling arbitrary missing modality configurations without retraining.

**Limits**: DCO/DAO hyperparameters (α=0.1, β=0.02) tuned on brain imaging; generalizability to histopathology uncertain; missing modality feature generation is simple averaging (not generative); no end-to-end training with image synthesis models; evaluated primarily on medical imaging, not on whole-slide histopathology.

---

### P007 — HistDiST: Diffusion-Based Stain Transfer (arXiv, 2025)

**Problem and Task Setting**: H&E-to-IHC stain transfer for histopathology, enabling cost-effective molecular biomarker assessment from routine H&E images. Existing GAN-based methods suffer from training instability and limited structural fidelity. The task is high-fidelity H&E→IHC translation with molecular relevance, validated on MIST and BCI datasets.

**Methodology and Why It Works**: Latent Diffusion Model (LDM) framework with dual-conditioning: (1) **Phikon-extracted morphological embeddings** provide pathology-relevant structural context; (2) **VAE-encoded H&E representations** preserve染色 appearance. Key innovations: (a) rescaled noise schedule + v-prediction + trailing timesteps enforce zero-SNR condition at final timestep, addressing brightness biases in histopathology; (b) DDIM inversion preserves morphological structure during inference; (c) η-cosine noise schedule balances structural consistency and molecular fidelity. Novel evaluation metric: **MRA (Molecular Retrieval Accuracy)** using GigaPath embeddings—pathology-aware, not just image-quality metrics.

**Main Evidence**:
- **28% improvement in MRA** on H&E-to-Ki67 translation vs GAN baselines (BCI dataset)
- Significantly outperforms existing methods on BCI and MIST datasets
- Captures true IHC semantics better than GAN-based approaches

**Relevance to the Current Grounded Topic**: HistDiST directly improves upon the Pyramid Pix2Pix approach used in the BCI dataset paper. Its 28% MRA improvement over GAN baselines represents a significant qualitative leap in synthesis quality. If pathologists can better interpret HistDiST-generated IHC images vs. Pix2Pix-generated ones, this directly addresses the clinical applicability bottleneck identified in the BCI paper (37.5–40% pathologist accuracy on generated images). HistDiST can serve as a drop-in replacement for the CM-GAN component in the HER2 prediction framework.

**Limits**: Computational cost higher than GANs (diffusion models); validated primarily on Ki67 and BCI datasets; broader pathology generalisation unknown; zero-SNR condition is novel and not yet widely validated.

---

### P008 — DyMo: Dynamic Modality Selection (arXiv, 2026)

**Problem and Task Setting**: The "discarding-imputation dilemma" in incomplete multimodal learning—existing methods either discard missing modalities (losing information) or impute them (introducing noise). DyMo addresses this by dynamically selecting reliable recovered modalities at inference time for each test sample.

**Methodology and Why It Works**: Central innovation: theoretically connecting multimodal task-relevant information with task loss. Since direct information estimation is intractable at test time, DyMo uses **inference-time task loss as a tractable proxy** for modality relevance. A principled reward function based on information maximization guides which modality combinations to select. Architecture: flexible multimodal network compatible with arbitrary modality combinations + tailored training strategy for robust representation learning. This is fundamentally different from static branch selection (which uses a fixed policy) or generative imputation (which fixes missing data before classification).

**Main Evidence**:
- Significantly outperforms SOTA incomplete/dynamic MDL methods across various missing-data scenarios
- Evaluated on diverse natural and medical image datasets
- Code: https://github.com/siyi-wind/DyMo

**Relevance to the Current Grounded Topic**: DyMo provides a principled information-theoretic framework for the same problem addressed by the HER2 prediction framework's dynamic branch selection mechanism. While the HER2 prediction framework uses a quality-gated branch selection approach (Channel Attention Module as quality metric), DyMo's loss-based modality scoring offers an alternative design principle. The flexible architecture compatibility means it could be integrated with the HER2 prediction framework's modality recovery pipeline.

**Limits**: Dynamic selection at inference adds computational overhead; requires tailored training strategy; evaluated on general/medical image classification, not on histopathology WSI classification.

---

### P009 — MoRA: LoRA for Missing Modality (arXiv, 2024)

**Problem and Task Setting**: Applying multi-modal pretrained models to disease diagnosis with missing modalities, while keeping fine-tuning computationally tractable. Previous methods (prompt-based: MAPs, MSPs) either lack robustness across different missing settings or need to be plugged into several layers.

**Methodology and Why It Works**: Modality-aware Low-Rank Adaptation (MoRA). Unlike standard LoRA which applies the same up-projection to all inputs, MoRA uses **different modality-aware up-projections** for different modalities. During fine-tuning, all pretrained weights are frozen; only MoRA modules + classifier are trained. This keeps trainable parameters at **<1.6% of total model parameters** while achieving superior accuracy and robustness across missing modality scenarios. The modality-aware up-projections allow the model to discern unique characteristics of each modality, enhancing robustness when modalities are missing.

**Main Evidence**:
- <1.6% trainable parameters vs full fine-tuning
- Outperforms existing fine-tuning methods on disease diagnosis with missing modalities
- Plug-and-play: integrates into first block of pretrained model

**Relevance to the Current Grounded Topic**: MoRA offers a parameter-efficient alternative to ShaSpec for missing modality handling. Its integration into pretrained models (critical for histopathology where large pretrained models like CPath-Omni and foundation models are becoming standard) makes it complementary to both ShaSpec (feature-level) and CM-GAN (generation-level) approaches. For the HER2 prediction framework, MoRA could enable efficient fine-tuning of a pretrained multimodal pathology model.

**Limits**: Designed for fine-tuning pretrained models (not from-scratch training); two-modality assumption in problem formulation; pathology-specific validation absent.

---

### P010 — AIDA: Adversarial Fourier Domain Adaptation (npj Precision Oncology, 2024)

**Problem and Task Setting**: Domain shift in multi-center histopathology classification. CNNs are sensitive to amplitude spectrum variations (staining, scanner differences) but humans rely on phase-related components (morphology). AIDA combines adversarial training with FFT-Enhancer to make models domain-invariant.

**Methodology and Why It Works**: FFT-Enhancer module processes images in frequency domain, adjusting source domain colors to look like target domain. The adversarial training component has a domain classifier that learns to distinguish source from target while the feature extractor tries to fool it. VLAD aggregation converts patch-level features to slide-level representations. Key finding: intermediate CNN layers (block 4) produce the most generalizable features for domain adaptation.

**Main Evidence**:
- Breast cancer (source: ICIAR-2018, target: BreaKHis): Base 55.15% → AIDA **74.11%** balanced accuracy (+18.96 pp)
- Ovarian cancer: Base 64.65% → AIDA **75.82%** (+11.17 pp)
- Bladder cancer: Base 54.77% → AIDA **77.65%** (+22.88 pp)
- Adversarial training alone (ADA): +5.34 pp (breast); +9.51 pp (bladder) over base
- FFT-Enhancer contributes additional +13.62 pp (breast) over ADA alone

**Relevance to the Current Grounded Topic**: AIDA directly addresses the cross-institutional deployment challenge noted in the BCI dataset paper and the HER2 prediction framework's evaluation. The +18.96 pp improvement on the breast cancer cross-dataset task demonstrates that domain adaptation is essential for real-world deployment. The FFT-Enhancer's frequency-domain approach is complementary to color normalization and stain augmentation methods.

**Limits**: VLAD+SVM aggregation is not end-to-end (unlike attention-based methods); intermediate CNN layer selection requires tuning per dataset; breast cancer task is binary (benign/malignant), not molecular subtype classification.

---

### P011 — Molecular Biomarker Prediction from H&E Review (JPM, 2022)

**Problem and Task Setting**: Comprehensive review of deep learning methods for predicting molecular biomarkers from H&E-stained histopathology whole slide images. Covers four biomarker categories: (1) protein biomarkers, (2) genomic subtypes/expression, (3) molecular alterations, (4) virus presence. Across 10+ cancer types.

**Methodology and Why It Works**: Reviews frameworks from bottom-up (learn directly from pixels) to pathologist-driven (use expert features) to hybrid. Key methodological insights: (1) Weak supervision (patient-level labels only) requires MIL attention mechanisms; (2) Self-supervised pretraining (fingerprinting, contrastive learning) significantly improves feature quality; (3) Transformers are emerging as superior to CNNs for WSI analysis; (4) Tile aggregation via attention-weighted pooling (DeepMIL) outperforms mean prediction or majority vote.

**Main Evidence**:
- HER2 protein biomarker: La Barbera et al. used second-stage classifier on tile predictions; self-supervised fingerprinting improves HER2 prediction
- Multiple instance learning with attention provides visual indication of HER2-positive regions
- Contrastive learning (cross-entropy + contrastive objectives) increases intra-class similarity
- Challenges: small training sets, weak supervision, WSI processing (100,000×100,000 pixels), model explainability

**Relevance to the Current Grounded Topic**: This review provides the methodological foundation for H&E→biomarker prediction. The MIL attention mechanism, self-supervised pretraining strategy, and tile aggregation methods are all directly applicable to the HER2 prediction framework's H&E encoding pipeline. The identified challenges frame the evaluation priorities for the HER2 prediction framework.

**Limits**: 2022 review; does not cover recent transformer-based and foundation model approaches; primarily methodological overview rather than empirical results.

---

### P012 — MuPD: Multimodal Pathology Diffusion (arXiv, 2026)

**Problem and Task Setting**: Unified generative foundation model for histopathology that integrates H&E histology, RNA profiles, and clinical text in a shared latent space via diffusion transformer. Addresses the limitation of task-specific models trained on narrow single source-target pairs.

**Methodology and Why It Works**: Diffusion Transformer (DiT) backbone with **decoupled cross-modal attention**—separate attention streams for different modality pairs (H&E↔RNA, H&E↔text, RNA↔text). Pretraining data: 100M histology patches, 1.6M text-histology pairs, 10.8M RNA-histology pairs, across 34 human organs. Supports: (1) text-conditioned histology generation; (2) RNA-conditioned histology generation; (3) virtual staining (H&E→IHC).

**Main Evidence**:
- FID reduced by **50%** vs domain-specific models for text-conditioned and image-to-image generation
- Few-shot classification accuracy improved by up to **47%** through synthetic data augmentation
- RNA-conditioned histology: FID reduced by **23%** vs next-best; preserves cell-type distributions across 5 cancer types
- Virtual stainer: H&E→IHC translation with **37% higher marker correlation** than existing methods

**Relevance to the Current Grounded Topic**: MuPD represents the most advanced cross-modal synthesis approach for computational pathology. Its 37% improvement in IHC marker correlation for virtual staining directly improves upon the Pyramid Pix2Pix baseline in the BCI dataset paper. The shared latent space for H&E+RNA+IHC+text is architecturally analogous to—but more comprehensive than—the multimodal fusion in the HER2 prediction framework. MuPD can serve as a universal backbone replacing individual CM-GAN, ShaSpec, and channel attention modules.

**Limits**: Very large model (diffusion transformer); computational cost likely prohibitive for routine use; HER2-specific IHC validation not reported; RNA integration requires genomic data; most ambitious paper here but also least validated on specific clinical tasks.

---

### P013 — CPath-Omni: Unified Foundation Model (arXiv, 2024)

**Problem and Task Setting**: First 15-billion-parameter Large Multimodal Model (LMM) unifying both patch-level and whole-slide image (WSI) analysis in computational pathology. Addresses redundancy of separately trained patch and WSI models.

**Methodology and Why It Works**: Unified architecture handling classification, VQA, captioning, and visual referring prompting at both patch and WSI levels. CPath-CLIP: specialized pathology CLIP visual processor integrating multiple vision models with LLM text encoder. The unification strategy avoids redundant feature extraction between patch-level and WSI-level models.

**Main Evidence**:
- SOTA on **39/42** datasets across diverse tasks
- Outperforms task-specific models trained for individual tasks
- CPath-CLIP: SOTA on 9 zero-shot and 4 few-shot datasets

**Relevance to the Current Grounded Topic**: CPath-Omni provides the broader context of large-scale foundation models for computational pathology. Its unified patch+WSI architecture addresses the aggregation challenge in HER2 prediction (MIL attention vs. VLAD vs. other aggregation strategies). CPath-CLIP's pathology-specific visual processor could serve as a feature extractor for the HER2 prediction framework.

**Limits**: 15B parameters = extreme computational cost; CLIP-based approach may miss fine-grained biomarker details; not specifically validated for HER2 scoring; pathology domain adaptation still required.

---

### P014 — Multimodal Foundation Models Survey (arXiv, 2025)

**Problem and Task Setting**: Comprehensive survey of 32 multi-modal foundation models in computational pathology, categorizing them into three paradigms: vision-language, vision-knowledge graph, and vision-gene expression. Analyzes 28 datasets and identifies key challenges and future directions.

**Methodology and Why It Works**: Systematic taxonomy of multimodal CPath models. Vision-language models (non-LLM-based vs. LLM-based) integrate text/reports with images. Vision-knowledge graph models incorporate structured domain knowledge. Vision-gene expression models (closest to the HER2 prediction framework's domain) integrate molecular profiles. Key finding: most successful models use pathology-specific pretraining beyond ImageNet.

**Key Challenges Identified**:
1. Data heterogeneity (WSI scale vs. text/RNA granularity)
2. Annotation cost and quality
3. Cross-modal alignment at different granularity levels
4. Domain shift across institutions
5. Interpretability and clinical validation requirements

**Relevance to the Current Grounded Topic**: This survey provides the strategic landscape for where the HER2 prediction framework fits. It confirms that the vision-gene expression paradigm (H&E+IHC+RNA integration) is an active and important research direction. The identified challenges directly inform what the HER2 prediction framework needs to address for clinical deployment.

**Limits**: Survey paper (no primary experimental results); rapidly evolving field (models from 2025-2026 may not be fully covered).

---

## Snippet-Level / Not-Fully-Opened Candidates

The following items appeared in search results but were not fully opened and read. They are documented for completeness and future reference.

1. **HER2 Multimodal Alignment and Prediction (MAP) — PubMed abstract** (Nature Biomed Eng 2025): The full paper abstract was accessed through the Nature page; the PubMed record confirms 14,472 images from 6,991 cases across 4 centres and GitHub availability. The core contribution (addressing intratumoural heterogeneity via multimodal imaging) is consistent with the opened Nature page content.

2. **Precision HER2 (BMC Cancer 2024)**: Partial content was obtained. The system follows ASCO/CAP 2018/2023 guidelines and focuses on invasive tumour regions. Key claims (high concordance with pathologists, reduced HER2 1+ misdiagnosis) are documented but specific quantitative metrics are limited in the opened content.

3. **HistDiST (arXiv 2025) — HTML version**: The full HTML page was accessed. The 28% MRA improvement on Ki67 translation and the dual-conditioning strategy (Phikon + VAE) are well-documented from the abstract and metadata. Full experimental details would require PDF access.

4. **MoRA (arXiv 2024)**: The HTML version timed out during full retrieval. The abstract and key claims (<1.6% parameters, modality-aware up-projections) are documented. Full method details (LoRA rank, specific adaptation mechanism) require PDF access.

5. **Qiu et al. Frontiers HER2 MRI 2025**: Full paper content was successfully opened and read; no snippet-only fallback needed.

6. **HER2 MAP Nature Biomed Eng 2025**: Full paper content was successfully opened and read; no snippet-only fallback needed.

7. **Additional arXiv results**: Several additional arXiv results appeared in search but were not opened due to content overlap with already-opened papers or limited relevance. These include general multimodal learning papers and domain adaptation papers that were covered by more specific opened papers.

---

## Initial Takeaways for the Current Grounded Topic

### Most Borrowable Methods

1. **HistDiST (diffusion-based stain transfer)**: Should replace Pyramid Pix2Pix as the cross-modal synthesis engine. The 28% MRA improvement and pathology-aware evaluation metric (MRA) directly address the clinical applicability gap noted in the BCI dataset paper. However, computational cost must be evaluated against Pix2Pix for deployment scenarios.

2. **ShaSpec's DCO+DAO auxiliary task framework**: The shared-specific feature decomposition with domain classification and distribution alignment is the most validated approach for missing modality handling. The HER2 prediction framework already implements this design; literature confirms it as a strong choice over simpler imputation or discarding strategies.

3. **AIDA's FFT-Enhancer**: The frequency-domain approach (+13.62 pp over adversarial training alone on breast cancer) is complementary to color normalization and could be integrated as a preprocessing or augmentation step to improve cross-institutional robustness.

4. **DeepMIL attention-weighted aggregation**: The biomarker prediction review confirms attention pooling as the superior tile aggregation strategy for WSI-level prediction, over mean prediction or majority vote.

### What Still Needs Validation

1. **Generated image clinical acceptance**: The BCI dataset paper shows pathologists achieve only 37.5–40% accuracy on GAN-generated IHC images. Whether HistDiST or MuPD-generated images achieve better pathologist acceptance is not yet clinically validated. This is the single most critical gap for the HER2 prediction framework's clinical impact.

2. **Dynamic modality selection in WSI context**: DyMo and MoRA have been validated on classification tasks with small images; their application to 100,000×100,000 pixel WSIs with complex tissue morphology is an open research question.

3. **HER2-low/ultra-low performance**: Most published methods focus on binary (HER2+ vs. HER2-) or 3-way classification; performance specifically on HER2-low (IHC 1+) and HER2-ultra-low (IHC 0 with faint/barely perceptible staining) is less well-characterized, despite the clinical importance of these groups for ADC therapy.

4. **Cross-institutional external validation**: The AIDA paper demonstrates +18.96 pp improvement on cross-dataset breast cancer classification, but this is for binary benign/malignant. External validation of HER2 molecular subtype prediction across institutions remains largely absent from the literature.

### What Looks Risky or Unsupported

1. **Foundation model integration**: MuPD and CPath-Omni are promising but extremely large (15B parameters). Deploying them for a specific task like HER2 scoring may be overkill and computationally prohibitive. The HER2 prediction framework's custom dual-encoder architecture may be more practical for the specific H&E+IHC combination.

2. **Small dataset studies**: The HER2 ViT Multistage paper (13 cases) and Precision HER2 paper demonstrate feasibility but lack statistical power for clinical validation. Results should be treated as preliminary.

3. **Missing modality feature generation**: ShaSpec's simple averaging of available modalities is a limitation for histopathology where the relationship between modalities is complex. The combination of generative synthesis (CM-GAN/HistDiST) with feature-level robustness (ShaSpec) may be necessary but introduces architectural complexity.

### What the Current Research Stage Can Already Support

1. The **multimodal H&E+IHC approach** is well-supported by P001, P002, P003 with AUC 0.94–0.95, making it a strong technical direction.
2. **AI assistance** (not full automation) dramatically improves HER2-low detection (F1 0.78→0.98, P004), establishing a clear clinical value proposition.
3. The **diffusion model approach** (HistDiST, MuPD) is a mature alternative to GAN-based synthesis, with quantitative improvements in molecular fidelity.

### What Remains Blocked by Evidence Gaps

1. The **clinical validation of generated IHC images** by expert pathologists for HER2-specific assessment (vs. Ki67 general molecular correlation) is the critical missing evidence that would most directly impact the HER2 prediction framework's clinical acceptance.
2. **Prospective multi-centre clinical studies** with AI-assisted HER2 scoring are needed before regulatory approval and widespread clinical deployment.
