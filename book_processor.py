"""CLI script to process agricultural books into JSON knowledge artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.book_processing.pipeline import BookProcessingPipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process books to structured JSON knowledge.")
    parser.add_argument("--input", required=True, help="Input file or directory containing books")
    parser.add_argument("--output", default="data/json_output", help="Directory for generated JSON files")
    parser.add_argument("--embeddings", default="data/embeddings", help="Directory for generated embeddings")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = BookProcessingPipeline().process(
        input_path=args.input,
        output_dir=args.output,
        embeddings_dir=args.embeddings,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
