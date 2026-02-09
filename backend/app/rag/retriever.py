"""Retrieval logic with re-ranking."""

import logging
from typing import List, Dict, Any
import re

from app.indexing.embedder import get_embedding_model
from app.indexing.indexer import search_index
from app.storage.db import get_chunk_by_id
from app.config import settings

logger = logging.getLogger(__name__)


async def create_query_embedding(query: str) -> List[float]:
    """Create embedding for query."""
    model = get_embedding_model()
    
    if isinstance(model, object) and hasattr(model, 'embeddings'):
        # OpenAI API
        response = model.embeddings.create(
            model=settings.openai_embedding_model,
            input=[query]
        )
        return response.data[0].embedding
    else:
        # Local model
        embedding = model.encode([query], convert_to_numpy=True)[0]
        return embedding.tolist()


def calculate_keyword_score(query: str, chunk_content: str) -> float:
    """Calculate simple keyword overlap score for re-ranking."""
    query_words = set(re.findall(r'\w+', query.lower()))
    content_words = set(re.findall(r'\w+', chunk_content.lower()))
    
    if not query_words:
        return 0.0
    
    overlap = len(query_words & content_words)
    return overlap / len(query_words)


def rerank_chunks(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simple re-ranking based on keyword overlap."""
    if not chunks:
        return chunks
    
    # Calculate scores
    for chunk in chunks:
        keyword_score = calculate_keyword_score(query, chunk["content"])
        chunk["_rerank_score"] = keyword_score
    
    # Sort by rerank score (descending)
    reranked = sorted(chunks, key=lambda x: x.get("_rerank_score", 0), reverse=True)
    
    # Remove temporary score field
    for chunk in reranked:
        chunk.pop("_rerank_score", None)
    
    return reranked


async def retrieve_relevant_chunks(
    repo_id: str,
    query: str,
    top_k: int = 8,
    use_reranking: bool = True
) -> List[Dict[str, Any]]:
    """Retrieve relevant code chunks for a query with optional re-ranking.
    
    Args:
        repo_id: Repository identifier
        query: User query
        top_k: Number of chunks to retrieve
        use_reranking: Whether to apply keyword-based re-ranking
        
    Returns:
        List of relevant chunks with metadata
    """
    # Create query embedding
    query_embedding = await create_query_embedding(query)
    
    # Search FAISS index (retrieve more for re-ranking)
    retrieve_k = top_k * 2 if use_reranking else top_k
    chunk_ids = await search_index(repo_id, query_embedding, retrieve_k)
    
    # Fetch full chunks from database
    chunks = []
    for chunk_id in chunk_ids:
        chunk = await get_chunk_by_id(chunk_id)
        if chunk:
            chunks.append(chunk)
    
    # Apply re-ranking if enabled
    if use_reranking and len(chunks) > top_k:
        chunks = rerank_chunks(query, chunks)
        chunks = chunks[:top_k]
    
    logger.info(f"Retrieved and {'re-ranked ' if use_reranking else ''}{len(chunks)} chunks for query")
    return chunks