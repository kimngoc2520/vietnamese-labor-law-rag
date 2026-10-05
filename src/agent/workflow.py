from src.generation.pipeline import GenerationPipeline

from .state import AgentState


def run_workflow(query: str) -> AgentState:
    """Execute the Vietnamese labor-law RAG workflow."""
    query = query.strip()

    if not query:
        raise ValueError("Query must not be empty.")

    result = GenerationPipeline().run(query)

    return {
        "query": query,
        "route": "rag",
        "answer": result.answer,
        "citations": result.citations,
        "retrieved_chunks": result.retrieved_chunks,
        "complexity": result.complexity,
        "retrieval_budget": result.retrieval_budget,
        "error": None,
    }
