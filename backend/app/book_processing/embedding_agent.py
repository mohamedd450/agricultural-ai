"""Vector embedding agent for extracted knowledge records."""

from __future__ import annotations

import hashlib
import json
import os


class VectorEmbeddingAgent:
    """Generate deterministic vectors and persist them for local retrieval."""

    def generate(self, payload: dict, output_dir: str) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "book_knowledge_embeddings.jsonl")

        records = self._flatten(payload)
        with open(output_path, "w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

        return {"path": output_path, "count": len(records)}

    def _flatten(self, payload: dict) -> list[dict]:
        rows: list[dict] = []
        for entity_type in ("diseases", "treatments", "techniques"):
            for item in payload.get(entity_type, []):
                text = " | ".join(
                    [
                        str(item.get("name_ar", "")),
                        str(item.get("name_en", "")),
                        " ".join(item.get("book_sources", [])),
                    ]
                ).strip()
                rows.append(
                    {
                        "id": item.get("id"),
                        "type": entity_type,
                        "text": text,
                        "vector": self._encode_text(text),
                        "metadata": {
                            "name_ar": item.get("name_ar", ""),
                            "name_en": item.get("name_en", ""),
                        },
                    }
                )
        return rows

    @staticmethod
    def _encode_text(text: str) -> list[float]:
        digest = hashlib.sha384(text.encode("utf-8")).digest()
        base = [float(byte) / 255.0 for byte in digest]
        return (base * (384 // len(base) + 1))[:384]
