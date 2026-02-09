"""Chat and Q&A endpoints."""

import logging
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.retriever import retrieve_relevant_chunks
from app.rag.generator import generate_answer
from app.storage.db import get_repo

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")


class Citation(BaseModel):
    """Source citation."""
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class Telemetry(BaseModel):
    """Request telemetry."""
    latency_ms: float
    tokens_estimate: int
    cost_usd_estimate: float


class ChatRequest(BaseModel):
    """Chat request."""
    repo_id: str = Field(..., description="Repository ID")
    messages: List[ChatMessage] = Field(..., description="Conversation history")
    top_k: int = Field(default=8, ge=1, le=20, description="Number of chunks to retrieve")
    model: str = Field(default="openai", description="Model: openai or local")


class ChatResponse(BaseModel):
    """Chat response."""
    answer_markdown: str
    citations: List[Citation]
    confidence: str = Field(description="low, medium, or high")
    telemetry: Telemetry


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the codebase."""
    start_time = time.time()
    
    try:
        # Validate repo exists
        repo = await get_repo(request.repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        if repo["status"] != "ready":
            raise HTTPException(
                status_code=400,
                detail=f"Repository not ready. Status: {repo['status']}"
            )
        
        # Get latest user message
        if not request.messages or request.messages[-1].role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
        
        query = request.messages[-1].content
        
        # Retrieve relevant chunks
        logger.info(f"Retrieving chunks for query: {query[:100]}")
        retrieved_chunks = await retrieve_relevant_chunks(
            repo_id=request.repo_id,
            query=query,
            top_k=request.top_k
        )
        
        if not retrieved_chunks:
            return ChatResponse(
                answer_markdown="I couldn't find any relevant code in the repository for your question. Could you rephrase or provide more context?",
                citations=[],
                confidence="low",
                telemetry=Telemetry(
                    latency_ms=(time.time() - start_time) * 1000,
                    tokens_estimate=0,
                    cost_usd_estimate=0.0
                )
            )
        
        # Generate answer
        logger.info(f"Generating answer with {len(retrieved_chunks)} chunks")
        result = await generate_answer(
            query=query,
            chunks=retrieved_chunks,
            conversation_history=request.messages[:-1],
            model=request.model
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ChatResponse(
            answer_markdown=result["answer"],
            citations=[
                Citation(
                    file_path=c["file_path"],
                    start_line=c["start_line"],
                    end_line=c["end_line"],
                    snippet=c["snippet"]
                )
                for c in result["citations"]
            ],
            confidence=result["confidence"],
            telemetry=Telemetry(
                latency_ms=latency_ms,
                tokens_estimate=result["tokens_estimate"],
                cost_usd_estimate=result["cost_estimate"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))