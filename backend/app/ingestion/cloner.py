"""Repository cloning utilities."""

import logging
import shutil
from pathlib import Path
from typing import Optional
import git

from app.config import settings

logger = logging.getLogger(__name__)


async def clone_repository(
    repo_id: str,
    repo_url: str,
    branch: str = "main",
    github_token: Optional[str] = None
) -> Path:
    """Clone a GitHub repository.
    
    Args:
        repo_id: Unique repository identifier
        repo_url: GitHub repository URL
        branch: Branch to clone
        github_token: Optional GitHub access token
        
    Returns:
        Path to cloned repository
    """
    repo_path = settings.repos_dir / repo_id
    
    # Remove existing directory if present
    if repo_path.exists():
        shutil.rmtree(repo_path)
    
    # Inject token into URL for private repos
    if github_token and "github.com" in repo_url:
        # Convert https://github.com/user/repo to https://token@github.com/user/repo
        repo_url = repo_url.replace("https://", f"https://{github_token}@")
    
    try:
        logger.info(f"Cloning repository from {repo_url.replace(github_token or '', '***')} to {repo_path}")
        
        git.Repo.clone_from(
            repo_url,
            repo_path,
            branch=branch,
            depth=1  # Shallow clone for faster cloning
        )
        
        logger.info(f"Successfully cloned repository to {repo_path}")
        return repo_path
        
    except git.GitCommandError as e:
        logger.error(f"Git clone failed: {e}")
        raise ValueError(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during clone: {e}")
        raise