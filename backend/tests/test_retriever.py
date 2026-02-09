"""Tests for retrieval."""

import pytest
from app.rag.retriever import create_query_embedding


@pytest.mark.asyncio
async def test_create_query_embedding(test_settings):
    """Test query embedding creation."""
    # This test requires either OpenAI key or sentence-transformers
    # For CI, we'll just check the function exists
    try:
        embedding = await create_query_embedding("test query")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    except (RuntimeError, ImportError):
        # Expected if no API key or library
        pytest.skip("Embedding model not available")