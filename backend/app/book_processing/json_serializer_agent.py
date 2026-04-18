"""JSON serializer agent for extracted agricultural knowledge."""

from __future__ import annotations

from datetime import date


class JSONSerializerAgent:
    """Build the canonical JSON schema for extracted book knowledge."""

    def serialize(
        self,
        extracted: dict,
        total_books: int,
        language: str,
        version: str = "1.0",
    ) -> dict:
        return {
            "books_metadata": {
                "total_books": total_books,
                "processing_date": date.today().isoformat(),
                "language": language,
                "version": version,
            },
            "diseases": extracted.get("diseases", []),
            "treatments": extracted.get("treatments", []),
            "techniques": extracted.get("techniques", []),
            "relationships": extracted.get("relationships", []),
        }
