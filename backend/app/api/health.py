"""Health check endpoints with comprehensive diagnostics."""

import logging
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.storage.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Enhanced health check response."""
    ok: bool
    service: str = "codebase-copilot"
    version: str = "1.0.0"
    database: str = "unknown"
    repos_count: int = 0
    openai_configured: bool = False
    local_embeddings_enabled: bool = False


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with system diagnostics."""
    status = {
        "ok": True,
        "service": "codebase-copilot",
        "version": "1.0.0"
    }
    
    # Check database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM repositories")
            repo_count = cursor.fetchone()[0]
            status["database"] = "healthy"
            status["repos_count"] = repo_count
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status["database"] = "unhealthy"
        status["ok"] = False
        status["repos_count"] = 0
    
    # Check directories
    status["data_dir_exists"] = settings.data_dir.exists()
    status["repos_dir_exists"] = settings.repos_dir.exists()
    status["faiss_dir_exists"] = settings.faiss_index_dir.exists()
    
    # Check OpenAI key
    status["openai_configured"] = bool(settings.openai_api_key)
    status["local_embeddings_enabled"] = settings.use_local_embeddings
    
    return status