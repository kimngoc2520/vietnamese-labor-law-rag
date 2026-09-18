import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from src.db.connection import SessionLocal
from src.retrieval.adaptive import AdaptiveRetriever

TEST_QUERIES = [
    (
        "Simple",
        "Thời gian thử việc tối đa là bao lâu?",
    ),
    (
        "Medium",
        "Người lao động đơn phương chấm dứt hợp đồng lao động phải báo trước bao nhiêu ngày?",
    ),
    (
        "Complex",
        "Nếu người lao động đơn phương chấm dứt hợp đồng lao động khi người sử dụng lao động vi phạm nghĩa vụ thì có phải báo trước không và có được hưởng trợ cấp thôi việc hay không?",
    ),
]


def main():
    db = SessionLocal()

    try:
        retriever = AdaptiveRetriever(db)

        print("=" * 70)
        print("ADAPTIVE RETRIEVAL TEST")
        print("=" * 70)

        for expected_level, query in TEST_QUERIES:
            print("\n" + "-" * 70)
            print(f"Expected complexity: {expected_level}")
            print(f"Query: {query}")

            result = retriever.retrieve(query)

            print(f"Detected complexity: {result.complexity.level}")
            print(f"Complexity score: {result.complexity.score}")
            print(f"Retrieval budget: {result.budget.top_k}")
            print(f"Candidate count: {len(result.candidates)}")
            print(f"Final result count: {len(result.results)}")

            print("\nFinal results:")

            for rank, chunk in enumerate(
                result.results,
                start=1,
            ):
                print(
                    f"{rank}. "
                    f"{chunk['document_id']} | "
                    f"{chunk['article_title']} | "
                    f"rerank={chunk['rerank_score']:.4f}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()