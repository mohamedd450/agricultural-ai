"""CLI script to ingest PDF documents into the agricultural AI pipeline."""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for PDF ingestion pipeline."""
    parser = argparse.ArgumentParser(
        description="Ingest agricultural PDF documents into the data pipeline"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing PDF files to ingest",
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory for output artifacts (default: ./output)",
    )
    parser.add_argument(
        "--language",
        default="eng+ara",
        help="OCR language codes (default: eng+ara)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        logger.error("Input directory not found: %s", args.input_dir)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: PDF Processing
    logger.info("Step 1: Processing PDFs from %s", args.input_dir)
    from ingestion.pdf_processor import PDFProcessor
    processor = PDFProcessor()
    pages = processor.process_directory(args.input_dir)
    logger.info("Extracted %d pages", len(pages))

    if not pages:
        logger.warning("No pages extracted, exiting")
        sys.exit(0)

    # Step 2: Text Cleaning
    logger.info("Step 2: Cleaning extracted text")
    from ingestion.text_cleaner import TextCleaner
    cleaner = TextCleaner()
    for page in pages:
        page["text"] = cleaner.clean(page["text"])

    # Step 3: Semantic Chunking
    logger.info("Step 3: Chunking text")
    from processing.semantic_chunker import SemanticChunker
    chunker = SemanticChunker()
    all_chunks: list[dict] = []
    for page in pages:
        if page["text"].strip():
            chunks = chunker.chunk(page["text"])
            for chunk in chunks:
                chunk["metadata"]["source"] = page["source"]
                chunk["metadata"]["page_num"] = page["page_num"]
                chunk["metadata"]["language"] = page["language"]
            all_chunks.extend(chunks)
    logger.info("Created %d chunks", len(all_chunks))

    # Step 4: Embedding Generation
    logger.info("Step 4: Generating embeddings")
    from processing.embeddings_generator import EmbeddingsGenerator
    embedder = EmbeddingsGenerator()
    texts = [c["text"] for c in all_chunks]
    embeddings = embedder.batch_generate(texts)
    logger.info("Generated %d embeddings", len(embeddings))

    # Step 5: Vector Storage
    logger.info("Step 5: Loading vectors into Qdrant")
    from storage.qdrant_loader import QdrantLoader
    qdrant = QdrantLoader()
    qdrant.create_collection("agricultural_docs")
    payloads = [c["metadata"] for c in all_chunks]
    loaded = qdrant.load_vectors("agricultural_docs", embeddings, payloads)
    logger.info("Loaded %d vectors into Qdrant", loaded)

    logger.info("Pipeline complete. Processed %d pages into %d chunks.", len(pages), len(all_chunks))


if __name__ == "__main__":
    main()
