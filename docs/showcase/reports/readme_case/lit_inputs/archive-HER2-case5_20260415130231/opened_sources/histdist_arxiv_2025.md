# HistDiST: Histopathological Diffusion-based Stain Transfer

**Source:** arXiv:2505.06793
**URL:** https://arxiv.org/abs/2505.06793
**Access date:** 2026-04-15

## Abstract

HistDiST is a Latent Diffusion Model (LDM) framework for high-fidelity H&E-to-IHC stain transfer. It introduces a dual-conditioning strategy using Phikon-extracted morphological embeddings and VAE-encoded H&E representations. Key innovations include a rescaled noise schedule, v-prediction, and zero-SNR condition. Evaluated on MIST and BCI datasets, it achieves 28% improvement in MRA (Molecular Retrieval Accuracy) on H&E-to-Ki67 translation over GAN baselines.

## Key Technical Innovations

1. **Dual-conditioning:** Phikon morphological embeddings + VAE-encoded H&E → pathology-relevant context + structural consistency
2. **Rescaled noise schedule:** Addresses brightness biases in histopathology images
3. **v-prediction + trailing timesteps:** Zero-SNR condition at final timestep
4. **DDIM inversion:** Preserves morphological structure during inference
5. **Molecular Retrieval Accuracy (MRA):** Novel pathology-aware metric using GigaPath embeddings

## Performance

- 28% improvement in MRA on H&E-to-Ki67 translation vs GAN baselines
- Significantly outperforms existing methods on BCI dataset
- Captures true IHC semantics better than GAN-based approaches

## Relevance to Current Topic

HistDiST represents the next generation of cross-modal synthesis methods, directly improving upon the Pyramid Pix2Pix approach used in the BCI dataset paper. Its superior synthesis quality could directly enhance the CM-GAN component of the HER2 prediction framework.

## Code Available

GitHub link referenced in paper (to be confirmed)

## Limitations

- Computational cost of diffusion models higher than GANs
- Evaluated primarily on Ki67 and BCI datasets; broader pathology generalisation unknown
- Zero-SNR condition is novel; not yet widely validated
