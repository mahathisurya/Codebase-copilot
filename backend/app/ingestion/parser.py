"""Code parsing and chunking."""

import hashlib
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# File extensions to process
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt",
    ".scala", ".sh", ".bash", ".yaml", ".yml", ".json", ".xml",
    ".md", ".rst", ".txt", ".toml", ".ini", ".cfg"
}

# Directories to exclude
EXCLUDE_DIRS = {
    "node_modules", "dist", "build", ".git", ".next", "venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache", "target", "bin",
    ".idea", ".vscode", "coverage", "htmlcov"
}

# Language mapping
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".rst": "restructuredtext",
}


def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    return LANGUAGE_MAP.get(file_path.suffix, "text")


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed."""
    # Check extension
    if file_path.suffix not in CODE_EXTENSIONS:
        return False
    
    # Check if in excluded directory
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False
    
    # Check file size (skip files > 1MB)
    try:
        if file_path.stat().st_size > 1_000_000:
            return False
    except:
        return False
    
    return True


def chunk_content(content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
    """Chunk file content into smaller pieces with line tracking.
    
    Strategy: Split by lines, create overlapping chunks.
    """
    lines = content.splitlines()
    
    if not lines:
        return []
    
    chunks = []
    chunk_size_lines = 50  # ~200-500 tokens for most code
    overlap_lines = 5
    
    i = 0
    while i < len(lines):
        end = min(i + chunk_size_lines, len(lines))
        chunk_lines = lines[i:end]
        chunk_content = "\n".join(chunk_lines)
        
        # Skip empty or very small chunks
        if len(chunk_content.strip()) < 10:
            i += chunk_size_lines - overlap_lines
            continue
        
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "file_path": file_path,
            "language": language,
            "start_line": i + 1,  # 1-indexed
            "end_line": end,
            "content": chunk_content,
            "content_hash": hashlib.sha256(chunk_content.encode()).hexdigest()
        }
        chunks.append(chunk)
        
        # Move forward with overlap
        i += chunk_size_lines - overlap_lines
    
    return chunks


async def parse_repository(repo_id: str, repo_path: Path) -> List[Dict[str, Any]]:
    """Parse repository and extract code chunks with progress tracking.
    
    Args:
        repo_id: Repository identifier
        repo_path: Path to cloned repository
        
    Returns:
        List of code chunks with metadata
    """
    all_chunks = []
    file_count = 0
    skipped_count = 0
    error_count = 0
    
    logger.info(f"Parsing repository at {repo_path}")
    
    # Collect all files first for better progress tracking
    files_to_process = [
        f for f in repo_path.rglob("*") 
        if f.is_file() and should_process_file(f)
    ]
    
    total_files = len(files_to_process)
    logger.info(f"Found {total_files} files to process")
    
    for idx, file_path in enumerate(files_to_process, 1):
        try:
            # Read file content with size check
            if file_path.stat().st_size > 2_000_000:  # 2MB limit
                logger.warning(f"Skipping large file: {file_path} ({file_path.stat().st_size} bytes)")
                skipped_count += 1
                continue
            
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            
            # Skip empty files
            if not content.strip():
                skipped_count += 1
                continue
            
            # Get relative path
            rel_path = str(file_path.relative_to(repo_path))
            
            # Detect language
            language = detect_language(file_path)
            
            # Chunk the content
            chunks = chunk_content(content, rel_path, language)
            all_chunks.extend(chunks)
            
            file_count += 1
            
            # Progress logging
            if idx % 50 == 0 or idx == total_files:
                progress = (idx / total_files) * 100
                logger.info(
                    f"Progress: {progress:.1f}% ({idx}/{total_files}) - "
                    f"Processed: {file_count}, Chunks: {len(all_chunks)}, "
                    f"Skipped: {skipped_count}, Errors: {error_count}"
                )
                
        except UnicodeDecodeError:
            logger.debug(f"Binary file skipped: {file_path}")
            skipped_count += 1
        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")
            error_count += 1
            continue
    
    logger.info(
        f"Parsing complete: {file_count} files processed, {len(all_chunks)} chunks created, "
        f"{skipped_count} skipped, {error_count} errors"
    )
    
    if not all_chunks:
        logger.warning("No code chunks extracted from repository")
    
    return all_chunks