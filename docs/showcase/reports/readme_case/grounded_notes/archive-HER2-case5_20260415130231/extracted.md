# Archive Extraction Bundle

## Archive Overview
- Source archive: /root/autodl-tmp/.autodl/video2report/One-Research/docs/showcase/inputs/case5/HER2-case5.zip
- Ground ID: archive-HER2-case5_20260415130231
- Total files discovered: 4
- Supported files: 4
- Unsupported files: 0
- Skipped hidden/system files: 0
- Child grounding outputs for supported files should be written under `child_outputs/` inside this archive bundle.

## File Inventory
- `HER2/1.md` | type=document | supported=true | recommended_skill=document-grounding
- `HER2/11.pdf` | type=document | supported=true | recommended_skill=document-grounding
- `HER2/Liu 等 - 2022 - BCI Breast Cancer Immunohistochemical Image Generation through Pyramid Pix2pix.pdf` | type=document | supported=true | recommended_skill=document-grounding
- `HER2/Wang 等 - 2023 - Multi-Modal Learning with Missing Modality via Shared-Specific Feature Modelling.pdf` | type=document | supported=true | recommended_skill=document-grounding

## Supported Items and Recommended Child Output Paths
- `HER2/1.md` -> document-grounding | status=pending_child_grounding | child_output_path=child_outputs/doc-1
- `HER2/11.pdf` -> document-grounding | status=pending_child_grounding | child_output_path=child_outputs/doc-11
- `HER2/Liu 等 - 2022 - BCI Breast Cancer Immunohistochemical Image Generation through Pyramid Pix2pix.pdf` -> document-grounding | status=pending_child_grounding | child_output_path=child_outputs/doc-Liu__-_2022_-_BCI_Breast_Cancer_Immunohistochemical_Image_Generation_through_Pyramid_Pix2pix
- `HER2/Wang 等 - 2023 - Multi-Modal Learning with Missing Modality via Shared-Specific Feature Modelling.pdf` -> document-grounding | status=pending_child_grounding | child_output_path=child_outputs/doc-Wang__-_2023_-_Multi-Modal_Learning_with_Missing_Modality_via_Shared-Specific_Feature_Modelling

## Skipped / Unsupported Items
- None

## Next Step for the Agent
- Read `routed_items.json` and run the recommended existing child skill for each supported file.
- Write each child grounding output under the current archive bundle's `child_outputs/` directory, not the global grounding root.
- Only after child bundles are produced should you write a real archive-level `grounded.md`.
