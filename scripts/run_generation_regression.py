import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.generation.pipeline import GenerationPipeline


QUERIES = {
    "Q1": "Người lao động có quyền đơn phương chấm dứt hợp đồng lao động trong những trường hợp nào?",
    "Q2": "Thời gian thử việc tối đa đối với vị trí có trình độ chuyên môn kỹ thuật từ cao đẳng trở lên là bao lâu?",
}


def run_query(pipeline: GenerationPipeline, query_id: str, query: str) -> None:
    print("\n" + "=" * 80)
    print(f"{query_id}: {query}")
    print("=" * 80)

    result = pipeline.run(query=query, final_top_k=5)

    print("\n[RETRIEVAL]")
    print(f"Complexity       : {result.complexity}")
    print(f"Retrieval budget : {result.retrieval_budget}")
    print(f"Retrieved chunks : {len(result.retrieved_chunks)}")

    print("\n[TOP RESULTS]")
    for i, chunk in enumerate(result.retrieved_chunks, start=1):
        print(
            f"{i}. "
            f"{chunk.get('document_id', 'N/A')} | "
            f"{chunk.get('article_title', 'N/A')} | "
            f"rerank_score={chunk.get('rerank_score', 'N/A')}"
        )

    print("\n[ANSWER]")
    print(result.answer)

    print("\n[CITATIONS]")
    if result.citations:
        for citation in result.citations:
            print(f"- {citation}")
    else:
        print("- No citations")


def main() -> None:
    pipeline = GenerationPipeline()

    for query_id, query in QUERIES.items():
        try:
            run_query(pipeline, query_id, query)
        except Exception as exc:
            print("\n" + "!" * 80)
            print(f"{query_id} FAILED")
            print(f"{type(exc).__name__}: {exc}")
            print("!" * 80)


if __name__ == "__main__":
    main()