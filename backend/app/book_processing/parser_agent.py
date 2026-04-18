"""Book parser agent: derive lightweight structure (chapters/sections/toc)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.book_processing.ingestion_agent import RawBook


@dataclass
class ParsedSection:
    title: str
    text: str
    page_start: int


@dataclass
class ParsedBook:
    file_name: str
    language: str
    title: str
    table_of_contents: list[str]
    sections: list[ParsedSection]


class BookParserAgent:
    """Parse raw book text into logical sections."""

    _heading_pattern = re.compile(
        r"(^|\s)(chapter\s+\d+|section\s+\d+|الفصل\s+\d+|الباب\s+\d+)",
        flags=re.IGNORECASE,
    )

    def parse(self, raw_books: list[RawBook]) -> list[ParsedBook]:
        parsed: list[ParsedBook] = []

        for raw in raw_books:
            title = self._derive_title(raw)
            sections = self._split_sections(raw)
            toc = [section.title for section in sections]
            parsed.append(
                ParsedBook(
                    file_name=raw.file_name,
                    language=raw.language,
                    title=title,
                    table_of_contents=toc,
                    sections=sections,
                )
            )

        return parsed

    def _derive_title(self, raw: RawBook) -> str:
        if raw.pages:
            head = raw.pages[0].get("text", "").strip().split("\n", maxsplit=1)[0]
            if head:
                return head[:120]
        return raw.file_name

    def _split_sections(self, raw: RawBook) -> list[ParsedSection]:
        lines = [line.strip() for line in raw.text.split("\n") if line.strip()]
        if not lines:
            return []

        sections: list[ParsedSection] = []
        current_title = "Introduction"
        current_lines: list[str] = []

        for line in lines:
            if self._heading_pattern.search(line):
                if current_lines:
                    sections.append(
                        ParsedSection(
                            title=current_title,
                            text="\n".join(current_lines),
                            page_start=len(sections) + 1,
                        )
                    )
                current_title = line[:100]
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                ParsedSection(
                    title=current_title,
                    text="\n".join(current_lines),
                    page_start=len(sections) + 1,
                )
            )

        if not sections:
            sections.append(
                ParsedSection(title="Introduction", text=raw.text, page_start=1)
            )

        return sections
