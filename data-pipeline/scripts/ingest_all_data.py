"""Main data ingestion orchestration script.

Runs the complete Agricultural AI data pipeline:
    PDF documents → OCR/text extraction → cleaning → semantic chunking
    → embeddings → Qdrant vector store + Neo4j knowledge graph
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Allow running from repo root or data-pipeline/ directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.pdf_processor import PDFProcessor
from ingestion.text_cleaner import TextCleaner
from processing.embeddings_generator import EmbeddingsGenerator
from processing.graph_extractor import GraphExtractor
from processing.semantic_chunker import SemanticChunker
from storage.neo4j_loader import Neo4jLoader
from storage.qdrant_loader import QdrantLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_all_data")


# ── Pipeline configuration ────────────────────────────────────────────────


def _build_config_from_env() -> dict:
    """Build pipeline configuration from environment variables."""
    return {
        "qdrant_host":       os.getenv("QDRANT_HOST", "localhost"),
        "qdrant_port":       int(os.getenv("QDRANT_PORT", "6333")),
        "qdrant_collection": os.getenv("QDRANT_COLLECTION", "agricultural_knowledge"),
        "neo4j_uri":         os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "neo4j_user":        os.getenv("NEO4J_USER", "neo4j"),
        "neo4j_password":    os.getenv("NEO4J_PASSWORD", ""),
        "embedding_model":   os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        "chunk_size":        int(os.getenv("CHUNK_SIZE", "512")),
        "chunk_overlap":     int(os.getenv("CHUNK_OVERLAP", "50")),
        "language":          os.getenv("PIPELINE_LANGUAGE", "ar"),
        "ocr_enabled":       os.getenv("OCR_ENABLED", "true").lower() == "true",
        "batch_size":        int(os.getenv("EMBED_BATCH_SIZE", "32")),
    }


# ── Core pipeline ─────────────────────────────────────────────────────────


async def run_pipeline(source_dir: str, config: dict) -> dict:
    """Execute the full ingestion pipeline.

    Parameters
    ----------
    source_dir:
        Directory containing PDF files to ingest.
    config:
        Pipeline configuration dictionary.

    Returns
    -------
    dict
        Summary with ``pages``, ``chunks``, ``embeddings``,
        ``qdrant_loaded``, ``entities``, and ``relationships`` counts.
    """
    stats: dict = {
        "pages": 0,
        "chunks": 0,
        "embeddings": 0,
        "qdrant_loaded": 0,
        "entities": 0,
        "relationships": 0,
    }

    # ── Step 1: extract text from PDFs ───────────────────────────────────
    logger.info("Step 1/5 – Extracting text from PDFs in '%s'", source_dir)
    pdf_processor = PDFProcessor(ocr_enabled=config["ocr_enabled"])
    pages = await pdf_processor.process_directory(source_dir)
    stats["pages"] = len(pages)
    logger.info("Extracted %d pages", stats["pages"])

    if not pages:
        logger.warning("No pages extracted – pipeline complete with no output")
        return stats

    # ── Step 2: clean and chunk text ─────────────────────────────────────
    logger.info("Step 2/5 – Cleaning and chunking text")
    cleaner = TextCleaner(normalize_arabic=True)
    chunker = SemanticChunker(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        language=config["language"],
    )

    all_chunks: list[dict] = []
    for page in pages:
        cleaned = cleaner.clean(page["text"])
        if not cleaned:
            continue
        page_chunks = chunker.chunk_text(cleaned, page["metadata"])
        all_chunks.extend(page_chunks)

    stats["chunks"] = len(all_chunks)
    logger.info("Created %d chunks", stats["chunks"])

    # ── Step 3: generate embeddings ───────────────────────────────────────
    logger.info("Step 3/5 – Generating embeddings")
    embedder = EmbeddingsGenerator(model_name=config["embedding_model"])
    texts = [c["text"] for c in all_chunks]

    # Process in batches to limit memory usage
    batch_size = config.get("batch_size", 32)
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = await embedder.generate(batch)
        all_embeddings.extend(batch_embeddings)

    stats["embeddings"] = len(all_embeddings)
    logger.info("Generated %d embeddings", stats["embeddings"])

    # ── Step 4: load into Qdrant ──────────────────────────────────────────
    logger.info("Step 4/5 – Loading into Qdrant")
    qdrant = QdrantLoader(
        host=config["qdrant_host"],
        port=config["qdrant_port"],
        collection_name=config["qdrant_collection"],
    )
    await qdrant.initialize()
    loaded = await qdrant.load_documents(all_chunks, all_embeddings)
    await qdrant.close()
    stats["qdrant_loaded"] = loaded
    logger.info("Loaded %d documents into Qdrant", loaded)

    # ── Step 5: build knowledge graph in Neo4j ───────────────────────────
    logger.info("Step 5/5 – Building knowledge graph in Neo4j")
    extractor = GraphExtractor()
    neo4j = Neo4jLoader(
        uri=config["neo4j_uri"],
        user=config["neo4j_user"],
        password=config["neo4j_password"],
    )
    await neo4j.connect()

    total_entities = 0
    total_relationships = 0
    for page in pages:
        cleaned = cleaner.clean(page["text"])
        if not cleaned:
            continue
        entities = await extractor.extract_entities(cleaned)
        relationships = await extractor.extract_relationships(cleaned, entities)
        total_entities += await neo4j.load_entities(entities)
        total_relationships += await neo4j.load_relationships(relationships)

    await neo4j.close()
    stats["entities"] = total_entities
    stats["relationships"] = total_relationships
    logger.info(
        "Knowledge graph: %d entities, %d relationships",
        total_entities,
        total_relationships,
    )

    return stats


# ── CLI ───────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agricultural AI – Data Ingestion Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "source_dir",
        help="Directory containing PDF files to ingest",
    )
    parser.add_argument(
        "--language",
        default=os.getenv("PIPELINE_LANGUAGE", "ar"),
        choices=["ar", "en"],
        help="Primary language of the source documents",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=int(os.getenv("CHUNK_SIZE", "512")),
        help="Target character length for each text chunk",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=int(os.getenv("CHUNK_OVERLAP", "50")),
        help="Character overlap between consecutive chunks",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("EMBED_BATCH_SIZE", "32")),
        help="Number of texts per embedding batch",
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()
    config = _build_config_from_env()

    # CLI args override env vars
    config["language"] = args.language
    config["chunk_size"] = args.chunk_size
    config["chunk_overlap"] = args.chunk_overlap
    config["batch_size"] = args.batch_size

    logger.info("=" * 60)
    logger.info("Agricultural AI – Data Ingestion Pipeline")
    logger.info("Source directory : %s", args.source_dir)
    logger.info("Language         : %s", config["language"])
    logger.info("Chunk size       : %d", config["chunk_size"])
    logger.info("=" * 60)

    stats = await run_pipeline(args.source_dir, config)

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("  Pages extracted   : %d", stats["pages"])
    logger.info("  Chunks created    : %d", stats["chunks"])
    logger.info("  Embeddings        : %d", stats["embeddings"])
    logger.info("  Qdrant documents  : %d", stats["qdrant_loaded"])
    logger.info("  Graph entities    : %d", stats["entities"])
    logger.info("  Graph relations   : %d", stats["relationships"])
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
