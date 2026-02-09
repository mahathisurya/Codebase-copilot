"""Tests for database operations."""

import pytest
from app.storage.db import (
    init_db,
    create_repo,
    get_repo,
    list_repos,
    update_repo_status,
    save_chunks,
    get_chunks
)
from app.storage.models import RepoStatus


@pytest.mark.asyncio
async def test_create_and_get_repo(test_settings):
    """Test repository creation and retrieval."""
    await init_db()
    
    repo_id = await create_repo(
        repo_url="https://github.com/test/repo",
        branch="main",
        display_name="Test Repo"
    )
    
    assert repo_id is not None
    
    repo = await get_repo(repo_id)
    assert repo is not None
    assert repo["repo_url"] == "https://github.com/test/repo"
    assert repo["display_name"] == "Test Repo"
    assert repo["status"] == RepoStatus.QUEUED.value


@pytest.mark.asyncio
async def test_list_repos(test_settings):
    """Test listing repositories."""
    await init_db()
    
    repo_id1 = await create_repo("https://github.com/test/repo1", "main", "Repo 1")
    repo_id2 = await create_repo("https://github.com/test/repo2", "main", "Repo 2")
    
    repos = await list_repos()
    assert len(repos) >= 2
    assert any(r["repo_id"] == repo_id1 for r in repos)
    assert any(r["repo_id"] == repo_id2 for r in repos)


@pytest.mark.asyncio
async def test_update_repo_status(test_settings):
    """Test updating repository status."""
    await init_db()
    
    repo_id = await create_repo("https://github.com/test/repo", "main", "Test")
    
    await update_repo_status(repo_id, RepoStatus.INDEXING)
    repo = await get_repo(repo_id)
    assert repo["status"] == RepoStatus.INDEXING.value
    
    await update_repo_status(repo_id, RepoStatus.READY)
    repo = await get_repo(repo_id)
    assert repo["status"] == RepoStatus.READY.value


@pytest.mark.asyncio
async def test_save_and_get_chunks(test_settings, sample_chunks):
    """Test saving and retrieving chunks."""
    await init_db()
    
    repo_id = await create_repo("https://github.com/test/repo", "main", "Test")
    
    await save_chunks(repo_id, sample_chunks)
    
    chunks = await get_chunks(repo_id)
    assert len(chunks) == len(sample_chunks)
    assert chunks[0]["chunk_id"] == sample_chunks[0]["chunk_id"]