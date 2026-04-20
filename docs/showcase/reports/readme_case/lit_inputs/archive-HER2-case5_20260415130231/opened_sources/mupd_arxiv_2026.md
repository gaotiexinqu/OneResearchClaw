# MuPD: A Generative Foundation Model for Multimodal Histopathology

**Source:** arXiv:2604.03635, 2026
**URL:** https://arxiv.org/abs/2604.03635
**Access date:** 2026-04-15

## Abstract

MuPD (Multimodal Pathology Diffusion) is a generative foundation model that embeds H&E histology, RNA profiles, and clinical text into a shared latent space via a diffusion transformer with decoupled cross-modal attention. Pretrained on 100M histology patches, 1.6M text-histology pairs, and 10.8M RNA-histology pairs across 34 organs. Supports cross-modal synthesis without task-specific fine-tuning.

## Key Capabilities

1. **Text-conditioned histology generation:** Generate histology from text descriptions
2. **Image-to-image generation:** FID reduced by 50% vs domain-specific models
3. **RNA-conditioned histology:** FID reduced by 23% vs next-best; preserves cell-type distributions
4. **Virtual stainer:** H&E → IHC translation with 37% higher marker correlation than existing methods

## Architecture

- **Diffusion Transformer (DiT)** backbone
- **Decoupled cross-modal attention:** Separate attention streams for different modality pairs
- **Shared latent space:** H&E, RNA, text unified in one embedding
- **Pretraining data:** 34 human organs

## Relevance to Current Topic

MuPD represents the next-generation unified approach to cross-modal synthesis in computational pathology. Its superior virtual staining capability (37% improvement over existing methods) could directly replace the Pyramid Pix2Pix approach in the BCI dataset paper. Its H&E→IHC translation aligns directly with the CM-GAN component of the HER2 prediction framework.

## Limitations

- Very large model (diffusion transformer); computational cost likely high
- RNA integration requires genomic data which may not always be available
- Virtual stainer quality on HER2-specific IHC not specifically validated
