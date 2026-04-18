"""End-to-end multi-agent book processing pipeline."""

from __future__ import annotations

import json
import os
from typing import Optional

from app.book_processing.aggregator_agent import KnowledgeAggregatorAgent
from app.book_processing.embedding_agent import VectorEmbeddingAgent
from app.book_processing.extraction_agent import InformationExtractionAgent
from app.book_processing.ingestion_agent import BookIngestionAgent
from app.book_processing.json_serializer_agent import JSONSerializerAgent
from app.book_processing.parser_agent import BookParserAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BookProcessingPipeline:
    """Process books to JSON knowledge and vectorized local index."""

    def __init__(self) -> None:
        self.ingestion_agent = BookIngestionAgent()
        self.parser_agent = BookParserAgent()
        self.extraction_agent = InformationExtractionAgent()
        self.serializer_agent = JSONSerializerAgent()
        self.aggregator_agent = KnowledgeAggregatorAgent()
        self.embedding_agent = VectorEmbeddingAgent()

    def process(
        self,
        input_path: str,
        output_dir: str,
        embeddings_dir: Optional[str] = None,
    ) -> dict:
        raw_books = self.ingestion_agent.ingest(input_path)
        if not raw_books:
            return {
                "total_books": 0,
                "books": [],
                "aggregated_output": "",
                "embeddings": None,
            }

        os.makedirs(output_dir, exist_ok=True)
        if embeddings_dir:
            os.makedirs(embeddings_dir, exist_ok=True)

        book_outputs: list[dict] = []
        book_jsons: list[dict] = []

        for raw_book in raw_books:
            parsed_books = self.parser_agent.parse([raw_book])
            extracted = self.extraction_agent.extract(parsed_books)
            serialized = self.serializer_agent.serialize(
                extracted=extracted,
                total_books=1,
                language=raw_book.language,
            )

            output_name = f"{os.path.splitext(raw_book.file_name)[0]}.json"
            output_path = os.path.join(output_dir, output_name)
            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(serialized, file, ensure_ascii=False, indent=2)

            book_outputs.append(
                {
                    "book": raw_book.file_name,
                    "language": raw_book.language,
                    "output": output_path,
                }
            )
            book_jsons.append(serialized)

        aggregated = self.aggregator_agent.aggregate(book_jsons)
        aggregated_path = os.path.join(output_dir, "aggregated_knowledge.json")
        with open(aggregated_path, "w", encoding="utf-8") as file:
            json.dump(aggregated, file, ensure_ascii=False, indent=2)

        embedding_result = None
        if embeddings_dir:
            embedding_result = self.embedding_agent.generate(aggregated, embeddings_dir)

        logger.info("Processed %d books into %s", len(book_outputs), output_dir)
        return {
            "total_books": len(book_outputs),
            "books": book_outputs,
            "aggregated_output": aggregated_path,
            "embeddings": embedding_result,
        }
