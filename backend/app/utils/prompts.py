"""Prompt templates for the Agricultural AI Graph-RAG pipeline.

Every template uses Python :meth:`str.format` placeholders so that they can be
rendered with ``TEMPLATE.format(key=value, …)``.
"""

from __future__ import annotations

# ── Vision → Graph bridge ───────────────────────────────────────────────────

VISION_TO_GRAPH_PROMPT: str = (
    "You are an agricultural knowledge-graph assistant.\n"
    "A vision model has analysed a crop image and produced the following output:\n\n"
    "Crop: {crop}\n"
    "Detected symptoms: {symptoms}\n"
    "Confidence: {confidence}\n\n"
    "Convert this information into a structured Cypher query that retrieves\n"
    "relevant diseases, treatments, and preventive measures from the\n"
    "agricultural knowledge graph.  Return ONLY the Cypher query."
)

# ── Diagnosis generation ────────────────────────────────────────────────────

DIAGNOSIS_PROMPT: str = (
    "You are an expert agricultural diagnostician.\n\n"
    "Based on the following information, provide a comprehensive diagnosis:\n\n"
    "Crop: {crop}\n"
    "Observed symptoms: {symptoms}\n"
    "Vision model diagnosis: {diagnosis}\n"
    "Confidence score: {confidence}\n\n"
    "Knowledge graph context:\n{graph_context}\n\n"
    "Vector search context:\n{vector_context}\n\n"
    "Provide:\n"
    "1. A confirmed or refined diagnosis\n"
    "2. Severity assessment (low / medium / high / critical)\n"
    "3. Recommended treatment steps\n"
    "4. Preventive measures for the future\n"
    "5. Expected recovery timeline"
)

# ── Arabic response ─────────────────────────────────────────────────────────

ARABIC_RESPONSE_PROMPT: str = (
    "أنت مساعد زراعي متخصص.  قدّم الإجابة التالية باللغة العربية الفصحى "
    "بأسلوب واضح ومبسّط يناسب المزارعين.\n\n"
    "التشخيص: {diagnosis}\n"
    "درجة الثقة: {confidence}\n"
    "المحصول: {crop}\n"
    "الأعراض: {symptoms}\n\n"
    "يُرجى تقديم:\n"
    "١. ملخّص التشخيص\n"
    "٢. خطوات العلاج الموصى بها\n"
    "٣. إجراءات وقائية\n"
    "٤. الجدول الزمني المتوقع للتعافي"
)

# ── English response ────────────────────────────────────────────────────────

ENGLISH_RESPONSE_PROMPT: str = (
    "You are a specialised agricultural assistant.  Present the following\n"
    "answer in clear, plain English suitable for farmers.\n\n"
    "Diagnosis: {diagnosis}\n"
    "Confidence: {confidence}\n"
    "Crop: {crop}\n"
    "Symptoms: {symptoms}\n\n"
    "Please provide:\n"
    "1. Diagnosis summary\n"
    "2. Recommended treatment steps\n"
    "3. Preventive measures\n"
    "4. Expected recovery timeline"
)

# ── Multi-source fusion ─────────────────────────────────────────────────────

FUSION_PROMPT: str = (
    "You are a data-fusion engine for an agricultural AI platform.\n\n"
    "Combine the following sources into a single, coherent response:\n\n"
    "Vision model output:\n{vision_output}\n\n"
    "Knowledge graph results:\n{graph_results}\n\n"
    "Vector search results:\n{vector_results}\n\n"
    "Crop: {crop}\n"
    "Symptoms: {symptoms}\n\n"
    "Produce a unified analysis that:\n"
    "1. Resolves any contradictions between sources\n"
    "2. Highlights consensus findings\n"
    "3. Assigns an overall confidence score\n"
    "4. Provides actionable recommendations"
)
