from dataclasses import dataclass
from time import perf_counter
from typing import Any

from src.db.connection import SessionLocal
from src.generation.citation import build_citations
from src.generation.llm import get_llm
from src.generation.prompt import SYSTEM_PROMPT, build_prompt
from src.observability.latency import record_latency
from src.observability.metrics import record_metric
from src.retrieval.adaptive import AdaptiveRetriever
from src.verification.evidence import select_evidence


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
        total_start = perf_counter()
        record_metric(
            name="total_requests",
            value=1,
        )

        db = SessionLocal()

        try:
            retriever = AdaptiveRetriever(db)

            retrieval_start = perf_counter()
            retrieval = retriever.retrieve(
                query=query,
                final_top_k=final_top_k,
            )
            record_latency(
                stage="retrieval",
                milliseconds=(perf_counter() - retrieval_start) * 1000,
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

            generation_start = perf_counter()
            answer = self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                context="\n\n".join(context),
                query=query,
            )
            record_latency(
                stage="generation",
                milliseconds=(perf_counter() - generation_start) * 1000,
            )

            selected_evidence = select_evidence(
                answer=answer,
                evidence=results,
            )
            citations = build_citations(selected_evidence)

            result = GenerationResult(
                answer=answer,
                citations=citations,
                retrieved_chunks=results,
                complexity=retrieval.complexity.level,
                retrieval_budget=retrieval.budget.top_k,
            )

            record_metric(
                name="successful_requests",
                value=1,
            )

            return result

        except Exception:
            record_metric(
                name="failed_requests",
                value=1,
            )
            raise

        finally:
            record_latency(
                stage="total",
                milliseconds=(perf_counter() - total_start) * 1000,
            )
            db.close()