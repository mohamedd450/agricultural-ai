"""CLI script to build agricultural knowledge graph from extracted text."""

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
    """Main entry point for knowledge graph building pipeline."""
    parser = argparse.ArgumentParser(
        description="Build agricultural knowledge graph from extracted text"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing extracted text files or PDFs",
    )
    parser.add_argument(
        "--neo4j-uri",
        default="bolt://localhost:7687",
        help="Neo4j connection URI (default: bolt://localhost:7687)",
    )
    parser.add_argument(
        "--neo4j-user",
        default="neo4j",
        help="Neo4j username (default: neo4j)",
    )
    parser.add_argument(
        "--neo4j-password",
        default="password",
        help="Neo4j password (default: password)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        logger.error("Input directory not found: %s", args.input_dir)
        sys.exit(1)

    # Step 1: Load text from PDFs
    logger.info("Step 1: Loading text from %s", args.input_dir)
    from ingestion.pdf_processor import PDFProcessor
    from ingestion.text_cleaner import TextCleaner

    processor = PDFProcessor()
    cleaner = TextCleaner()
    pages = processor.process_directory(args.input_dir)

    all_text = ""
    for page in pages:
        cleaned = cleaner.clean(page["text"])
        if cleaned.strip():
            all_text += cleaned + "\n\n"

    if not all_text.strip():
        logger.warning("No text extracted, exiting")
        sys.exit(0)

    logger.info("Loaded text from %d pages", len(pages))

    # Step 2: Entity Extraction
    logger.info("Step 2: Extracting entities")
    from processing.graph_extractor import GraphExtractor
    extractor = GraphExtractor()
    entities = extractor.extract_entities(all_text)
    logger.info("Extracted %d entities", len(entities))

    # Step 3: Relationship Extraction
    logger.info("Step 3: Extracting relationships")
    relationships = extractor.extract_relationships(all_text, entities)
    logger.info("Extracted %d relationships", len(relationships))

    # Step 4: Neo4j Loading
    logger.info("Step 4: Loading into Neo4j at %s", args.neo4j_uri)
    from storage.neo4j_loader import Neo4jLoader
    neo4j = Neo4jLoader(
        uri=args.neo4j_uri,
        user=args.neo4j_user,
        password=args.neo4j_password,
    )
    counts = neo4j.batch_load({"entities": entities, "relationships": relationships})
    neo4j.close()
    logger.info("Neo4j: loaded %d entities, %d relationships", counts["entities"], counts["relationships"])

    # Step 5: EdgeQuake Indexing
    logger.info("Step 5: Indexing in EdgeQuake")
    from storage.edgequake_indexer import EdgeQuakeIndexer
    indexer = EdgeQuakeIndexer()
    documents = [
        {"id": e["id"], "text": e["name"], "metadata": {"type": e["type"]}}
        for e in entities
    ]
    indexed = indexer.batch_index(documents)
    indexer.build_graph_index()
    logger.info("EdgeQuake: indexed %d documents", indexed)

    # Summary
    logger.info("=" * 50)
    logger.info("Knowledge Graph Build Summary")
    logger.info("  Pages processed: %d", len(pages))
    logger.info("  Entities extracted: %d", len(entities))
    logger.info("  Relationships extracted: %d", len(relationships))
    logger.info("  Neo4j entities loaded: %d", counts["entities"])
    logger.info("  Neo4j relationships loaded: %d", counts["relationships"])
    logger.info("  EdgeQuake documents indexed: %d", indexed)
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
