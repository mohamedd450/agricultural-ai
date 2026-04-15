"""Multilingual LLM prompt templates for the Agricultural AI Platform."""

from __future__ import annotations

from string import Template
from typing import Final

# ---------------------------------------------------------------------------
# Diagnosis prompts
# ---------------------------------------------------------------------------

DIAGNOSIS_PROMPT_EN: Final[str] = (
    "You are an expert agricultural pathologist. Given the following information "
    "about a plant, provide a diagnosis.\n\n"
    "Image analysis result: ${vision_result}\n"
    "Knowledge graph data: ${graph_result}\n"
    "Relevant documents: ${vector_result}\n\n"
    "Provide:\n"
    "1. The most likely disease or condition\n"
    "2. Confidence level (0-100%)\n"
    "3. Key symptoms observed\n"
    "4. Recommended treatment\n"
    "5. Preventive measures\n\n"
    "Respond in clear, concise English suitable for a farmer."
)

DIAGNOSIS_PROMPT_AR: Final[str] = (
    "أنت خبير في أمراض النباتات الزراعية. بناءً على المعلومات التالية "
    "حول النبات، قدم تشخيصاً.\n\n"
    "نتيجة تحليل الصورة: ${vision_result}\n"
    "بيانات الرسم البياني المعرفي: ${graph_result}\n"
    "المستندات ذات الصلة: ${vector_result}\n\n"
    "قدم:\n"
    "1. المرض أو الحالة الأكثر احتمالاً\n"
    "2. مستوى الثقة (0-100%)\n"
    "3. الأعراض الرئيسية الملاحظة\n"
    "4. العلاج الموصى به\n"
    "5. التدابير الوقائية\n\n"
    "أجب بلغة عربية واضحة وموجزة مناسبة للمزارع."
)

# ---------------------------------------------------------------------------
# Graph query prompts
# ---------------------------------------------------------------------------

GRAPH_QUERY_PROMPT_EN: Final[str] = (
    "You are a knowledge graph query generator for an agricultural database. "
    "Convert the following natural language question into a structured query.\n\n"
    "Question: ${question}\n"
    "Available node types: Disease, Symptom, Crop, Fertilizer, Weather\n"
    "Available relationships: causes, treated_by, worsened_by, triggered_by, affects\n\n"
    "Return a JSON object with:\n"
    "- entities: list of entity names mentioned\n"
    "- relationships: list of relationship types to traverse\n"
    "- intent: one of [diagnosis, treatment, prevention, information]\n"
    "- max_hops: recommended traversal depth (1-3)"
)

GRAPH_QUERY_PROMPT_AR: Final[str] = (
    "أنت مولد استعلامات لرسم بياني معرفي لقاعدة بيانات زراعية. "
    "حوّل السؤال التالي بالعربية إلى استعلام منظم.\n\n"
    "السؤال: ${question}\n"
    "أنواع العقد المتاحة: مرض، عرض، محصول، سماد، طقس\n"
    "العلاقات المتاحة: يسبب، يعالج_بـ، يتفاقم_بـ، يثيره، يؤثر_على\n\n"
    "أعد كائن JSON يحتوي على:\n"
    "- entities: قائمة بأسماء الكيانات المذكورة\n"
    "- relationships: قائمة بأنواع العلاقات\n"
    "- intent: واحد من [تشخيص، علاج، وقاية، معلومات]\n"
    "- max_hops: عمق التتبع الموصى به (1-3)"
)

# ---------------------------------------------------------------------------
# Fusion prompts
# ---------------------------------------------------------------------------

FUSION_PROMPT_EN: Final[str] = (
    "You are an agricultural AI assistant. Synthesize the following multi-source "
    "analysis results into a single, coherent response for the farmer.\n\n"
    "Vision analysis: ${vision_result}\n"
    "Knowledge graph paths: ${graph_result}\n"
    "Document search results: ${vector_result}\n"
    "User query: ${query}\n\n"
    "Create a unified diagnosis that:\n"
    "- Resolves any conflicts between sources\n"
    "- Prioritizes the most reliable source for each claim\n"
    "- Provides actionable recommendations\n"
    "- Uses simple language a farmer can understand\n"
    "- Includes confidence levels for key findings"
)

FUSION_PROMPT_AR: Final[str] = (
    "أنت مساعد ذكاء اصطناعي زراعي. اجمع نتائج التحليل متعددة المصادر "
    "التالية في استجابة واحدة ومتماسكة للمزارع.\n\n"
    "تحليل الصورة: ${vision_result}\n"
    "مسارات الرسم البياني المعرفي: ${graph_result}\n"
    "نتائج البحث في المستندات: ${vector_result}\n"
    "استعلام المستخدم: ${query}\n\n"
    "أنشئ تشخيصاً موحداً:\n"
    "- يحل أي تعارضات بين المصادر\n"
    "- يعطي الأولوية للمصدر الأكثر موثوقية\n"
    "- يقدم توصيات قابلة للتنفيذ\n"
    "- يستخدم لغة بسيطة يفهمها المزارع\n"
    "- يتضمن مستويات الثقة للنتائج الرئيسية"
)

# ---------------------------------------------------------------------------
# Prompt registry and accessor
# ---------------------------------------------------------------------------

_PROMPT_REGISTRY: Final[dict[str, dict[str, str]]] = {
    "diagnosis": {"en": DIAGNOSIS_PROMPT_EN, "ar": DIAGNOSIS_PROMPT_AR},
    "graph_query": {"en": GRAPH_QUERY_PROMPT_EN, "ar": GRAPH_QUERY_PROMPT_AR},
    "fusion": {"en": FUSION_PROMPT_EN, "ar": FUSION_PROMPT_AR},
}


def get_prompt(
    name: str,
    language: str = "en",
    **substitutions: str,
) -> str:
    """Retrieve a prompt template and optionally fill in variables.

    Parameters
    ----------
    name:
        Prompt key – one of ``"diagnosis"``, ``"graph_query"``, ``"fusion"``.
    language:
        ISO-639-1 code (``"en"`` or ``"ar"``).
    **substitutions:
        Keyword arguments mapped into ``${key}`` placeholders via
        :class:`string.Template`.  Missing keys are left as-is.

    Returns
    -------
    str
        The (optionally rendered) prompt string.

    Raises
    ------
    KeyError
        If *name* is not in the registry.
    """
    lang = language.strip().lower()[:2]
    prompts_for_name = _PROMPT_REGISTRY.get(name)
    if prompts_for_name is None:
        raise KeyError(
            f"Unknown prompt '{name}'. Available: {', '.join(_PROMPT_REGISTRY)}"
        )

    template_str = prompts_for_name.get(lang, prompts_for_name["en"])

    if substitutions:
        return Template(template_str).safe_substitute(substitutions)
    return template_str
