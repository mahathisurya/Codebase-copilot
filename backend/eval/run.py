"""Evaluation runner."""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.generator import generate_answer
from app.storage.db import get_repo

logger = logging.getLogger(__name__)


async def load_eval_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load evaluation dataset from JSON file."""
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data.get("questions", [])


async def evaluate_retrieval_precision(
    retrieved_chunks: List[Dict],
    expected_files: List[str]
) -> float:
    """Calculate retrieval precision@k.
    
    Checks if retrieved chunks contain expected files.
    """
    if not expected_files or not retrieved_chunks:
        return 0.0
    
    retrieved_files = {chunk["file_path"] for chunk in retrieved_chunks}
    relevant_count = sum(1 for f in expected_files if f in retrieved_files)
    
    return relevant_count / len(expected_files)


async def evaluate_citation_precision(
    citations: List[Dict],
    chunks: List[Dict]
) -> float:
    """Calculate citation precision.
    
    Checks if citations point to actual retrieved content.
    """
    if not citations:
        return 0.0
    
    valid_citations = 0
    for citation in citations:
        # Check if citation matches a retrieved chunk
        for chunk in chunks:
            if (chunk["file_path"] == citation["file_path"] and
                chunk["start_line"] <= citation["start_line"] <= chunk["end_line"]):
                valid_citations += 1
                break
    
    return valid_citations / len(citations)


async def evaluate_faithfulness(
    answer: str,
    chunks: List[Dict],
    use_llm: bool = False
) -> float:
    """Calculate faithfulness score.
    
    Checks if answer is grounded in retrieved sources.
    """
    if not chunks:
        return 0.0
    
    if use_llm and settings.openai_api_key:
        # LLM-as-judge evaluation
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        sources_text = "\n\n".join([
            f"Source {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(chunks)
        ])
        
        prompt = f"""Rate the faithfulness of the answer to the provided sources on a scale of 0.0 to 1.0.

Sources:
{sources_text}

Answer:
{answer}

Provide only a single number between 0.0 and 1.0, where:
- 1.0 = All claims are directly supported by sources
- 0.5 = Some claims supported, some not
- 0.0 = No claims are supported

Score:"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            return float(score_text)
            
        except Exception as e:
            logger.error(f"LLM-as-judge failed: {e}")
            return 0.5
    else:
        # Heuristic: check keyword overlap
        answer_lower = answer.lower()
        sources_text = " ".join(chunk["content"].lower() for chunk in chunks)
        
        # Simple word overlap
        answer_words = set(answer_lower.split())
        source_words = set(sources_text.split())
        
        overlap = len(answer_words & source_words)
        total = len(answer_words)
        
        return min(overlap / total, 1.0) if total > 0 else 0.0


async def evaluate_question(
    repo_id: str,
    question: Dict[str, Any],
    use_llm_judge: bool = False
) -> Dict[str, Any]:
    """Evaluate a single question."""
    query = question["question"]
    expected_files = question.get("expected_files", [])
    
    start_time = datetime.now()
    
    # Retrieve chunks
    chunks = await retrieve_relevant_chunks(repo_id, query, top_k=8)
    
    # Generate answer
    result = await generate_answer(query, chunks, [], model="openai")
    
    latency = (datetime.now() - start_time).total_seconds() * 1000
    
    # Calculate metrics
    retrieval_precision = await evaluate_retrieval_precision(chunks, expected_files)
    citation_precision = await evaluate_citation_precision(result["citations"], chunks)
    faithfulness = await evaluate_faithfulness(result["answer"], chunks, use_llm_judge)
    
    return {
        "question": query,
        "answer": result["answer"],
        "retrieval_precision": retrieval_precision,
        "citation_precision": citation_precision,
        "faithfulness": faithfulness,
        "confidence": result["confidence"],
        "latency_ms": latency,
        "num_chunks_retrieved": len(chunks),
        "num_citations": len(result["citations"])
    }


async def run_evaluation(
    repo_id: str,
    dataset_path: str,
    use_llm_judge: bool = False
) -> Dict[str, Any]:
    """Run full evaluation suite."""
    logger.info(f"Loading evaluation dataset from {dataset_path}")
    questions = await load_eval_dataset(dataset_path)
    
    logger.info(f"Evaluating {len(questions)} questions")
    
    results = []
    for i, question in enumerate(questions, 1):
        logger.info(f"Evaluating question {i}/{len(questions)}: {question['question'][:50]}...")
        
        result = await evaluate_question(repo_id, question, use_llm_judge)
        results.append(result)
    
    # Calculate aggregate metrics
    avg_retrieval_precision = sum(r["retrieval_precision"] for r in results) / len(results)
    avg_citation_precision = sum(r["citation_precision"] for r in results) / len(results)
    avg_faithfulness = sum(r["faithfulness"] for r in results) / len(results)
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo_id": repo_id,
        "dataset": dataset_path,
        "num_questions": len(questions),
        "metrics": {
            "retrieval_precision_at_k": avg_retrieval_precision,
            "citation_precision": avg_citation_precision,
            "faithfulness_score": avg_faithfulness,
            "avg_latency_ms": avg_latency
        },
        "results": results
    }
    
    return report


def print_report(report: Dict[str, Any]):
    """Print evaluation report to console."""
    print("\n" + "="*60)
    print("EVALUATION REPORT")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Repository: {report['repo_id']}")
    print(f"Questions: {report['num_questions']}")
    print("\n" + "-"*60)
    print("METRICS")
    print("-"*60)
    
    metrics = report['metrics']
    print(f"{'Metric':<30} {'Score':>10}")
    print("-"*60)
    print(f"{'Retrieval Precision@K':<30} {metrics['retrieval_precision_at_k']:>10.3f}")
    print(f"{'Citation Precision':<30} {metrics['citation_precision']:>10.3f}")
    print(f"{'Faithfulness Score':<30} {metrics['faithfulness_score']:>10.3f}")
    print(f"{'Avg Latency (ms)':<30} {metrics['avg_latency_ms']:>10.1f}")
    print("="*60 + "\n")


async def main():
    """Main evaluation entry point."""
    parser = argparse.ArgumentParser(description="Run Codebase Copilot evaluation")
    parser.add_argument("--repo-id", required=True, help="Repository ID to evaluate")
    parser.add_argument("--dataset", required=True, help="Path to evaluation dataset JSON")
    parser.add_argument("--use-llm-judge", action="store_true", help="Use LLM for faithfulness evaluation")
    parser.add_argument("--output", help="Output path for results JSON")
    
    args = parser.parse_args()
    
    # Check repo exists
    repo = await get_repo(args.repo_id)
    if not repo:
        print(f"Error: Repository {args.repo_id} not found")
        return
    
    if repo["status"] != "ready":
        print(f"Error: Repository status is {repo['status']}, must be 'ready'")
        return
    
    # Run evaluation
    report = await run_evaluation(args.repo_id, args.dataset, args.use_llm_judge)
    
    # Print results
    print_report(report)
    
    # Save results
    output_path = args.output
    if not output_path:
        runs_dir = Path("eval/runs")
        runs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = runs_dir / f"eval_{timestamp}.json"
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())