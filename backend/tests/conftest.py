"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
import shutil

from app.config import Settings


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def test_settings(temp_dir):
    """Test settings with temporary directories."""
    settings = Settings(
        data_dir=temp_dir / "data",
        repos_dir=temp_dir / "repos",
        faiss_index_dir=temp_dir / "data/faiss",
        sqlite_db_path=temp_dir / "data/test.db",
        openai_api_key="test-key"
    )
    return settings


@pytest.fixture
def sample_code():
    """Sample code content for testing."""
    return '''def authenticate(user: User) -> Token:
    """Authenticate user and return token."""
    if not user.is_active:
        raise AuthError("User not active")
    
    token = create_jwt_token(user.id)
    return token
'''


@pytest.fixture
def sample_chunks():
    """Sample code chunks for testing."""
    import uuid
    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "file_path": "src/auth.py",
            "language": "python",
            "start_line": 1,
            "end_line": 8,
            "content": "def authenticate(user):\n    return token",
            "content_hash": "hash1"
        },
        {
            "chunk_id": str(uuid.uuid4()),
            "file_path": "src/utils.py",
            "language": "python",
            "start_line": 10,
            "end_line": 20,
            "content": "def helper():\n    pass",
            "content_hash": "hash2"
        }
    ]