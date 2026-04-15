"""Tests for GraphRAGService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.models.graph_models import GraphRAGResponse
from app.services.graph_rag_service import GraphRAGService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def _mock_settings():
    settings = MagicMock(edgequake_host="localhost", edgequake_port=9090)
    with patch("app.services.graph_rag_service.get_settings", return_value=settings):
        yield settings


@pytest.fixture
def mock_http_client():
    """An httpx.AsyncClient mock that returns sync .json() responses."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def graph_service(_mock_settings, mock_http_client):
    return GraphRAGService(http_client=mock_http_client)


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_returns_response(graph_service, mock_http_client):
    """A successful query should return a GraphRAGResponse."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "answer": "Apply urea for nitrogen deficiency",
        "confidence": 0.85,
        "nodes": [],
        "edges": [],
        "paths": [],
        "reasoning_steps": ["Identified disease", "Found treatment"],
    }
    mock_http_client.post.return_value = mock_response

    result = await graph_service.query("How to treat nitrogen deficiency?")
    assert isinstance(result, GraphRAGResponse)
    assert result.confidence == 0.85
    assert "urea" in result.answer.lower()


@pytest.mark.asyncio
async def test_multi_hop_query(graph_service, mock_http_client):
    """Multi-hop query should return a valid response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "answer": "Leaf blight in rice can be treated with copper fungicide",
        "confidence": 0.75,
        "nodes": [
            {"id": "d1", "label": "Leaf Blight", "type": "Disease"},
            {"id": "c1", "label": "Rice", "type": "Crop"},
        ],
        "edges": [
            {"source": "d1", "target": "c1", "relationship": "affects", "weight": 0.9},
        ],
        "paths": [],
        "reasoning_steps": ["Step 1", "Step 2", "Step 3"],
    }
    mock_http_client.post.return_value = mock_response

    result = await graph_service.multi_hop_query("What diseases affect rice?", max_hops=2)
    assert isinstance(result, GraphRAGResponse)
    assert result.confidence == 0.75
    assert len(result.reasoning_steps) >= 2


@pytest.mark.asyncio
async def test_fallback_when_unavailable(graph_service, mock_http_client):
    """When EdgeQuake is unreachable, the service falls back gracefully."""
    mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

    result = await graph_service.query("nitrogen deficiency treatment")
    assert isinstance(result, GraphRAGResponse)
    # Fallback should still match the disease via local knowledge
    assert result.confidence > 0
    assert "nitrogen" in result.answer.lower() or result.confidence == 0.6
