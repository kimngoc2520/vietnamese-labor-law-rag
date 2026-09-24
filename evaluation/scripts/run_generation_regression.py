from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.generation.pipeline import GenerationPipeline

from src.generation.pipeline import GenerationPipeline


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "evaluation" / "datasets" / "ground_truth_evidence.json"
RESULTS_DIR = ROOT / "evaluation" / "results" / "generation"
JSONL_PATH = RESULTS_DIR / "generation_regression.jsonl"
SUMMARY_PATH = RESULTS_DIR / "generation_regression_summary.json"

# Retry only transient Gemini service failures.
MAX_503_RETRIES = 3
INITIAL_RETRY_SECONDS = 5

# Do not repeatedly retry a Free Tier quota error.
STOP_ON_QUOTA_429 = True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {DATASET_PATH}")

    return data


def load_existing_results() -> dict[str, dict[str, Any]]:
    if not JSONL_PATH.exists():
        return {}

    results: dict[str, dict[str, Any]] = {}

    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"[WARN] Skipping invalid JSONL line {line_number}")
                continue

            query_id = record.get("query_id")

            if query_id:
                results[query_id] = record

    return results


def append_result(record: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def error_text(exc: Exception) -> str:
    return str(exc)


def is_503_error(exc: Exception) -> bool:
    text = error_text(exc).lower()

    return "503" in text and (
        "unavailable" in text
        or "high demand" in text
        or "service unavailable" in text
    )


def is_429_quota_error(exc: Exception) -> bool:
    text = error_text(exc).lower()

    return "429" in text and (
        "resource_exhausted" in text
        or "quota" in text
        or "rate limit" in text
    )


def run_with_retry(
    pipeline: GenerationPipeline,
    query: str,
) -> tuple[Any | None, Exception | None, int]:
    """
    Run generation with retry handling.

    503:
        Retry up to MAX_503_RETRIES using exponential backoff.

    429:
        Return immediately so the caller can stop the regression run.
    """

    retry_count = 0

    while True:
        try:
            result = pipeline.run(query=query)

            return result, None, retry_count

        except Exception as exc:

            # Quota exceeded -> do not retry immediately.
            if is_429_quota_error(exc):
                return None, exc, retry_count

            # Non-503 error -> return immediately.
            if not is_503_error(exc):
                return None, exc, retry_count

            # 503 but retry limit reached.
            if retry_count >= MAX_503_RETRIES:
                return None, exc, retry_count

            retry_count += 1

            wait_seconds = INITIAL_RETRY_SECONDS * (
                2 ** (retry_count - 1)
            )

            print(
                f"[RETRY] Gemini returned 503 for query "
                f"'{query[:60]}...'. "
                f"Retry {retry_count}/{MAX_503_RETRIES} "
                f"in {wait_seconds}s."
            )

            time.sleep(wait_seconds)


def summarize(
    dataset_size: int,
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:

    success_records = [
        record
        for record in records.values()
        if record.get("status") == "success"
    ]

    error_records = [
        record
        for record in records.values()
        if record.get("status") == "error"
    ]

    complexity_distribution: dict[str, int] = {}

    budgets: list[int] = []
    citation_counts: list[int] = []

    for record in success_records:

        complexity = record.get("complexity")

        if complexity:
            complexity_distribution[complexity] = (
                complexity_distribution.get(complexity, 0) + 1
            )

        budget = record.get("retrieval_budget")

        if isinstance(budget, (int, float)):
            budgets.append(int(budget))

        citations = record.get("citations")

        if isinstance(citations, list):
            citation_counts.append(len(citations))

    error_distribution: dict[str, int] = {}

    for record in error_records:

        error_type = record.get(
            "error_type",
            "Unknown",
        )

        error_distribution[error_type] = (
            error_distribution.get(error_type, 0) + 1
        )

    return {
        "generated_at": utc_now(),
        "dataset_size": dataset_size,
        "successful": len(success_records),
        "errors": len(error_records),
        "success_rate": (
            len(success_records) / dataset_size
            if dataset_size
            else 0.0
        ),
        "complexity_distribution": complexity_distribution,
        "average_retrieval_budget": (
            sum(budgets) / len(budgets)
            if budgets
            else None
        ),
        "average_citations": (
            sum(citation_counts) / len(citation_counts)
            if citation_counts
            else None
        ),
        "error_distribution": error_distribution,
        "retry_config": {
            "max_503_retries": MAX_503_RETRIES,
            "initial_retry_seconds": INITIAL_RETRY_SECONDS,
            "stop_on_quota_429": STOP_ON_QUOTA_429,
        },
    }


def main() -> None:

    dataset = load_dataset()

    existing = load_existing_results()

    print("=" * 60)
    print("Generation Regression")
    print("=" * 60)

    print(f"Dataset size: {len(dataset)}")
    print(f"Existing records: {len(existing)}")
    print()

    pipeline = GenerationPipeline()

    for index, item in enumerate(dataset, start=1):

        query_id = item["query_id"]
        query = item["query"]

        previous = existing.get(query_id)

        # Successful queries are already complete.
        if previous and previous.get("status") == "success":

            print(
                f"[{index}/{len(dataset)}] "
                f"{query_id} -> already successful, skip"
            )

            continue

        print(
            f"[{index}/{len(dataset)}] "
            f"{query_id}"
        )

        print(f"Query: {query}")

        started_at = utc_now()

        result, exc, retry_count = run_with_retry(
            pipeline,
            query,
        )

        # -------------------------
        # SUCCESS
        # -------------------------

        if result is not None:

            record = {
                "query_id": query_id,
                "query": query,
                "status": "success",
                "started_at": started_at,
                "finished_at": utc_now(),
                "retry_count": retry_count,
                "complexity": result.complexity,
                "retrieval_budget": result.retrieval_budget,
                "answer": result.answer,
                "citations": result.citations,
                "retrieved_chunks": result.retrieved_chunks,
            }

            append_result(record)

            existing[query_id] = record

            print(
                f"  -> success | "
                f"complexity={result.complexity} | "
                f"budget={result.retrieval_budget} | "
                f"citations={len(result.citations)}"
            )

            print()

            continue

        # -------------------------
        # ERROR
        # -------------------------

        assert exc is not None

        if is_429_quota_error(exc):

            error_type = "QuotaExceeded"

        elif is_503_error(exc):

            error_type = "ServerUnavailable"

        else:

            error_type = type(exc).__name__

        record = {
            "query_id": query_id,
            "query": query,
            "status": "error",
            "started_at": started_at,
            "finished_at": utc_now(),
            "retry_count": retry_count,
            "error_type": error_type,
            "error": error_text(exc),
        }

        append_result(record)

        existing[query_id] = record

        print(f"  -> {error_type}")
        print(f"  -> {error_text(exc)}")
        print()

        # Stop when Gemini Free Tier quota is exhausted.
        if (
            STOP_ON_QUOTA_429
            and error_type == "QuotaExceeded"
        ):

            print(
                "[STOP] Gemini Free Tier quota "
                "has been exhausted."
            )

            print(
                "       Stop now instead of sending "
                "the remaining queries."
            )

            break

    # -------------------------
    # SAVE SUMMARY
    # -------------------------

    summary = summarize(
        len(dataset),
        existing,
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("=" * 60)
    print("=== Generation Regression Summary ===")

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()

    print(f"Saved: {JSONL_PATH}")
    print(f"Saved: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()