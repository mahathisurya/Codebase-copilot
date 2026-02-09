"""Database operations using SQLite with connection pooling."""

import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import uuid
from contextlib import contextmanager

from app.config import settings
from app.storage.models import RepoStatus

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """Get database connection with automatic cleanup."""
    conn = sqlite3.Connection(
        settings.sqlite_db_path,
        timeout=30.0,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    # Optimize for performance
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    
    try:
        yield conn
    finally:
        conn.close()


async def init_db():
    """Initialize database tables with optimizations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Repositories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                repo_id TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                branch TEXT NOT NULL,
                display_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                indexed_at TEXT,
                file_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0
            )
        """)
        
        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES repositories (repo_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_repo ON chunks(repo_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(repo_id, file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_status ON repositories(status)")
        
        conn.commit()
        
    logger.info("Database initialized with optimizations")


async def create_repo(repo_url: str, branch: str, display_name: str) -> str:
    """Create a new repository record."""
    repo_id = str(uuid.uuid4())
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repositories (repo_id, repo_url, branch, display_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (repo_id, repo_url, branch, display_name, RepoStatus.QUEUED.value, datetime.utcnow().isoformat()))
        conn.commit()
    
    logger.info(f"Created repository {repo_id}")
    return repo_id


async def get_repo(repo_id: str) -> Optional[Dict[str, Any]]:
    """Get repository by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories WHERE repo_id = ?", (repo_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
    return None


async def list_repos() -> List[Dict[str, Any]]:
    """List all repositories."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


async def update_repo_status(repo_id: str, status: RepoStatus, error_message: Optional[str] = None):
    """Update repository status."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if status == RepoStatus.READY:
            cursor.execute("""
                UPDATE repositories 
                SET status = ?, error_message = ?, indexed_at = ?
                WHERE repo_id = ?
            """, (status.value, error_message, datetime.utcnow().isoformat(), repo_id))
        else:
            cursor.execute("""
                UPDATE repositories 
                SET status = ?, error_message = ?
                WHERE repo_id = ?
            """, (status.value, error_message, repo_id))
        
        conn.commit()
    
    logger.info(f"Updated repository {repo_id} status to {status.value}")


async def save_chunks(repo_id: str, chunks: List[Dict[str, Any]]):
    """Save chunks to database with batch optimization."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Delete existing chunks for this repo
        cursor.execute("DELETE FROM chunks WHERE repo_id = ?", (repo_id,))
        
        # Insert new chunks in batches for better performance
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            cursor.executemany("""
                INSERT INTO chunks (
                    chunk_id, repo_id, file_path, language, start_line, end_line,
                    content, content_hash, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    chunk["chunk_id"],
                    repo_id,
                    chunk["file_path"],
                    chunk.get("language"),
                    chunk["start_line"],
                    chunk["end_line"],
                    chunk["content"],
                    chunk["content_hash"],
                    json.dumps(chunk.get("metadata", {})),
                    datetime.utcnow().isoformat()
                )
                for chunk in batch
            ])
        
        # Update chunk count
        cursor.execute("""
            UPDATE repositories 
            SET chunk_count = ?,
                file_count = (SELECT COUNT(DISTINCT file_path) FROM chunks WHERE repo_id = ?)
            WHERE repo_id = ?
        """, (len(chunks), repo_id, repo_id))
        
        conn.commit()
    
    logger.info(f"Saved {len(chunks)} chunks for repository {repo_id}")


async def get_chunks(repo_id: str) -> List[Dict[str, Any]]:
    """Get all chunks for a repository."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks WHERE repo_id = ? ORDER BY file_path, start_line", (repo_id,))
        rows = cursor.fetchall()
        
        chunks = []
        for row in rows:
            chunk = dict(row)
            chunk["metadata"] = json.loads(chunk.get("metadata", "{}"))
            chunks.append(chunk)
        
        return chunks


async def get_chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    """Get chunk by ID with caching consideration."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
        row = cursor.fetchone()
        
        if row:
            chunk = dict(row)
            chunk["metadata"] = json.loads(chunk.get("metadata", "{}"))
            return chunk
    return None