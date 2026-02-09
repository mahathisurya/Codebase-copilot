"""Answer generation with citations."""

import logging
import re
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


def format_sources_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks as sources for the prompt."""
    sources = []
    for i, chunk in enumerate(chunks, 1):
        source = f"[Source {i}]\n"
        source += f"File: {chunk['file_path']}\n"
        source += f"Lines: {chunk['start_line']}-{chunk['end_line']}\n"
        source += f"Language: {chunk.get('language', 'unknown')}\n"
        source += f"```{chunk.get('language', '')}\n{chunk['content']}\n```\n"
        sources.append(source)
    return "\n".join(sources)


def build_rag_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    conversation_history: List[Any],
) -> str:
    """Build the RAG prompt with sources and instructions."""
    sources = format_sources_for_prompt(chunks)

    history_text = ""
    if conversation_history:
        history_text = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-4:]:
            role = msg.role if hasattr(msg, "role") else msg["role"]
            content = msg.content if hasattr(msg, "content") else msg["content"]
            history_text += f"{role.title()}: {content}\n"

    prompt = f"""You are a code assistant helping developers understand a codebase. Answer the question using ONLY the provided source code below.

CRITICAL RULES:
1. Every factual claim MUST be cited using [Source N] format
2. If you cannot answer from the sources, say "I don't have enough information in the codebase to answer this"
3. Do not make assumptions or add information not present in the sources
4. When referencing code, always cite the specific source

{sources}
{history_text}

Question: {query}

Provide a clear, well-structured answer with proper citations. Format your response in markdown.

Answer:"""
    return prompt


def extract_citations(answer: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract citations from the answer and map to source chunks."""
    citations = []

    citation_pattern = r"\[Source (\d+)\]"
    matches = re.findall(citation_pattern, answer)
    unique_sources = set(int(m) for m in matches)

    for source_num in sorted(unique_sources):
        if 1 <= source_num <= len(chunks):
            chunk = chunks[source_num - 1]
            snippet = chunk["content"][:200]
            if len(chunk["content"]) > 200:
                snippet += "..."
            citations.append(
                {
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "snippet": snippet,
                }
            )

    return citations


def calculate_confidence(answer: str, citations: List[Dict], chunks: List[Dict]) -> str:
    """Calculate confidence level based on citations and answer quality."""
    if not citations:
        return "low"

    if len(answer) < 50:
        return "low"

    citation_count = len(citations)
    words = len(answer.split())
    if words > 100 and citation_count < 2:
        return "medium"

    uncertainty_phrases = [
        "i don't have",
        "not sure",
        "unclear",
        "might",
        "possibly",
        "i cannot find",
        "no information",
        "error generating answer",
    ]
    answer_lower = answer.lower()
    if any(p in answer_lower for p in uncertainty_phrases):
        return "low"

    if citation_count >= 2:
        return "high"
    if citation_count == 1:
        return "medium"
    return "low"


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ~= 4 characters)."""
    return len(text) // 4


def build_local_fallback_answer(chunks: List[Dict[str, Any]], max_chunks: int = 3) -> str:
    """
    Local/offline fallback answer:
    - Shows top chunks (retrieval results) as evidence
    - Still includes [Source N] citations (so citations panel works)
    """
    if not chunks:
        return (
            "I couldn't find any relevant code in the repository for your question.\n\n"
            "*Tip: try asking with a filename, function name, or keyword.*"
        )

    answer = (
        "⚠️ **LLM generation is disabled or unavailable** (no valid OpenAI key / OpenAI turned off).\n"
        "Showing the most relevant retrieved excerpts instead:\n\n"
    )

    for i, chunk in enumerate(chunks[:max_chunks], 1):
        answer += (
            f"### `{chunk['file_path']}` (lines {chunk['start_line']}-{chunk['end_line']}) [Source {i}]\n"
            f"```{chunk.get('language', '')}\n{chunk['content'][:500]}\n```\n\n"
        )

    answer += "*Note: To get richer explanations, provide a valid OpenAI key and set model=openai.*"
    return answer


async def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    conversation_history: List[Any],
    model: str = "openai",
) -> Dict[str, Any]:
    """
    Generate answer using OpenAI if available, otherwise fallback to local excerpt-based answer.
    Always returns a consistent response shape.
    """
    prompt = build_rag_prompt(query, chunks, conversation_history)

    tokens_estimate = estimate_tokens(prompt)
    cost_estimate = 0.0

    use_openai = bool(settings.openai_api_key) and model == "openai"

    if use_openai:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)

            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful code assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            answer = response.choices[0].message.content or ""
            tokens_estimate = response.usage.total_tokens if response.usage else tokens_estimate

            # Rough cost estimate (placeholder; adjust pricing as needed)
            cost_estimate = (tokens_estimate / 1000) * 0.01

        except Exception as e:
            # If OpenAI fails (invalid key, quota, network), fall back locally instead of returning an error string
            logger.error(f"OpenAI API error, falling back to local answer: {e}", exc_info=True)
            answer = build_local_fallback_answer(chunks)

    else:
        answer = build_local_fallback_answer(chunks)

    citations = extract_citations(answer, chunks)
    confidence = calculate_confidence(answer, citations, chunks)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "tokens_estimate": tokens_estimate,
        "cost_estimate": cost_estimate,
    }
