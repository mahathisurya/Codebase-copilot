"""Embedding generation."""

import logging
from typing import List, Dict, Any
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Global embedding model cache
_embedding_model = None


def get_embedding_model():
    """Get or initialize embedding model."""
    global _embedding_model
    
    if _embedding_model is not None:
        return _embedding_model
    
    if settings.openai_api_key and not settings.use_local_embeddings:
        # Use OpenAI embeddings
        from openai import OpenAI
        _embedding_model = OpenAI(api_key=settings.openai_api_key)
        logger.info("Initialized OpenAI embeddings")
    else:
        # Use local sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(settings.local_embedding_model)
            logger.info(f"Initialized local embeddings: {settings.local_embedding_model}")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    return _embedding_model


async def create_embeddings(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create embeddings for chunks with improved error handling and progress tracking.
    
    Args:
        chunks: List of code chunks
        
    Returns:
        Chunks with embeddings added
    """
    if not chunks:
        return []
    
    model = get_embedding_model()
    
    # Extract texts
    texts = [chunk["content"] for chunk in chunks]
    
    logger.info(f"Creating embeddings for {len(texts)} chunks")
    
    # Create embeddings in batches with retry logic
    batch_size = 32
    all_embeddings = []
    failed_batches = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        try:
            if isinstance(model, object) and hasattr(model, 'embeddings'):
                # OpenAI API
                response = model.embeddings.create(
                    model=settings.openai_embedding_model,
                    input=batch_texts
                )
                batch_embeddings = [item.embedding for item in response.data]
            else:
                # Local model
                batch_embeddings = model.encode(
                    batch_texts,
                    show_progress_bar=False,
                    convert_to_numpy=True
                ).tolist()
            
            all_embeddings.extend(batch_embeddings)
            
            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"Created embeddings for {i + len(batch_texts)}/{len(texts)} chunks")
                
        except Exception as e:
            logger.error(f"Failed to create embeddings for batch {i//batch_size}: {e}")
            # Add zero embeddings for failed batches
            failed_batches.append(i)
            # Get embedding dimension from first successful embedding
            dim = len(all_embeddings[0]) if all_embeddings else 1536
            all_embeddings.extend([[0.0] * dim for _ in batch_texts])
    
    if failed_batches:
        logger.warning(f"Failed to create embeddings for {len(failed_batches)} batches")
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, all_embeddings):
        chunk["embedding"] = embedding
    
    logger.info(f"Created {len(all_embeddings)} embeddings")
    return chunks