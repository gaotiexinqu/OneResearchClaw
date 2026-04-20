# DyMo: Inference-Time Dynamic Modality Selection for Incomplete Multimodal Classification

**Source:** arXiv:2601.22853, 2026
**URL:** https://arxiv.org/abs/2601.22853
**Access date:** 2026-04-15

## Abstract

DyMo addresses the "discarding-imputation dilemma" in incomplete multimodal learning by dynamically selecting reliable recovered modalities at inference time. Rather than discarding missing modalities or imputing them, DyMo adaptively identifies task-relevant modalities for each test sample using a principled reward function based on information maximization.

## Core Innovation

The "discarding-imputation dilemma":
- **Discarding:** Missing modality → lose valuable task-relevant information
- **Imputing:** Generate missing modality → potentially introduce irrelevant noise

**DyMo's solution:** Dynamic modality selection at inference time

## Key Mechanism

1. **Information-theoretic foundation:** Establishes connection between multimodal task-relevant information and task loss
2. **Inference-time reward function:** Computes task loss as proxy for information maximization
3. **Flexible architecture:** Compatible with arbitrary modality combinations
4. **Tailored training strategy:** For robust representation learning

## Relevant to Current Topic

DyMo represents a new generation of dynamic modality handling methods that go beyond the static branch selection approach used in the HER2 prediction framework. It provides a principled information-theoretic framework for the same problem domain.

## Code Available

https://github.com/siyi-wind/DyMo

## Limitations

- Dynamic selection at inference time adds computational overhead
- Requires training strategy adaptation for each new modality combination
