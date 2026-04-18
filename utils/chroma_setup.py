from __future__ import annotations

from typing import Any


class LocalChroma:
    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        self._documents.append({"text": text, "metadata": metadata or {}})

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        query_l = query.lower()
        ranked = sorted(
            self._documents,
            key=lambda row: row["text"].lower().count(query_l),
            reverse=True,
        )
        return ranked[:top_k]


def build_default_store() -> LocalChroma:
    store = LocalChroma()
    store.add("Yellow leaves can indicate nitrogen deficiency.", {"source": "nitrogen_deficiency_guide"})
    store.add("Urea fertilizer is a common nitrogen supplement.", {"source": "urea_application_protocol"})
    return store
