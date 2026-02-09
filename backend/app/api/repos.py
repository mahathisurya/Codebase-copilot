"""Repository management endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.ingestion.cloner import clone_repository
from app.ingestion.parser import parse_repository, detect_language
from app.indexing.embedder import create_embeddings
from app.indexing.indexer import build_faiss_index
from app.storage.db import (
    create_repo,
    get_repo,
    list_repos,
    update_repo_status,
    save_chunks,
)
from app.storage.models import RepoStatus
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateRepoRequest(BaseModel):
    """Request to create/index a repository."""

    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to clone")
    github_token: Optional[str] = Field(default=None, description="GitHub access token")
    display_name: Optional[str] = Field(default=None, description="Display name")


class RepoResponse(BaseModel):
    """Repository response."""

    repo_id: str
    status: str
    message: str


class RepoListItem(BaseModel):
    """Repository list item."""

    repo_id: str
    display_name: str
    status: str
    last_indexed_at: Optional[str]
    file_count: Optional[int] = 0
    chunk_count: Optional[int] = 0


class FileItem(BaseModel):
    """File or directory item."""

    path: str
    is_dir: bool
    language: Optional[str] = None


class FileContentResponse(BaseModel):
    """File content response."""

    path: str
    content: str
    language: str
    line_count: int


async def index_repository_task(
    repo_id: str,
    repo_url: str,
    branch: str,
    github_token: Optional[str],
):
    """Background task to index a repository."""
    try:
        logger.info(f"Starting indexing for repo {repo_id}")

        # Update status to indexing
        await update_repo_status(repo_id, RepoStatus.INDEXING)

        # Clone repository
        logger.info(f"Cloning repository {repo_url}")
        repo_path = await clone_repository(repo_id, repo_url, branch, github_token)

        # Parse files
        logger.info("Parsing repository files")
        chunks = await parse_repository(repo_id, repo_path)

        if not chunks:
            raise ValueError("No code chunks extracted from repository")

        logger.info(f"Extracted {len(chunks)} chunks")

        # Create embeddings
        logger.info("Creating embeddings")
        chunks_with_embeddings = await create_embeddings(chunks)

        # Build FAISS index
        logger.info("Building FAISS index")
        await build_faiss_index(repo_id, chunks_with_embeddings)

        # Save to database
        logger.info("Saving chunks to database")
        await save_chunks(repo_id, chunks_with_embeddings)

        # Update status to ready
        await update_repo_status(repo_id, RepoStatus.READY)
        logger.info(f"Repository {repo_id} indexed successfully")

    except Exception as e:
        logger.error(f"Error indexing repository {repo_id}: {e}", exc_info=True)
        await update_repo_status(repo_id, RepoStatus.ERROR, str(e))


@router.post("/repos", response_model=RepoResponse)
async def create_repository(
    request: CreateRepoRequest,
    background_tasks: BackgroundTasks,
) -> RepoResponse:
    """Create and index a new repository."""
    try:
        display_name = request.display_name or request.repo_url.split("/")[-1]

        repo_id = await create_repo(
            repo_url=request.repo_url,
            branch=request.branch,
            display_name=display_name,
        )

        background_tasks.add_task(
            index_repository_task,
            repo_id,
            request.repo_url,
            request.branch,
            request.github_token,
        )

        return RepoResponse(
            repo_id=repo_id,
            status="queued",
            message="Repository queued for indexing",
        )

    except Exception as e:
        logger.error(f"Error creating repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos", response_model=List[RepoListItem])
async def list_repositories() -> List[RepoListItem]:
    """List all repositories."""
    try:
        repos = await list_repos()
        return [
            RepoListItem(
                repo_id=repo["repo_id"],
                display_name=repo["display_name"],
                status=repo["status"],
                last_indexed_at=repo.get("indexed_at"),
                file_count=repo.get("file_count", 0),
                chunk_count=repo.get("chunk_count", 0),
            )
            for repo in repos
        ]

    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{repo_id}/files", response_model=List[FileItem])
async def list_files(
    repo_id: str,
    path: Optional[str] = None,
) -> List[FileItem]:
    """List files in a repository."""
    try:
        repo = await get_repo(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_path = settings.repos_dir / repo_id
        if not repo_path.exists():
            return []

        target_path = repo_path / path if path else repo_path
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")

        items: List[FileItem] = []
        for item in sorted(target_path.iterdir()):
            rel_path = str(item.relative_to(repo_path))
            items.append(
                FileItem(
                    path=rel_path,
                    is_dir=item.is_dir(),
                    language=detect_language(item) if item.is_file() else None,
                )
            )

        return items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{repo_id}/file", response_model=FileContentResponse)
async def get_file_content(
    repo_id: str,
    path: str,
) -> FileContentResponse:
    """Get file content."""
    try:
        repo = await get_repo(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        file_path = settings.repos_dir / repo_id / path

        # Security: ensure path is within repo directory
        try:
            file_path = file_path.resolve()
            repo_path = (settings.repos_dir / repo_id).resolve()
            file_path.relative_to(repo_path)
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        line_count = len(content.splitlines())

        return FileContentResponse(
            path=path,
            content=content,
            language=detect_language(file_path),
            line_count=line_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
