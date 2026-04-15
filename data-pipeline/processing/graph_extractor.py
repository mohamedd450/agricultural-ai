"""Knowledge graph extraction for agricultural entities and relationships."""

import logging
import re
import uuid

logger = logging.getLogger(__name__)

# Agricultural entity patterns
ENTITY_PATTERNS: dict[str, list[str]] = {
    "Disease": [
        r"\b(blight|rust|wilt|rot|mildew|mosaic|smut|scab|canker|leaf\s*spot)\b",
        r"\b(تبقع|صدأ|ذبول|عفن|بياض)\b",
    ],
    "Symptom": [
        r"\b(yellowing|wilting|stunting|lesion|necrosis|chlorosis|browning|curling)\b",
        r"\b(اصفرار|ذبول|تقزم|نخر)\b",
    ],
    "Crop": [
        r"\b(wheat|rice|corn|maize|cotton|tomato|potato|barley|soybean|date\s*palm)\b",
        r"\b(قمح|أرز|ذرة|قطن|طماطم|بطاطس|شعير|نخيل)\b",
    ],
    "Fertilizer": [
        r"\b(urea|npk|phosphate|potassium|nitrogen|compost|manure|ammonium)\b",
        r"\b(يوريا|سماد|فوسفات|بوتاسيوم|نيتروجين)\b",
    ],
    "Treatment": [
        r"\b(fungicide|pesticide|herbicide|insecticide|nematicide|spray|irrigation)\b",
        r"\b(مبيد|رش|ري|علاج)\b",
    ],
    "Weather": [
        r"\b(drought|flood|frost|heatwave|rainfall|humidity|temperature)\b",
        r"\b(جفاف|فيضان|صقيع|حرارة|رطوبة|أمطار)\b",
    ],
}

RELATIONSHIP_PATTERNS: list[dict] = [
    {"pattern": r"(\w+)\s+(?:causes?|leads?\s+to)\s+(\w+)", "type": "causes"},
    {"pattern": r"(\w+)\s+(?:treated|controlled)\s+(?:by|with)\s+(\w+)", "type": "treated_by"},
    {"pattern": r"(\w+)\s+(?:worsened|aggravated)\s+by\s+(\w+)", "type": "worsened_by"},
    {"pattern": r"(\w+)\s+(?:affects?|impacts?)\s+(\w+)", "type": "affects"},
    {"pattern": r"(\w+)\s+(?:grows?|grown|cultivated)\s+in\s+(\w+)", "type": "grows_in"},
]


class GraphExtractor:
    """Extracts knowledge graph entities and relationships from agricultural text."""

    def extract_entities(self, text: str) -> list[dict]:
        """Extract agricultural entities from text.

        Args:
            text: Input text to analyze.

        Returns:
            List of dicts with keys: name, type, confidence, id.
        """
        entities: list[dict] = []
        seen: set[str] = set()

        for entity_type, patterns in ENTITY_PATTERNS.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        name = match.group(0).strip().lower()
                        key = f"{entity_type}:{name}"
                        if key not in seen:
                            seen.add(key)
                            entities.append({
                                "id": str(uuid.uuid4()),
                                "name": name,
                                "type": entity_type,
                                "confidence": 0.85,
                            })
                except re.error as e:
                    logger.warning("Regex error for pattern %s: %s", pattern, e)

        logger.info("Extracted %d entities", len(entities))
        return entities

    def extract_relationships(
        self, text: str, entities: list[dict]
    ) -> list[dict]:
        """Extract relationships between entities from text.

        Args:
            text: Input text to analyze.
            entities: Previously extracted entities.

        Returns:
            List of relationship dicts with keys: source, target, type, confidence.
        """
        relationships: list[dict] = []
        entity_names = {e["name"].lower() for e in entities}
        entity_lookup = {e["name"].lower(): e for e in entities}

        for rel_pattern in RELATIONSHIP_PATTERNS:
            try:
                matches = re.finditer(rel_pattern["pattern"], text, re.IGNORECASE)
                for match in matches:
                    source_name = match.group(1).strip().lower()
                    target_name = match.group(2).strip().lower()

                    source = entity_lookup.get(source_name)
                    target = entity_lookup.get(target_name)

                    if source and target:
                        relationships.append({
                            "source": source["id"],
                            "source_name": source["name"],
                            "target": target["id"],
                            "target_name": target["name"],
                            "type": rel_pattern["type"],
                            "confidence": 0.75,
                        })
            except re.error as e:
                logger.warning("Regex error in relationship pattern: %s", e)

        # Proximity-based relationship extraction
        proximity_rels = self._extract_proximity_relationships(text, entities)
        relationships.extend(proximity_rels)

        logger.info("Extracted %d relationships", len(relationships))
        return relationships

    @staticmethod
    def _extract_proximity_relationships(
        text: str, entities: list[dict]
    ) -> list[dict]:
        """Extract relationships based on entity proximity in text.

        Entities mentioned within a short window are likely related.

        Args:
            text: Input text.
            entities: List of extracted entities.

        Returns:
            List of proximity-based relationships.
        """
        relationships: list[dict] = []
        text_lower = text.lower()
        entity_positions: list[tuple[int, dict]] = []

        for entity in entities:
            pos = text_lower.find(entity["name"].lower())
            if pos >= 0:
                entity_positions.append((pos, entity))

        entity_positions.sort(key=lambda x: x[0])

        window = 200  # characters
        for i, (pos_a, ent_a) in enumerate(entity_positions):
            for pos_b, ent_b in entity_positions[i + 1:]:
                if pos_b - pos_a > window:
                    break
                if ent_a["type"] != ent_b["type"]:
                    relationships.append({
                        "source": ent_a["id"],
                        "source_name": ent_a["name"],
                        "target": ent_b["id"],
                        "target_name": ent_b["name"],
                        "type": "related_to",
                        "confidence": 0.5,
                    })

        return relationships
