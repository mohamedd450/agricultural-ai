from __future__ import annotations

import logging

from data_pipeline.embeddings_generator import EmbeddingsGenerator
from data_pipeline.graph_extractor import GraphExtractor
from data_pipeline.neo4j_loader import Neo4jLoader
from data_pipeline.pdf_processor import PDFProcessor
from data_pipeline.qdrant_loader import QdrantLoader
from data_pipeline.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)

_VALID_STEPS = ("pdf", "chunk", "embed", "qdrant", "neo4j")


class DataPipeline:
    """Orchestrate the full data-ingestion pipeline.

    Pipeline stages:
        1. **pdf**    – extract text from PDF documents
        2. **chunk**  – split text into semantic chunks
        3. **embed**  – generate vector embeddings
        4. **qdrant** – load vectors into Qdrant
        5. **neo4j**  – load knowledge graph into Neo4j
    """

    def __init__(self, config: dict) -> None:
        self.config = config

        self.pdf_processor = PDFProcessor(
            ocr_enabled=config.get("ocr_enabled", True),
        )
        self.chunker = SemanticChunker(
            chunk_size=config.get("chunk_size", 512),
            chunk_overlap=config.get("chunk_overlap", 50),
            language=config.get("language", "ar"),
        )
        self.embeddings = EmbeddingsGenerator(
            model_name=config.get(
                "embedding_model",
                "sentence-transformers/all-MiniLM-L6-v2",
            ),
        )
        self.graph_extractor = GraphExtractor()
        self.qdrant = QdrantLoader(
            host=config.get("qdrant_host", "localhost"),
            port=config.get("qdrant_port", 6333),
            collection_name=config.get(
                "qdrant_collection", "agricultural_knowledge"
            ),
        )
        self.neo4j = Neo4jLoader(
            uri=config.get("neo4j_uri", "bolt://localhost:7687"),
            user=config.get("neo4j_user", "neo4j"),
            password=config.get("neo4j_password", ""),
        )

    async def run(self, source_dir: str) -> None:
        """Execute the full pipeline from PDF ingestion to database loading."""
        logger.info("Pipeline started — source directory: %s", source_dir)

        # Step 1: extract text from PDFs
        logger.info("Step 1/5: Extracting text from PDFs …")
        pages = await self.pdf_processor.process_directory(source_dir)
        logger.info("Extracted %d pages", len(pages))

        # Step 2: chunk the extracted text
        logger.info("Step 2/5: Chunking text …")
        all_chunks: list[dict] = []
        for page in pages:
            chunks = self.chunker.chunk_text(page["text"], page["metadata"])
            all_chunks.extend(chunks)
        logger.info("Created %d chunks", len(all_chunks))

        # Step 3: generate embeddings
        logger.info("Step 3/5: Generating embeddings …")
        texts = [c["text"] for c in all_chunks]
        embeddings = await self.embeddings.generate(texts)
        logger.info("Generated %d embeddings", len(embeddings))

        # Step 4: load into Qdrant
        logger.info("Step 4/5: Loading into Qdrant …")
        await self.qdrant.initialize()
        loaded = await self.qdrant.load_documents(all_chunks, embeddings)
        logger.info("Loaded %d documents into Qdrant", loaded)

        # Step 5: extract & load knowledge graph into Neo4j
        logger.info("Step 5/5: Building knowledge graph …")
        await self.neo4j.connect()
        total_entities = 0
        total_relationships = 0
        for page in pages:
            entities = await self.graph_extractor.extract_entities(page["text"])
            relationships = await self.graph_extractor.extract_relationships(
                page["text"], entities
            )
            total_entities += await self.neo4j.load_entities(entities)
            total_relationships += await self.neo4j.load_relationships(
                relationships
            )
        logger.info(
            "Knowledge graph: %d entities, %d relationships",
            total_entities,
            total_relationships,
        )

        # Cleanup
        await self.qdrant.close()
        await self.neo4j.close()

        logger.info("Pipeline completed successfully.")

    async def run_step(self, step: str, **kwargs) -> object:
        """Run an individual pipeline step by name.

        Supported steps: ``pdf``, ``chunk``, ``embed``, ``qdrant``, ``neo4j``.
        """
        if step not in _VALID_STEPS:
            raise ValueError(
                f"Unknown step '{step}'. Must be one of {_VALID_STEPS}."
            )

        logger.info("Running individual step: %s", step)

        if step == "pdf":
            source_dir: str = kwargs.get("source_dir", "")
            return await self.pdf_processor.process_directory(source_dir)

        if step == "chunk":
            text: str = kwargs.get("text", "")
            metadata: dict = kwargs.get("metadata", {})
            return self.chunker.chunk_text(text, metadata)

        if step == "embed":
            texts: list[str] = kwargs.get("texts", [])
            return await self.embeddings.generate(texts)

        if step == "qdrant":
            documents: list[dict] = kwargs.get("documents", [])
            embeddings_list: list[list[float]] = kwargs.get("embeddings", [])
            await self.qdrant.initialize()
            return await self.qdrant.load_documents(documents, embeddings_list)

        if step == "neo4j":
            entities: list[dict] = kwargs.get("entities", [])
            relationships: list[dict] = kwargs.get("relationships", [])
            await self.neo4j.connect()
            e_count = await self.neo4j.load_entities(entities)
            r_count = await self.neo4j.load_relationships(relationships)
            return {"entities_loaded": e_count, "relationships_loaded": r_count}

        return None
