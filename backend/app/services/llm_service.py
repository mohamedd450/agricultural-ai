"""LLM integration service for agricultural AI platform.

Provides bilingual (Arabic/English) prompt generation and completion
using OpenAI-compatible APIs with graceful fallback.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.utils.exceptions import ServiceUnavailableError
from app.utils.logger import get_logger
from app.utils.prompts import PROMPTS

logger: logging.Logger = get_logger(__name__)

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    OPENAI_AVAILABLE = False
    logger.warning("openai package not installed – LLM features will be limited")


class LLMService:
    """LLM integration for generating agricultural diagnoses and recommendations.

    Supports OpenAI-compatible APIs and falls back to template-based responses
    when the API is unavailable.
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 1024
    TEMPERATURE = 0.3  # low for factual agricultural advice

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model
        self._client: Optional[Any] = None

        if OPENAI_AVAILABLE and api_key:
            try:
                kwargs: dict[str, Any] = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                self._client = openai.AsyncOpenAI(**kwargs)
                logger.info("LLMService initialised with model '%s'", model)
            except Exception:
                logger.error("Failed to initialise OpenAI client", exc_info=True)
                self._client = None

    # ── Core completion ──────────────────────────────────────────────────

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        language: str = "ar",
        max_tokens: int = MAX_TOKENS,
    ) -> dict:
        """Send a completion request to the LLM.

        Returns
        -------
        dict
            ``{"text": str, "tokens_used": int, "model": str, "success": bool}``
        """
        if self._client is None:
            logger.warning("LLM client unavailable – using template fallback")
            return self._template_fallback(prompt, language)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.TEMPERATURE,
            )
            text = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0

            return {
                "text": text.strip(),
                "tokens_used": tokens,
                "model": self.model,
                "success": True,
            }
        except Exception:
            logger.error("LLM completion failed", exc_info=True)
            return self._template_fallback(prompt, language)

    # ── Agricultural-specific helpers ────────────────────────────────────

    async def build_diagnosis_prompt(
        self,
        vision_result: Optional[dict] = None,
        graph_paths: Optional[list[str]] = None,
        user_query: str = "",
        language: str = "ar",
    ) -> str:
        """Construct a structured agricultural diagnosis prompt.

        Merges vision classification, graph reasoning paths, and the
        user's natural-language question into a single LLM prompt.

        Parameters
        ----------
        vision_result:
            Dict with ``class`` and ``confidence`` keys from the vision
            service.
        graph_paths:
            List of reasoning paths, e.g.
            ``["yellow_leaves → nitrogen_deficiency → urea"]``.
        user_query:
            Free-text question from the user.
        language:
            ``"ar"`` for Arabic output, ``"en"`` for English.

        Returns
        -------
        str
            A formatted prompt ready to be passed to :meth:`complete`.
        """
        template = PROMPTS.get(language, PROMPTS["ar"])

        vision_info = ""
        if vision_result:
            cls = vision_result.get("class", "unknown")
            conf = vision_result.get("confidence", 0.0)
            if language == "ar":
                vision_info = (
                    f"نتيجة تحليل الصورة: {cls} (ثقة: {conf:.0%})"
                )
            else:
                vision_info = (
                    f"Image analysis result: {cls} (confidence: {conf:.0%})"
                )

        paths_info = ""
        if graph_paths:
            joined = "\n  - ".join(graph_paths)
            if language == "ar":
                paths_info = f"مسارات الاستدلال من قاعدة المعرفة:\n  - {joined}"
            else:
                paths_info = f"Knowledge graph reasoning paths:\n  - {joined}"

        sections = [s for s in [vision_info, paths_info, user_query] if s]
        context = "\n\n".join(sections)

        return template["diagnosis"].format(context=context)

    async def generate_treatment_recommendation(
        self,
        diagnosis: str,
        crop_type: Optional[str] = None,
        language: str = "ar",
    ) -> dict:
        """Generate a treatment recommendation for the given diagnosis.

        Parameters
        ----------
        diagnosis:
            The identified disease or deficiency.
        crop_type:
            Optional crop species for tailored advice.
        language:
            Response language.

        Returns
        -------
        dict
            ``{"treatment": str, "prevention": str, "success": bool}``
        """
        template = PROMPTS.get(language, PROMPTS["ar"])

        crop_str = f" ({crop_type})" if crop_type else ""
        if language == "ar":
            prompt = (
                f"قدم توصيات علاجية ووقائية مفصلة لـ: {diagnosis}{crop_str}"
            )
            system = template.get("system", "أنت خبير زراعي متخصص.")
        else:
            prompt = (
                f"Provide detailed treatment and prevention recommendations for: "
                f"{diagnosis}{crop_str}"
            )
            system = template.get(
                "system", "You are a specialized agricultural expert."
            )

        result = await self.complete(prompt, system_prompt=system, language=language)

        if result.get("success"):
            text = result["text"]
            # Split into treatment vs prevention if both sections present
            if language == "ar":
                parts = text.split("الوقاية:", 1)
            else:
                parts = text.split("Prevention:", 1)

            treatment = parts[0].strip()
            prevention = parts[1].strip() if len(parts) > 1 else ""
            return {
                "treatment": treatment,
                "prevention": prevention,
                "success": True,
            }

        return {
            "treatment": diagnosis,
            "prevention": "",
            "success": False,
        }

    async def translate(
        self,
        text: str,
        target_language: str = "ar",
    ) -> str:
        """Translate *text* to *target_language* using the LLM.

        Returns the original text if translation fails.
        """
        if not text:
            return text

        if target_language == "ar":
            prompt = f"ترجم النص التالي إلى العربية بدقة:\n\n{text}"
        else:
            prompt = f"Translate the following text to English accurately:\n\n{text}"

        result = await self.complete(prompt, language=target_language)
        return result.get("text") or text

    # ── Availability check ───────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the LLM client is configured and ready."""
        return self._client is not None

    # ── Fallback ─────────────────────────────────────────────────────────

    @staticmethod
    def _template_fallback(prompt: str, language: str) -> dict:
        """Return a minimal fallback response when no LLM is available."""
        if language == "ar":
            text = (
                "خدمة نموذج اللغة غير متاحة حالياً. "
                "يرجى التحقق من إعداد مفتاح API."
            )
        else:
            text = (
                "Language model service is currently unavailable. "
                "Please check your API key configuration."
            )
        return {
            "text": text,
            "tokens_used": 0,
            "model": "fallback",
            "success": False,
        }
