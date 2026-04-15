"""Seed the Neo4j agricultural knowledge graph with sample data.

Populates the graph with diseases, symptoms, crops, fertilizers,
weather conditions, regions, and the relationships between them.
All statements use ``MERGE`` so the script is idempotent.
"""

import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Diseases
# ------------------------------------------------------------------
DISEASES: list[dict] = [
    {"name": "Nitrogen Deficiency", "name_ar": "نقص النيتروجين", "severity": "moderate", "type": "nutritional"},
    {"name": "Leaf Blight", "name_ar": "لفحة الأوراق", "severity": "high", "type": "fungal"},
    {"name": "Powdery Mildew", "name_ar": "البياض الدقيقي", "severity": "moderate", "type": "fungal"},
    {"name": "Rust", "name_ar": "الصدأ", "severity": "high", "type": "fungal"},
    {"name": "Bacterial Spot", "name_ar": "التبقع البكتيري", "severity": "high", "type": "bacterial"},
    {"name": "Late Blight", "name_ar": "اللفحة المتأخرة", "severity": "critical", "type": "fungal"},
    {"name": "Early Blight", "name_ar": "اللفحة المبكرة", "severity": "high", "type": "fungal"},
    {"name": "Fusarium Wilt", "name_ar": "ذبول الفيوزاريوم", "severity": "critical", "type": "fungal"},
    {"name": "Downy Mildew", "name_ar": "البياض الزغبي", "severity": "high", "type": "fungal"},
    {"name": "Mosaic Virus", "name_ar": "فيروس الموزاييك", "severity": "high", "type": "viral"},
]

# ------------------------------------------------------------------
# Symptoms (with Arabic translations)
# ------------------------------------------------------------------
SYMPTOMS: list[dict] = [
    {"name": "Yellowing Leaves", "name_ar": "اصفرار الأوراق"},
    {"name": "Stunted Growth", "name_ar": "تقزم النمو"},
    {"name": "Brown Spots", "name_ar": "بقع بنية"},
    {"name": "Wilting", "name_ar": "الذبول"},
    {"name": "White Powder on Leaves", "name_ar": "مسحوق أبيض على الأوراق"},
    {"name": "Leaf Curl", "name_ar": "تجعد الأوراق"},
    {"name": "Orange Pustules", "name_ar": "بثور برتقالية"},
    {"name": "Leaf Drop", "name_ar": "تساقط الأوراق"},
    {"name": "Water-soaked Lesions", "name_ar": "آفات مشبعة بالماء"},
    {"name": "Fruit Spots", "name_ar": "بقع على الثمار"},
    {"name": "Dark Concentric Rings", "name_ar": "حلقات داكنة متحدة المركز"},
    {"name": "Stem Rot", "name_ar": "تعفن الساق"},
    {"name": "Fuzzy Grey Growth", "name_ar": "نمو رمادي زغبي"},
    {"name": "Mosaic Pattern", "name_ar": "نمط فسيفسائي"},
    {"name": "Distorted Leaves", "name_ar": "أوراق مشوهة"},
]

# ------------------------------------------------------------------
# Crops
# ------------------------------------------------------------------
CROPS: list[dict] = [
    {"name": "Tomato", "name_ar": "طماطم", "season": "summer"},
    {"name": "Wheat", "name_ar": "قمح", "season": "winter"},
    {"name": "Rice", "name_ar": "أرز", "season": "summer"},
    {"name": "Corn", "name_ar": "ذرة", "season": "summer"},
    {"name": "Cotton", "name_ar": "قطن", "season": "summer"},
    {"name": "Potato", "name_ar": "بطاطس", "season": "spring"},
]

# ------------------------------------------------------------------
# Fertilizers
# ------------------------------------------------------------------
FERTILIZERS: list[dict] = [
    {"name": "Urea", "name_ar": "يوريا", "type": "nitrogen"},
    {"name": "DAP", "name_ar": "داب", "type": "phosphorus"},
    {"name": "Potash", "name_ar": "بوتاس", "type": "potassium"},
    {"name": "NPK", "name_ar": "ن ب ك", "type": "compound"},
    {"name": "Compost", "name_ar": "سماد عضوي", "type": "organic"},
    {"name": "Neem Oil", "name_ar": "زيت النيم", "type": "organic"},
]

# ------------------------------------------------------------------
# Weather conditions
# ------------------------------------------------------------------
WEATHER_CONDITIONS: list[dict] = [
    {"name": "High Humidity", "name_ar": "رطوبة عالية"},
    {"name": "Drought", "name_ar": "جفاف"},
    {"name": "Heavy Rain", "name_ar": "أمطار غزيرة"},
    {"name": "Heat Wave", "name_ar": "موجة حر"},
]

# ------------------------------------------------------------------
# Regions
# ------------------------------------------------------------------
REGIONS: list[dict] = [
    {"name": "Nile Delta", "name_ar": "دلتا النيل", "climate": "subtropical"},
    {"name": "Upper Egypt", "name_ar": "صعيد مصر", "climate": "arid"},
    {"name": "Punjab", "name_ar": "البنجاب", "climate": "semi-arid"},
]

# ------------------------------------------------------------------
# Relationships
# ------------------------------------------------------------------
# (source_label, source_name, relationship, target_label, target_name)
DISEASE_SYMPTOM_RELS: list[tuple[str, str, str, str, str]] = [
    ("Disease", "Nitrogen Deficiency", "SHOWS", "Symptom", "Yellowing Leaves"),
    ("Disease", "Nitrogen Deficiency", "SHOWS", "Symptom", "Stunted Growth"),
    ("Disease", "Leaf Blight", "SHOWS", "Symptom", "Brown Spots"),
    ("Disease", "Leaf Blight", "SHOWS", "Symptom", "Wilting"),
    ("Disease", "Powdery Mildew", "SHOWS", "Symptom", "White Powder on Leaves"),
    ("Disease", "Powdery Mildew", "SHOWS", "Symptom", "Leaf Curl"),
    ("Disease", "Rust", "SHOWS", "Symptom", "Orange Pustules"),
    ("Disease", "Rust", "SHOWS", "Symptom", "Leaf Drop"),
    ("Disease", "Bacterial Spot", "SHOWS", "Symptom", "Water-soaked Lesions"),
    ("Disease", "Bacterial Spot", "SHOWS", "Symptom", "Fruit Spots"),
    ("Disease", "Late Blight", "SHOWS", "Symptom", "Brown Spots"),
    ("Disease", "Late Blight", "SHOWS", "Symptom", "Fuzzy Grey Growth"),
    ("Disease", "Early Blight", "SHOWS", "Symptom", "Dark Concentric Rings"),
    ("Disease", "Early Blight", "SHOWS", "Symptom", "Leaf Drop"),
    ("Disease", "Fusarium Wilt", "SHOWS", "Symptom", "Wilting"),
    ("Disease", "Fusarium Wilt", "SHOWS", "Symptom", "Stem Rot"),
    ("Disease", "Downy Mildew", "SHOWS", "Symptom", "Fuzzy Grey Growth"),
    ("Disease", "Downy Mildew", "SHOWS", "Symptom", "Yellowing Leaves"),
    ("Disease", "Mosaic Virus", "SHOWS", "Symptom", "Mosaic Pattern"),
    ("Disease", "Mosaic Virus", "SHOWS", "Symptom", "Distorted Leaves"),
]

DISEASE_CROP_RELS: list[tuple[str, str, str, str, str]] = [
    ("Disease", "Nitrogen Deficiency", "AFFECTS", "Crop", "Tomato"),
    ("Disease", "Nitrogen Deficiency", "AFFECTS", "Crop", "Wheat"),
    ("Disease", "Nitrogen Deficiency", "AFFECTS", "Crop", "Rice"),
    ("Disease", "Nitrogen Deficiency", "AFFECTS", "Crop", "Corn"),
    ("Disease", "Leaf Blight", "AFFECTS", "Crop", "Corn"),
    ("Disease", "Leaf Blight", "AFFECTS", "Crop", "Rice"),
    ("Disease", "Powdery Mildew", "AFFECTS", "Crop", "Wheat"),
    ("Disease", "Powdery Mildew", "AFFECTS", "Crop", "Cotton"),
    ("Disease", "Rust", "AFFECTS", "Crop", "Wheat"),
    ("Disease", "Bacterial Spot", "AFFECTS", "Crop", "Tomato"),
    ("Disease", "Late Blight", "AFFECTS", "Crop", "Tomato"),
    ("Disease", "Late Blight", "AFFECTS", "Crop", "Potato"),
    ("Disease", "Early Blight", "AFFECTS", "Crop", "Tomato"),
    ("Disease", "Early Blight", "AFFECTS", "Crop", "Potato"),
    ("Disease", "Fusarium Wilt", "AFFECTS", "Crop", "Tomato"),
    ("Disease", "Fusarium Wilt", "AFFECTS", "Crop", "Cotton"),
    ("Disease", "Downy Mildew", "AFFECTS", "Crop", "Corn"),
    ("Disease", "Mosaic Virus", "AFFECTS", "Crop", "Tomato"),
]

FERTILIZER_DISEASE_RELS: list[tuple[str, str, str, str, str]] = [
    ("Fertilizer", "Urea", "TREATS", "Disease", "Nitrogen Deficiency"),
    ("Fertilizer", "NPK", "TREATS", "Disease", "Nitrogen Deficiency"),
    ("Fertilizer", "Compost", "TREATS", "Disease", "Nitrogen Deficiency"),
    ("Fertilizer", "Neem Oil", "TREATS", "Disease", "Powdery Mildew"),
    ("Fertilizer", "Neem Oil", "TREATS", "Disease", "Bacterial Spot"),
    ("Fertilizer", "Potash", "TREATS", "Disease", "Rust"),
    ("Fertilizer", "DAP", "TREATS", "Disease", "Early Blight"),
]

WEATHER_DISEASE_RELS: list[tuple[str, str, str, str, str]] = [
    ("Weather", "High Humidity", "TRIGGERS", "Disease", "Powdery Mildew"),
    ("Weather", "High Humidity", "TRIGGERS", "Disease", "Downy Mildew"),
    ("Weather", "High Humidity", "TRIGGERS", "Disease", "Late Blight"),
    ("Weather", "Heavy Rain", "TRIGGERS", "Disease", "Leaf Blight"),
    ("Weather", "Heavy Rain", "TRIGGERS", "Disease", "Bacterial Spot"),
    ("Weather", "Drought", "TRIGGERS", "Disease", "Fusarium Wilt"),
    ("Weather", "Heat Wave", "TRIGGERS", "Disease", "Mosaic Virus"),
]

ALL_RELATIONSHIPS = (
    DISEASE_SYMPTOM_RELS
    + DISEASE_CROP_RELS
    + FERTILIZER_DISEASE_RELS
    + WEATHER_DISEASE_RELS
)


def _merge_node_cypher(label: str, props: dict) -> tuple[str, dict]:
    """Build a MERGE Cypher statement and parameter dict for a node."""
    params = {f"p_{k}": v for k, v in props.items()}
    set_clauses = ", ".join(f"n.{k} = $p_{k}" for k in props)
    cypher = (
        f"MERGE (n:{label} {{name: $p_name}}) "
        f"ON CREATE SET {set_clauses} "
        f"ON MATCH SET {set_clauses}"
    )
    return cypher, params


async def seed_data(neo4j_driver) -> None:
    """Populate the Neo4j graph with agricultural seed data.

    All operations use ``MERGE`` to guarantee idempotency.

    Args:
        neo4j_driver: An open ``neo4j.AsyncDriver`` instance.
    """
    logger.info("Starting data seeding")

    async with neo4j_driver.session() as session:
        # -- Diseases ---------------------------------------------------
        for disease in DISEASES:
            cypher, params = _merge_node_cypher("Disease", disease)
            await session.run(cypher, params)
        logger.info("Seeded %d diseases", len(DISEASES))

        # -- Symptoms ---------------------------------------------------
        for symptom in SYMPTOMS:
            cypher, params = _merge_node_cypher("Symptom", symptom)
            await session.run(cypher, params)
        logger.info("Seeded %d symptoms", len(SYMPTOMS))

        # -- Crops ------------------------------------------------------
        for crop in CROPS:
            cypher, params = _merge_node_cypher("Crop", crop)
            await session.run(cypher, params)
        logger.info("Seeded %d crops", len(CROPS))

        # -- Fertilizers ------------------------------------------------
        for fert in FERTILIZERS:
            cypher, params = _merge_node_cypher("Fertilizer", fert)
            await session.run(cypher, params)
        logger.info("Seeded %d fertilizers", len(FERTILIZERS))

        # -- Weather conditions -----------------------------------------
        for weather in WEATHER_CONDITIONS:
            cypher, params = _merge_node_cypher("Weather", weather)
            await session.run(cypher, params)
        logger.info("Seeded %d weather conditions", len(WEATHER_CONDITIONS))

        # -- Regions ----------------------------------------------------
        for region in REGIONS:
            cypher, params = _merge_node_cypher("Region", region)
            await session.run(cypher, params)
        logger.info("Seeded %d regions", len(REGIONS))

        # -- Relationships ----------------------------------------------
        for src_label, src_name, rel, tgt_label, tgt_name in ALL_RELATIONSHIPS:
            cypher = (
                f"MATCH (a:{src_label} {{name: $src_name}}) "
                f"MATCH (b:{tgt_label} {{name: $tgt_name}}) "
                f"MERGE (a)-[:{rel}]->(b)"
            )
            await session.run(cypher, {"src_name": src_name, "tgt_name": tgt_name})
        logger.info("Seeded %d relationships", len(ALL_RELATIONSHIPS))

    logger.info("Data seeding complete")
