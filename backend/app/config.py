"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import List, Union
import json


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: Union[List[str], str] = ["http://localhost:3000"]
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON array string or comma-separated
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Storage
    data_dir: Path = Path("./data")
    repos_dir: Path = Path("./repos")
    faiss_index_dir: Path = Path("./data/faiss")
    sqlite_db_path: Path = Path("./data/copilot.db")
    
    # RAG
    chunk_size: int = 400
    chunk_overlap: int = 50
    top_k_retrieval: int = 8
    min_confidence_threshold: float = 0.6
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    
    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    
    # Local models
    use_local_embeddings: bool = False
    local_embedding_model: str = "all-MiniLM-L6-v2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.repos_dir.mkdir(exist_ok=True, parents=True)
        self.faiss_index_dir.mkdir(exist_ok=True, parents=True)


settings = Settings()