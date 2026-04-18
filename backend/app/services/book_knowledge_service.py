"""Local knowledge service backed by aggregated book JSON outputs."""

from __future__ import annotations

import json
import os
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class BookKnowledgeService:
    """Serve lightweight search over processed book knowledge."""

    def __init__(self, aggregated_path: str = "data/json_output/aggregated_knowledge.json") -> None:
        self.aggregated_path = aggregated_path
        self._data: dict = {}

    def load(self) -> None:
        """Load aggregated knowledge file when available."""
        if not os.path.isfile(self.aggregated_path):
            self._data = {}
            return

        try:
            with open(self.aggregated_path, "r", encoding="utf-8") as file:
                self._data = json.load(file)
        except Exception:
            logger.exception("Failed to load book knowledge: %s", self.aggregated_path)
            self._data = {}

    @property
    def is_available(self) -> bool:
        return bool(self._data)

    async def search(self, query: str, language: str = "ar") -> Optional[dict]:
        """Search diseases/treatments/techniques for keyword overlap."""
        if not query or not self._data:
            return None

        q = query.lower()
        best: Optional[dict] = None

        for section in ("diseases", "treatments", "techniques"):
            for item in self._data.get(section, []):
                haystack = " ".join(
                    [
                        str(item.get("name_ar", "")),
                        str(item.get("name_en", "")),
                        " ".join(item.get("symptoms", [])),
                        " ".join(item.get("treatments", [])),
                        " ".join(item.get("benefits", [])),
                    ]
                ).lower()
                if not haystack:
                    continue

                score = self._keyword_score(q, haystack)
                if score <= 0:
                    continue

                candidate = {
                    "answer": item.get("name_ar") or item.get("name_en", ""),
                    "diagnosis": item.get("name_ar") or item.get("name_en", ""),
                    "treatment": self._pick_treatment(item),
                    "confidence": min(0.99, 0.55 + score * 0.1),
                    "graph_paths": [f"books:{section}:{item.get('id', '')}"],
                    "book_sources": item.get("book_sources", []),
                    "source": "book_knowledge",
                    "language": language,
                }
                if best is None or candidate["confidence"] > best["confidence"]:
                    best = candidate

        return best

    @staticmethod
    def _keyword_score(query: str, haystack: str) -> int:
        return sum(1 for token in query.split() if token and token in haystack)

    @staticmethod
    def _pick_treatment(item: dict) -> str:
        if item.get("treatments"):
            return str(item["treatments"][0])
        if item.get("name_ar") and "سماد" in str(item.get("name_ar")):
            return str(item["name_ar"])
        return ""
