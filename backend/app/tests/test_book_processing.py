from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.book_processing.pipeline import BookProcessingPipeline
from app.orchestrators.workflow_nodes import router_node


@pytest.mark.asyncio
async def test_router_detects_book_input() -> None:
    state = {"book_input_path": "data/books", "text_query": "", "language": "ar"}
    routed = await router_node(state)
    assert routed["input_type"] == "book"


def test_book_pipeline_processes_txt_to_aggregated_json(tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    output_dir = tmp_path / "json_output"
    embeddings_dir = tmp_path / "embeddings"
    books_dir.mkdir()

    sample_book = books_dir / "book1.txt"
    sample_book.write_text(
        "الفصل 1\n"
        "أوراق الطماطم الصفراء تعني نقص النيتروجين.\n"
        "العلاج المناسب هو سماد اليوريا مع الري بالتنقيط.",
        encoding="utf-8",
    )

    result = BookProcessingPipeline().process(
        input_path=str(books_dir),
        output_dir=str(output_dir),
        embeddings_dir=str(embeddings_dir),
    )

    assert result["total_books"] == 1
    assert result["aggregated_output"]
    aggregated_path = Path(result["aggregated_output"])
    assert aggregated_path.exists()

    aggregated = json.loads(aggregated_path.read_text(encoding="utf-8"))
    assert aggregated["books_metadata"]["total_books"] == 1
    assert any(item["name_en"] == "Nitrogen Deficiency" for item in aggregated["diseases"])
    assert any(item["name_en"] == "Urea Fertilizer" for item in aggregated["treatments"])
    assert any(item["name_en"] == "Drip Irrigation Technique" for item in aggregated["techniques"])

    embeddings = result["embeddings"]
    assert embeddings is not None
    assert Path(embeddings["path"]).exists()
    assert embeddings["count"] >= 1
