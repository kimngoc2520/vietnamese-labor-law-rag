from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from google import genai
from ragas import EvaluationDataset, evaluate
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    ContextPrecision,
    ContextRecall,
    Faithfulness,
    ResponseRelevancy,
)

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(os.getenv("RAG_PROJECT_ROOT", ROOT))
GENERATION_JSONL = PROJECT_ROOT / "evaluation/results/generation/generation_regression.jsonl"
GROUND_TRUTH_JSON = PROJECT_ROOT / "evaluation/datasets/ground_truth_evidence.json"
OUTPUT_DIR = PROJECT_ROOT / "evaluation/results/generation"
OUTPUT_JSON = OUTPUT_DIR / "ragas_evaluation.json"
OUTPUT_CSV = OUTPUT_DIR / "ragas_evaluation.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "ragas_evaluation_summary.json"


def load_latest_successes(path: Path) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    if not path.exists():
        raise FileNotFoundError(f"Generation regression file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"Skipping invalid JSONL line {line_no}: {exc}")
                continue

            query_id = record.get("query_id")
            if query_id and record.get("status") == "success":
                latest[query_id] = record

    return list(latest.values())


def load_ground_truth(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Ground-truth file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        records = data["records"]
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("Unsupported ground-truth JSON structure")

    result: dict[str, dict[str, Any]] = {}
    for record in records:
        query_id = record.get("query_id")
        if query_id:
            result[query_id] = record
    return result


def build_samples(
    successes: list[dict[str, Any]],
    ground_truth: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    for record in successes:
        query_id = record["query_id"]
        gt = ground_truth.get(query_id)
        if not gt:
            print(f"Skipping {query_id}: no ground-truth record")
            continue

        contexts = [
            chunk.get("content", "")
            for chunk in record.get("retrieved_chunks", [])
            if isinstance(chunk, dict) and chunk.get("content")
        ]
        answer = record.get("answer", "")
        query = record.get("query", "")
        evidence_note = gt.get("annotation", {}).get("evidence_note", "")

        if not query or not answer or not contexts:
            print(f"Skipping {query_id}: missing query/answer/context")
            continue

        sample = {
            "user_input": query,
            "response": answer,
            "retrieved_contexts": contexts,
            # This is an evidence-note proxy, not a full reference answer.
            "reference": evidence_note,
            "query_id": query_id,
            "complexity": record.get("complexity"),
            "retrieval_budget": record.get("retrieval_budget"),
        }
        samples.append(sample)

    return samples


def main() -> None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY before running RAGAS.")

    model_name = os.getenv("RAGAS_MODEL", "gemini-2.0-flash")

    successes = load_latest_successes(GENERATION_JSONL)
    ground_truth = load_ground_truth(GROUND_TRUTH_JSON)
    samples = build_samples(successes, ground_truth)

    if not samples:
        raise RuntimeError("No valid successful generation records are available for RAGAS.")

    print(f"Successful generation records: {len(successes)}")
    print(f"RAGAS evaluation samples: {len(samples)}")
    print(f"Evaluator model: {model_name}")

    client = genai.Client(api_key=api_key)
    evaluator_llm = llm_factory(model_name, provider="google", client=client)

    dataset = EvaluationDataset.from_list(samples)
    metrics = [
        Faithfulness(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm),
        ContextPrecision(llm=evaluator_llm),
        ContextRecall(llm=evaluator_llm),
    ]

    result = evaluate(dataset=dataset, metrics=metrics)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # RAGAS evaluation result can expose a pandas dataframe through to_pandas().
    result_df = result.to_pandas()
    result_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    result_dict = result.to_dict()
    OUTPUT_JSON.write_text(
        json.dumps(result_dict, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    numeric_columns = [
        column
        for column in [
            "faithfulness",
            "answer_relevancy",
            "response_relevancy",
            "context_precision",
            "context_recall",
        ]
        if column in result_df.columns
    ]

    summary: dict[str, Any] = {
        "evaluated_samples": len(result_df),
        "evaluator_model": model_name,
        "metrics": {},
        "note": (
            "Reference is the ground-truth evidence_note, used as a proxy rather than a full reference answer. "
            "ContextRecall/ContextPrecision should therefore be interpreted as evidence-alignment metrics."
        ),
    }

    for column in numeric_columns:
        values = pd.to_numeric(result_df[column], errors="coerce").dropna()
        summary["metrics"][column] = {
            "mean": float(values.mean()) if not values.empty else None,
            "count": int(values.count()),
        }

    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nRAGAS evaluation completed.")
    print(f"JSON:    {OUTPUT_JSON}")
    print(f"CSV:     {OUTPUT_CSV}")
    print(f"Summary: {OUTPUT_SUMMARY}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
