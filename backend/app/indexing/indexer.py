"""FAISS index management."""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import faiss

from app.config import settings

logger = logging.getLogger(__name__)


def get_index_path(repo_id: str) -> Path:
    """Get path to FAISS index file."""
    return settings.faiss_index_dir / f"{repo_id}.faiss"


def get_mapping_path(repo_id: str) -> Path:
    """Get path to chunk ID mapping file."""
    return settings.faiss_index_dir / f"{repo_id}_mapping.pkl"


async def build_faiss_index(repo_id: str, chunks: List[Dict[str, Any]]):
    """Build and save FAISS index for repository.
    
    Args:
        repo_id: Repository identifier
        chunks: List of chunks with embeddings
    """
    if not chunks:
        raise ValueError("No chunks to index")
    
    # Extract embeddings
    embeddings = np.array([chunk["embedding"] for chunk in chunks], dtype=np.float32)
    dimension = embeddings.shape[1]
    
    logger.info(f"Building FAISS index with {len(embeddings)} vectors of dimension {dimension}")
    
    # Create FAISS index (using L2 distance)
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index
    index_path = get_index_path(repo_id)
    faiss.write_index(index, str(index_path))
    
    # Save chunk ID mapping (index position -> chunk_id)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    mapping_path = get_mapping_path(repo_id)
    with open(mapping_path, "wb") as f:
        pickle.dump(chunk_ids, f)
    
    logger.info(f"FAISS index saved to {index_path}")


async def search_index(repo_id: str, query_embedding: List[float], top_k: int = 8) -> List[str]:
    """Search FAISS index for similar chunks.
    
    Args:
        repo_id: Repository identifier
        query_embedding: Query embedding vector
        top_k: Number of results to return
        
    Returns:
        List of chunk IDs
    """
    index_path = get_index_path(repo_id)
    mapping_path = get_mapping_path(repo_id)
    
    if not index_path.exists() or not mapping_path.exists():
        raise ValueError(f"Index not found for repository {repo_id}")
    
    # Load index
    index = faiss.read_index(str(index_path))
    
    # Load mapping
    with open(mapping_path, "rb") as f:
        chunk_ids = pickle.load(f)
    
    # Search
    query_vector = np.array([query_embedding], dtype=np.float32)
    distances, indices = index.search(query_vector, top_k)
    
    # Return chunk IDs
    result_chunk_ids = [chunk_ids[idx] for idx in indices[0] if idx < len(chunk_ids)]
    
    logger.info(f"Retrieved {len(result_chunk_ids)} chunks for query")
    
    return result_chunk_ids