#!/usr/bin/env python3
"""Debug: Check raw text blocks to understand parsing failure"""

import fitz
from pathlib import Path

kb_proposal = Path("data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf")
page_idx = 1
table_bbox = (36.0, 239.0, 559.1, 760.1)

doc = fitz.open(kb_proposal)
page = doc[page_idx]
text_dict = page.get_text("dict")
blocks = text_dict["blocks"]

print("Text blocks within table bbox:\n")
count = 0
for block in blocks:
    if block.get("type") != 0:
        continue

    bx0, by0, bx1, by1 = block["bbox"]
    cx = (bx0 + bx1) / 2
    cy = (by0 + by1) / 2

    if not (36.0 <= cx <= 559.1 and 239.0 <= cy <= 760.1):
        continue

    lines = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            lines.append(span["text"])

    text_content = " ".join(lines).strip()
    if not text_content:
        continue

    row_height = by1 - by0
    print(f"Block {count + 1}:")
    print(f"  Y: [{by0:.1f}, {by1:.1f}], Height: {row_height:.1f}")
    print(f"  Text: {text_content}")
    print()

    count += 1
    if count >= 10:
        break

doc.close()
