"""Tests for answer generation."""

import pytest
from app.rag.generator import (
    format_sources_for_prompt,
    extract_citations,
    calculate_confidence,
    estimate_tokens
)


def test_format_sources_for_prompt(sample_chunks):
    """Test source formatting."""
    formatted = format_sources_for_prompt(sample_chunks)
    
    assert "[Source 1]" in formatted
    assert "[Source 2]" in formatted
    assert "src/auth.py" in formatted
    assert "```python" in formatted


def test_extract_citations(sample_chunks):
    """Test citation extraction."""
    answer = "The code [Source 1] shows authentication. Also see [Source 2] for utils."
    
    citations = extract_citations(answer, sample_chunks)
    
    assert len(citations) == 2
    assert citations[0]["file_path"] == "src/auth.py"
    assert citations[1]["file_path"] == "src/utils.py"


def test_calculate_confidence():
    """Test confidence calculation."""
    # Low confidence - no citations
    assert calculate_confidence("Short answer", [], []) == "low"
    
    # Medium confidence - one citation with enough content
    citations = [{"file_path": "test.py", "start_line": 1, "end_line": 10, "snippet": "..."}]
    medium_answer = "This is a medium length answer with one citation that provides enough context and detail. " * 2
    assert calculate_confidence(medium_answer, citations, [{}]) == "medium"
    
    # High confidence - multiple citations
    citations2 = citations + [{"file_path": "test2.py", "start_line": 1, "end_line": 10, "snippet": "..."}]
    assert calculate_confidence("This is a longer answer with multiple citations providing good coverage.", citations2, [{}, {}]) == "high"


def test_estimate_tokens():
    """Test token estimation."""
    text = "This is a test" * 100
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens == len(text) // 4