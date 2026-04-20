#!/usr/bin/env python
import fitz
import json
import sys
from datetime import datetime, timezone, timedelta
import os

def extract_pdf_content(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for i, page in enumerate(doc):
        full_text += f"\n--- Page {i+1} ---\n"
        full_text += page.get_text()
    doc.close()
    return full_text

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    # Generate ground_id
    doc_id = os.path.basename(input_path).rsplit('.', 1)[0]
    doc_id = doc_id.replace(' ', '-').replace('/', '_')
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d%H%M%S")
    ground_id = f"pdf-{doc_id}_{timestamp}"

    bundle_dir = os.path.join(output_dir, ground_id)
    os.makedirs(bundle_dir, exist_ok=True)

    # Write ground_id.txt
    with open(os.path.join(bundle_dir, "ground_id.txt"), "w") as f:
        f.write(ground_id)

    # Extract content
    content = extract_pdf_content(input_path)

    # Write extracted.md
    with open(os.path.join(bundle_dir, "extracted.md"), "w", encoding="utf-8") as f:
        f.write(content)

    # Write extracted_meta.json
    meta = {
        "source": input_path,
        "doc_id": doc_id,
        "ground_id": ground_id,
        "extracted_at": datetime.now(timezone.utc).isoformat()
    }
    with open(os.path.join(bundle_dir, "extracted_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Write asset_index.json (empty for PDF)
    asset_index = {"assets": []}
    with open(os.path.join(bundle_dir, "asset_index.json"), "w", encoding="utf-8") as f:
        json.dump(asset_index, f, indent=2)

    print(f"[OK] Bundle written to: {bundle_dir}")
    print(f"[OK] Ground ID: {ground_id}")
