"""
STEP NEXT-66: Build File-based Vector Index

Create chunked JSONL + embeddings for all insurers.

Usage:
    python -m scripts.build_vector_index_file_v1
"""

import json
import argparse
from pathlib import Path
from typing import List
import numpy as np
from tqdm import tqdm

from core.vector_chunk import chunk_page_jsonl, EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_VERSION
from core.vector_search_file import get_model


# Output directory
OUTPUT_DIR = Path("data/vector_index/v1")

# Document types to index (NOT 가입설계서 - that's for amounts only)
DOC_TYPES = ["약관", "사업방법서", "상품요약서"]

# Axes/insurers
AXES = [
    "samsung", "meritz", "hanwha", "heungkuk", "hyundai",
    "kb", "db", "lotte_male", "lotte_female"
]


def build_index_for_axis(axis: str, evidence_text_dir: Path, output_dir: Path):
    """
    Build vector index for a single axis.

    Args:
        axis: Insurance axis (e.g., "samsung")
        evidence_text_dir: Root directory (data/evidence_text)
        output_dir: Output directory (data/vector_index/v1)
    """
    print(f"\n=== Building index for {axis} ===")

    # Map axis to insurer directory
    if axis.startswith("lotte_"):
        axis_dir = "lotte"
    else:
        axis_dir = axis

    axis_path = evidence_text_dir / axis_dir

    if not axis_path.exists():
        print(f"SKIP: {axis_path} does not exist")
        return

    # Collect all chunks
    all_chunks = []

    for doc_type in DOC_TYPES:
        doc_type_path = axis_path / doc_type

        if not doc_type_path.exists():
            print(f"  SKIP: {doc_type_path} (not found)")
            continue

        # Find all *.page.jsonl files
        page_files = list(doc_type_path.glob("*.page.jsonl"))

        if not page_files:
            print(f"  SKIP: {doc_type} (no page.jsonl files)")
            continue

        for page_file in page_files:
            print(f"  Processing: {page_file.name} ({doc_type})")

            # Determine insurer name
            # For lotte, check if it's male/female variant
            if axis.startswith("lotte_"):
                insurer = axis.replace("_", " ").title()
            else:
                insurer = axis

            # Chunk this file
            chunks = chunk_page_jsonl(axis, insurer, doc_type, str(page_file))
            all_chunks.extend(chunks)

            print(f"    → {len(chunks)} chunks")

    if not all_chunks:
        print(f"  WARNING: No chunks generated for {axis}")
        return

    print(f"\n  Total chunks: {len(all_chunks)}")

    # Generate embeddings
    print("  Generating embeddings...")
    model = get_model()

    texts = [c.text for c in all_chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    print(f"  Embeddings shape: {embeddings.shape}")

    # Save chunks (JSONL)
    chunks_path = output_dir / f"{axis}__chunks.jsonl"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')

    print(f"  Saved: {chunks_path} ({len(all_chunks)} chunks)")

    # Save embeddings (numpy)
    embeddings_path = output_dir / f"{axis}__embeddings.npy"
    np.save(embeddings_path, embeddings)

    print(f"  Saved: {embeddings_path} ({embeddings.shape})")


def main():
    parser = argparse.ArgumentParser(description="Build file-based vector index")
    parser.add_argument(
        "--axis", type=str, default="all",
        help="Axis to build (default: all)"
    )
    parser.add_argument(
        "--evidence-dir", type=str, default="data/evidence_text",
        help="Evidence text directory"
    )
    parser.add_argument(
        "--output-dir", type=str, default="data/vector_index/v1",
        help="Output directory"
    )

    args = parser.parse_args()

    evidence_text_dir = Path(args.evidence_dir)
    output_dir = Path(args.output_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write metadata
    meta_path = output_dir / "_META.json"
    metadata = {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_version": EMBEDDING_MODEL_VERSION,
        "doc_types": DOC_TYPES,
        "axes": AXES
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Embedding Model: {EMBEDDING_MODEL_NAME} ({EMBEDDING_MODEL_VERSION})")
    print(f"Output Directory: {output_dir}")

    # Build indices
    if args.axis == "all":
        for axis in AXES:
            build_index_for_axis(axis, evidence_text_dir, output_dir)
    else:
        build_index_for_axis(args.axis, evidence_text_dir, output_dir)

    print("\n✅ Vector index build complete")


if __name__ == "__main__":
    main()
