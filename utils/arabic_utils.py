from __future__ import annotations

import re


_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    return "ar" if _ARABIC_RE.search(text or "") else "en"


def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    return " ".join(text.split())
