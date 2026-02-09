"""Database models."""

from enum import Enum


class RepoStatus(str, Enum):
    """Repository status."""
    QUEUED = "queued"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"