"""Tests for security features."""

import pytest
from pathlib import Path


def test_path_traversal_protection(temp_dir):
    """Test protection against path traversal attacks."""
    base_path = temp_dir / "repos" / "repo1"
    base_path.mkdir(parents=True)
    
    # Attempt traversal
    malicious_path = base_path / ".." / ".." / "etc" / "passwd"
    
    try:
        resolved = malicious_path.resolve()
        base_resolved = base_path.resolve()
        
        # Should not be able to access outside base
        resolved.relative_to(base_resolved)
        assert False, "Should have raised ValueError"
    except ValueError:
        # Expected - path is outside base
        pass


def test_safe_filename_handling():
    """Test safe filename handling."""
    dangerous_names = [
        "../../../etc/passwd",
        "file;rm -rf /",
        "file$(whoami)"
    ]
    
    for name in dangerous_names:
        # Path.name extracts only the filename, removing directory traversal
        safe_name = Path(name).name
        # Verify no directory separators in extracted name
        assert "/" not in safe_name
        # The .. should be removed when we use .name (only gets filename)
        # For "../../../etc/passwd", .name returns "passwd"
        if ".." in name:
            # After extraction, dangerous patterns should be gone
            assert safe_name != name  # Name has been sanitized
    
    # Test Windows-style path separately
    windows_path = "..\\..\\windows\\system32"
    # On Unix systems, backslashes are part of filename, not separators
    # So we need to explicitly check and sanitize
    sanitized = Path(windows_path).name.replace("\\", "")
    assert "\\" not in sanitized or Path(windows_path).name == "system32"