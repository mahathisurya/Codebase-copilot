"""Tests for code parsing."""

import pytest
from pathlib import Path

from app.ingestion.parser import (
    detect_language,
    should_process_file,
    chunk_content
)


def test_detect_language():
    """Test language detection."""
    assert detect_language(Path("test.py")) == "python"
    assert detect_language(Path("test.js")) == "javascript"
    assert detect_language(Path("test.ts")) == "typescript"
    assert detect_language(Path("test.java")) == "java"
    assert detect_language(Path("test.unknown")) == "text"


def test_should_process_file(temp_dir):
    """Test file filtering."""
    # Create test files
    test_dir = temp_dir / "test_repo"
    test_dir.mkdir()
    
    # Should process
    py_file = test_dir / "main.py"
    py_file.write_text("print('hello')")
    assert should_process_file(py_file)
    
    js_file = test_dir / "utils.js"
    js_file.write_text("console.log('hello');")
    assert should_process_file(js_file)
    
    # Should not process - excluded directories
    node_modules_dir = test_dir / "node_modules"
    node_modules_dir.mkdir()
    assert not should_process_file(node_modules_dir / "package.json")
    
    git_dir = test_dir / ".git"
    git_dir.mkdir()
    assert not should_process_file(git_dir / "config")
    
    # Should not process - wrong extension
    assert not should_process_file(test_dir / "file.exe")


def test_chunk_content(sample_code):
    """Test content chunking."""
    chunks = chunk_content(sample_code, "auth.py", "python")
    
    assert len(chunks) > 0
    assert all("chunk_id" in c for c in chunks)
    assert all("file_path" in c for c in chunks)
    assert all("start_line" in c for c in chunks)
    assert all("end_line" in c for c in chunks)
    assert all("content" in c for c in chunks)
    
    # Check line ranges
    for chunk in chunks:
        assert chunk["start_line"] > 0
        assert chunk["end_line"] >= chunk["start_line"]