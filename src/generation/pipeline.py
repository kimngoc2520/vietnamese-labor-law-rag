from dataclasses import dataclass
from typing import Any

from src.generation.citation import build_citations
from src.generation.llm import get_llm
from src.generation.prompt import SYSTEM_PROMPT, build_prompt
from src.retrieval.adaptive import AdaptiveRetriever
from src.db.connection import SessionLocal


@dataclass
class GenerationResult:
    answer: str
    citations: list[str]
    retrieved_chunks: list[dict[str, Any]]
    complexity: str
    retrieval_budget: int


class GenerationPipeline:
    """End-to-end adaptive retrieval + grounded generation pipeline."""

    def __init__(self) -> None:
        self.llm = get_llm()

    def run(self, query: str, final_top_k: int = 5) -> GenerationResult:
        db = SessionLocal()

        try:
            retriever = AdaptiveRetriever(db)
            retrieval = retriever.retrieve(
                query=query,
                final_top_k=final_top_k,
            )

            results = retrieval.results

            context = [
                chunk["content"]
                for chunk in results
                if chunk.get("content")
            ]

            prompt = build_prompt(
                query=query,
                context=context,
            )

            answer = self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                context="\n\n".join(context),
                query=query,
            )

            citations = build_citations(results)

            return GenerationResult(
                answer=answer,
                citations=citations,
                retrieved_chunks=results,
                complexity=retrieval.complexity.level,
                retrieval_budget=retrieval.budget.top_k,
            )

        finally:
            db.close()