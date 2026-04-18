"""Knowledge aggregator agent to merge outputs from multiple books."""

from __future__ import annotations


class KnowledgeAggregatorAgent:
    """Merge duplicate entities while preserving references and relationships."""

    def aggregate(self, book_jsons: list[dict]) -> dict:
        if not book_jsons:
            return {
                "books_metadata": {
                    "total_books": 0,
                    "processing_date": "",
                    "language": "ar",
                    "version": "1.0",
                },
                "diseases": [],
                "treatments": [],
                "techniques": [],
                "relationships": [],
            }

        aggregated = {
            "books_metadata": book_jsons[-1]["books_metadata"],
            "diseases": [],
            "treatments": [],
            "techniques": [],
            "relationships": [],
        }

        by_type_name: dict[str, dict[str, dict]] = {
            "diseases": {},
            "treatments": {},
            "techniques": {},
        }
        relationships: dict[tuple[str, str, str], dict] = {}

        for payload in book_jsons:
            for section in ("diseases", "treatments", "techniques"):
                for item in payload.get(section, []):
                    key = (item.get("name_en") or item.get("name_ar") or item.get("id", "")).lower()
                    existing = by_type_name[section].get(key)
                    if existing is None:
                        by_type_name[section][key] = item
                        continue

                    for list_key in (
                        "symptoms",
                        "symptoms_en",
                        "causes",
                        "treatments",
                        "affected_crops",
                        "book_sources",
                        "results",
                        "suitable_for",
                        "benefits",
                        "best_crops",
                    ):
                        if list_key in existing or list_key in item:
                            existing[list_key] = sorted(
                                set(existing.get(list_key, []) + item.get(list_key, []))
                            )

                    for scalar_key in (
                        "dosage",
                        "frequency",
                        "application_method",
                        "description_ar",
                        "description_en",
                        "difficulty_level",
                    ):
                        if not existing.get(scalar_key) and item.get(scalar_key):
                            existing[scalar_key] = item[scalar_key]

                    for score_key in ("confidence", "effectiveness", "severity"):
                        if score_key in item:
                            existing[score_key] = max(float(existing.get(score_key, 0.0)), float(item.get(score_key, 0.0)))

            for rel in payload.get("relationships", []):
                rel_key = (rel.get("from", ""), rel.get("to", ""), rel.get("type", ""))
                current = relationships.get(rel_key)
                if current is None or rel.get("confidence", 0.0) > current.get("confidence", 0.0):
                    relationships[rel_key] = rel

        aggregated["diseases"] = list(by_type_name["diseases"].values())
        aggregated["treatments"] = list(by_type_name["treatments"].values())
        aggregated["techniques"] = list(by_type_name["techniques"].values())
        aggregated["relationships"] = list(relationships.values())
        aggregated["books_metadata"]["total_books"] = len(book_jsons)
        return aggregated
