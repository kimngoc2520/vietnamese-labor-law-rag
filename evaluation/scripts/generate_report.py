import json
from pathlib import Path
from typing import Any

# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

RESULTS_DIR = ROOT_DIR / "evaluation" / "results"
REPORT_DIR = ROOT_DIR / "evaluation" / "reports"

RETRIEVAL_RESULT_PATH = (
    RESULTS_DIR / "retrieval" / "retrieval_benchmark.json"
)

HYBRID_RESULT_PATH = (
    RESULTS_DIR / "retrieval" / "hybrid_benchmark.json"
)

ADAPTIVE_RESULT_PATH = (
    RESULTS_DIR / "adaptive" / "adaptive_benchmark.json"
)

GENERATION_RESULT_PATH = (
    RESULTS_DIR / "generation" / "generation_regression_summary.json"
)

GENERATION_JSONL_PATH = (
    RESULTS_DIR / "generation" / "generation_regression.jsonl"
)

RAGAS_SUMMARY_PATH = (
    RESULTS_DIR / "generation" / "ragas_evaluation_summary.json"
)

QUALITY_COST_RESULT_PATH = (
    RESULTS_DIR / "adaptive" / "quality_cost_benchmark.json"
)

REPORT_PATH = REPORT_DIR / "evaluation_report.md"

GENERATION_REPORT_PATH = (
    REPORT_DIR / "generation_evaluation_report.md"
)


# ============================================================
# HELPERS
# ============================================================


def load_json(path: Path) -> dict[str, Any] | None:
    """Load a JSON result file if it exists."""

    if not path.exists():
        print(f"[WARN] Result file not found: {path}")
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_metric(value: float | None) -> str:
    """Format a metric value for Markdown."""

    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)


def format_percent(value: float | None) -> str:
    """Format a ratio as a percentage."""

    if value is None:
        return "N/A"

    return f"{float(value) * 100:.2f}%"


def metrics_equal(
    left: dict[str, Any],
    right: dict[str, Any],
    keys: tuple[str, ...] = (
        "Hit@1",
        "Hit@3",
        "Hit@5",
        "MRR",
    ),
    tolerance: float = 1e-9,
) -> bool:
    """Compare retrieval metrics within a numeric tolerance."""

    for key in keys:
        left_value = left.get(key)
        right_value = right.get(key)

        if left_value is None or right_value is None:
            return False

        if abs(float(left_value) - float(right_value)) > tolerance:
            return False

    return True


def load_latest_records_by_query_id(
    path: Path,
) -> dict[str, dict[str, Any]]:
    """Return the last JSONL record per query_id.

    The JSONL file is append-only across runs and is not the
    benchmark size. This helper is only used for latest error detail.
    """

    latest: dict[str, dict[str, Any]] = {}

    if not path.exists():
        return latest

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            query_id = record.get("query_id")

            if query_id:
                latest[query_id] = record

    return latest


# ============================================================
# RETRIEVAL SECTION
# ============================================================


def build_retrieval_section(
    result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "## 1. Retrieval Baseline",
        "",
    ]

    if result is None:
        lines.extend(
            [
                "Retrieval benchmark results are not available.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            f"Evaluation queries: {result.get('query_count', 'N/A')}",
            "",
            "| Method | Hit@1 | Hit@3 | Hit@5 | MRR |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    methods = [
        ("Dense", "dense"),
        ("Dense + Reranker", "dense_reranker"),
    ]

    for label, key in methods:
        metrics = result.get(key, {})

        lines.append(
            "| "
            f"{label} | "
            f"{format_metric(metrics.get('Hit@1'))} | "
            f"{format_metric(metrics.get('Hit@3'))} | "
            f"{format_metric(metrics.get('Hit@5'))} | "
            f"{format_metric(metrics.get('MRR'))} |"
        )

    lines.append("")

    return lines


# ============================================================
# HYBRID SECTION
# ============================================================


def build_hybrid_section(
    result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "## 2. Hybrid Retrieval Ablation",
        "",
    ]

    if result is None:
        lines.extend(
            [
                "Hybrid benchmark results are not available.",
                "",
            ]
        )
        return lines

    pipelines = result.get("pipelines", {})

    lines.extend(
        [
            f"Evaluation queries: {result.get('query_count', 'N/A')}",
            "",
            "| Method | Hit@1 | Hit@3 | Hit@5 | MRR |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    methods = [
        ("Dense", "Dense"),
        ("Dense + Reranker", "Dense+Rerank"),
        ("Hybrid", "Hybrid"),
        ("Hybrid + Reranker", "Hybrid+Rerank"),
    ]

    for label, key in methods:
        metrics = pipelines.get(key, {})

        lines.append(
            "| "
            f"{label} | "
            f"{format_metric(metrics.get('Hit@1'))} | "
            f"{format_metric(metrics.get('Hit@3'))} | "
            f"{format_metric(metrics.get('Hit@5'))} | "
            f"{format_metric(metrics.get('MRR'))} |"
        )

    lines.append("")

    return lines


# ============================================================
# ADAPTIVE SECTION
# ============================================================


def build_adaptive_section(
    result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "## 3. Adaptive Retrieval",
        "",
    ]

    if result is None:
        lines.extend(
            [
                "Adaptive benchmark results are not available.",
                "",
            ]
        )
        return lines

    fixed_k = result.get("fixed_k", {})
    adaptive_k = result.get("adaptive_k", {})

    adaptive_metrics = adaptive_k.get("metrics", {})

    lines.extend(
        [
            f"Evaluation queries: {result.get('query_count', 'N/A')}",
            "",
            "### 3.1 Quality",
            "",
            "| Method | Hit@1 | Hit@3 | Hit@5 | MRR |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    for k in ["5", "10", "20"]:
        metrics = fixed_k.get(k, {})

        lines.append(
            "| "
            f"Fixed-K={k} | "
            f"{format_metric(metrics.get('Hit@1'))} | "
            f"{format_metric(metrics.get('Hit@3'))} | "
            f"{format_metric(metrics.get('Hit@5'))} | "
            f"{format_metric(metrics.get('MRR'))} |"
        )

    lines.append(
        "| "
        "Adaptive-K | "
        f"{format_metric(adaptive_metrics.get('Hit@1'))} | "
        f"{format_metric(adaptive_metrics.get('Hit@3'))} | "
        f"{format_metric(adaptive_metrics.get('Hit@5'))} | "
        f"{format_metric(adaptive_metrics.get('MRR'))} |"
    )

    lines.extend(
        [
            "",
            "### 3.2 Budget Statistics",
            "",
        ]
    )

    average_k = adaptive_k.get("average_selected_k")

    complexity_counts = adaptive_k.get(
        "complexity_counts",
        {},
    )

    k_distribution = adaptive_k.get(
        "k_distribution",
        {},
    )

    lines.extend(
        [
            f"- Average selected K: {format_metric(average_k)}",
            "",
            "Complexity distribution:",
            "",
            "| Complexity | Queries |",
            "|---|---:|",
        ]
    )

    for complexity in [
        "Simple",
        "Medium",
        "Complex",
    ]:
        lines.append(
            "| "
            f"{complexity} | "
            f"{complexity_counts.get(complexity, 0)} |"
        )

    lines.extend(
        [
            "",
            "Selected K distribution:",
            "",
            "| K | Queries |",
            "|---:|---:|",
        ]
    )

    for k in ["5", "10", "20"]:
        lines.append(
            "| "
            f"{k} | "
            f"{k_distribution.get(k, 0)} |"
        )

    lines.extend(
        [
            "",
            "### 3.3 Interpretation",
            "",
        ]
    )

    fixed_metric_groups = [
        fixed_k.get(k, {})
        for k in ["5", "10", "20"]
        if fixed_k.get(k)
    ]

    same_as_all_fixed = bool(fixed_metric_groups) and all(
        metrics_equal(adaptive_metrics, group)
        for group in fixed_metric_groups
    )

    if same_as_all_fixed:
        lines.extend(
            [
                (
                    "Adaptive-K achieved the same retrieval quality as "
                    "the fixed-K baselines on this evaluation set. "
                    "These results alone do not establish a quality "
                    "advantage. Efficiency should be interpreted through "
                    "matched-budget quality-cost comparisons."
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                (
                    "Adaptive-K is evaluated against Fixed-K baselines "
                    "using the same retrieval quality metrics. These "
                    "results should not be read as a quality ranking "
                    "unless a quality difference is shown under "
                    "matched candidate budgets."
                ),
                "",
            ]
        )

    return lines


# ============================================================
# QUALITY-COST SECTION
# ============================================================


def build_quality_cost_section(
    result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "### 3.4 Quality-cost (retrieval candidate budget)",
        "",
    ]

    if result is None:
        lines.extend(
            [
                (
                    "Quality-cost benchmark results are not "
                    "available. Run "
                    "`evaluation/scripts/run_quality_cost_benchmark.py` "
                    "to produce "
                    "`evaluation/results/adaptive/"
                    "quality_cost_benchmark.json`."
                ),
                "",
                (
                    "This comparison counts fused hybrid candidates "
                    "passed to the cross-encoder "
                    "(`reranker_scoring_count`). "
                    "That is not LLM token cost, and it is not the "
                    "final returned top_k after reranking."
                ),
                "",
            ]
        )
        return lines

    query_count = result.get("query_count", "N/A")
    final_top_k = result.get("final_returned_top_k", "N/A")
    fixed_k = result.get("fixed_k", {})
    adaptive = result.get("adaptive", {})
    adaptive_metrics = adaptive.get("metrics", {})
    reductions = result.get(
        "reranker_scoring_count_reduction_vs_fixed_k",
        {},
    )

    lines.extend(
        [
            f"Evaluation queries: {query_count}",
            "",
            f"Final returned top_k after reranking: {final_top_k}",
            "",
            (
                "Terminology: `retrieval_candidate_budget` is the "
                "requested dense/BM25/hybrid top_k. "
                "`reranker_scoring_count` is the number of fused "
                "hybrid candidates passed to "
                "`CrossEncoder.predict` (all of those candidates "
                "are scored). The reranker then returns only "
                "`final_returned_top_k` documents."
            ),
            "",
            (
                "| Method | Hit@1 | Hit@3 | Hit@5 | MRR | "
                "Avg retrieval budget | Total reranker scoring count |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for k in ["5", "10", "20"]:
        entry = fixed_k.get(k) or fixed_k.get(int(k), {})
        metrics = entry.get("metrics", {})

        lines.append(
            "| "
            f"Fixed-K={k} | "
            f"{format_metric(metrics.get('Hit@1'))} | "
            f"{format_metric(metrics.get('Hit@3'))} | "
            f"{format_metric(metrics.get('Hit@5'))} | "
            f"{format_metric(metrics.get('MRR'))} | "
            f"{format_metric(entry.get('average_retrieval_candidate_budget'))} | "
            f"{format_metric(entry.get('total_reranker_scoring_count'))} |"
        )

    lines.append(
        "| "
        "Adaptive-K | "
        f"{format_metric(adaptive_metrics.get('Hit@1'))} | "
        f"{format_metric(adaptive_metrics.get('Hit@3'))} | "
        f"{format_metric(adaptive_metrics.get('Hit@5'))} | "
        f"{format_metric(adaptive_metrics.get('MRR'))} | "
        f"{format_metric(adaptive.get('average_retrieval_candidate_budget'))} | "
        f"{format_metric(adaptive.get('total_reranker_scoring_count'))} |"
    )

    lines.extend(
        [
            "",
            "Reranker scoring-count reduction vs Fixed-K:",
            "",
        ]
    )

    if reductions:
        for k in ["5", "10", "20"]:
            item = reductions.get(k) or reductions.get(int(k), {})
            percent = item.get("percent")

            if percent is None:
                lines.append(f"- vs Fixed-K={k}: N/A")
                continue

            percent_value = float(percent)

            if percent_value >= 0:
                lines.append(
                    f"- vs Fixed-K={k}: {percent_value:.2f}% fewer "
                    "candidates scored by the reranker"
                )
            else:
                lines.append(
                    f"- vs Fixed-K={k}: {abs(percent_value):.2f}% more "
                    "candidates scored by the reranker"
                )
    else:
        lines.append("N/A")

    lines.extend(
        [
            "",
            (
                "A lower scoring count is a retrieval/reranking "
                "workload comparison, not evidence that Adaptive-K "
                "has higher answer quality."
            ),
            "",
        ]
    )

    return lines


# ============================================================
# GENERATION SECTION
# ============================================================


def latest_generation_errors() -> list[dict[str, Any]]:
    latest = load_latest_records_by_query_id(
        GENERATION_JSONL_PATH
    )

    errors = [
        record
        for record in latest.values()
        if record.get("status") == "error"
    ]

    errors.sort(key=lambda item: str(item.get("query_id", "")))
    return errors


def build_generation_section(
    result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "## 4. Generation Regression",
        "",
    ]

    if result is None:
        lines.extend(
            [
                "Generation regression results are not available.",
                "",
            ]
        )
        return lines

    dataset_size = result.get("dataset_size")
    successful = result.get("successful")
    errors = result.get("errors")
    success_rate = result.get("success_rate")
    complexity = result.get("complexity_distribution", {})
    error_distribution = result.get("error_distribution", {})
    retry_config = result.get("retry_config", {})

    lines.extend(
        [
            (
                "Authoritative source: "
                "`evaluation/results/generation/"
                "generation_regression_summary.json`."
            ),
            "",
            (
                "`generation_regression.jsonl` is append-only "
                "across runs. Line count in that file is not the "
                "benchmark size."
            ),
            "",
            f"- Evaluation queries: {dataset_size}",
            f"- Successful generations: {successful}",
            f"- Failed generations: {errors}",
            (
                f"- Execution success rate: "
                f"{format_percent(success_rate)} "
                f"({format_metric(success_rate)})"
            ),
            (
                f"- Average retrieval budget "
                f"(successful queries): "
                f"{format_metric(result.get('average_retrieval_budget'))}"
            ),
            (
                f"- Average citations "
                f"(successful queries): "
                f"{format_metric(result.get('average_citations'))}"
            ),
            f"- Generated at: {result.get('generated_at', 'N/A')}",
            "",
            "Complexity distribution (successful queries):",
            "",
            "| Complexity | Queries |",
            "|---|---:|",
        ]
    )

    for level in ["Simple", "Medium", "Complex"]:
        lines.append(
            f"| {level} | {complexity.get(level, 0)} |"
        )

    lines.extend(
        [
            "",
            "Error distribution (current summary, one record per query):",
            "",
        ]
    )

    if error_distribution:
        lines.extend(
            [
                "| Error type | Count |",
                "|---|---:|",
            ]
        )

        for error_type in sorted(error_distribution):
            lines.append(
                f"| {error_type} | "
                f"{error_distribution[error_type]} |"
            )
    else:
        lines.append("None.")

    latest_errors = latest_generation_errors()

    if latest_errors:
        lines.extend(
            [
                "",
                "Latest failed queries (last JSONL record per query_id):",
                "",
            ]
        )

        for record in latest_errors:
            query_id = record.get("query_id", "unknown")
            error_type = record.get("error_type", "Unknown")
            error_text = str(record.get("error", "")).replace(
                "\n",
                " ",
            )

            if len(error_text) > 180:
                error_text = error_text[:177] + "..."

            lines.append(
                f"- `{query_id}` ({error_type}): {error_text}"
            )

    if retry_config:
        lines.extend(
            [
                "",
                "Retry configuration:",
                "",
                (
                    f"- max_503_retries: "
                    f"{retry_config.get('max_503_retries', 'N/A')}"
                ),
                (
                    f"- initial_retry_seconds: "
                    f"{retry_config.get('initial_retry_seconds', 'N/A')}"
                ),
                (
                    f"- stop_on_quota_429: "
                    f"{retry_config.get('stop_on_quota_429', 'N/A')}"
                ),
            ]
        )

    lines.extend(
        [
            "",
            (
                "This is an execution-success regression, not a "
                "measure of legal answer correctness."
            ),
            "",
        ]
    )

    return lines


def build_generation_detail_report(
    result: dict[str, Any] | None,
    ragas_summary: dict[str, Any] | None,
) -> list[str]:
    dataset_size = (
        result.get("dataset_size")
        if result
        else "N/A"
    )

    lines = [
        "# Generation Evaluation Report",
        "",
        "## 1. Overview",
        "",
        (
            "This report covers generation regression on the "
            f"{dataset_size}-query golden dataset. RAGAS, when present, "
            "is an evidence-alignment proxy evaluation, not a "
            "full gold-answer evaluation."
        ),
        "",
        "## 2. Dataset",
        "",
        "Golden dataset: `evaluation/datasets/ground_truth_evidence.json`.",
        "",
        (
            "Current counts come from "
            "`generation_regression_summary.json`, not from the "
            "number of historical JSONL lines."
        ),
        "",
    ]

    lines.extend(
        [
            "## 3. Generation regression",
            "",
        ]
    )

    lines.extend(build_generation_section(result)[2:])

    lines.extend(
        [
            "## RAGAS",
            "",
        ]
    )

    if ragas_summary is None:
        lines.extend(
            [
                "RAGAS summary file is not available.",
                "",
                (
                    "When RAGAS is run, the `reference` field is the "
                    "ground-truth `evidence_note`. That is an "
                    "evidence-alignment proxy, not a full gold "
                    "answer. ContextPrecision and ContextRecall "
                    "should be read as evidence-alignment metrics."
                ),
                "",
            ]
        )
        return lines

    metrics = ragas_summary.get("metrics", {})

    lines.extend(
        [
            (
                f"- Evaluated samples: "
                f"{ragas_summary.get('evaluated_samples', 'N/A')}"
            ),
            (
                f"- Evaluator model: "
                f"{ragas_summary.get('evaluator_model', 'N/A')}"
            ),
            "",
            (
                ragas_summary.get(
                    "note",
                    "Reference is an evidence-alignment proxy "
                    "(evidence_note), not a full gold answer.",
                )
            ),
            "",
            "| Metric | Mean | Count |",
            "|---|---:|---:|",
        ]
    )

    for name in sorted(metrics):
        item = metrics[name]

        lines.append(
            "| "
            f"{name} | "
            f"{format_metric(item.get('mean'))} | "
            f"{item.get('count', 'N/A')} |"
        )

    lines.append("")

    return lines


# ============================================================
# LIMITATIONS
# ============================================================


def build_limitations_section() -> list[str]:
    return [
        "## 5. Limitations",
        "",
        (
            "- The evaluation dataset contains 30 annotated "
            "queries and should not be treated as a "
            "comprehensive representation of all Vietnamese "
            "labor-law queries."
        ),
        (
            "- Ground-truth evidence is based on exact "
            "`document_id` + `chunk_index` matching."
        ),
        (
            "- Retrieval metrics measure whether the annotated "
            "evidence is retrieved and do not by themselves "
            "establish answer correctness."
        ),
        (
            "- Adaptive-K should be compared using matched "
            "quality-cost budgets before making claims about "
            "efficiency advantages. Equal Hit@K/MRR versus "
            "Fixed-K does not mean Adaptive-K is better."
        ),
        (
            "- Generation regression measures whether the pipeline "
            "returned an answer. It is not legal correctness. "
            "The JSONL file may contain historical retries; "
            "the summary JSON is the current scoreboard."
        ),
        (
            "- RAGAS, if present, uses `evidence_note` as an "
            "evidence-alignment proxy rather than a full "
            "reference answer."
        ),
        "",
    ]


# ============================================================
# REPORT GENERATION
# ============================================================


def generate_report() -> None:
    print("=" * 70)
    print("GENERATING EVALUATION REPORT")
    print("=" * 70)

    retrieval_result = load_json(RETRIEVAL_RESULT_PATH)
    hybrid_result = load_json(HYBRID_RESULT_PATH)
    adaptive_result = load_json(ADAPTIVE_RESULT_PATH)
    generation_result = load_json(GENERATION_RESULT_PATH)
    quality_cost_result = load_json(QUALITY_COST_RESULT_PATH)
    ragas_summary = load_json(RAGAS_SUMMARY_PATH)

    report_lines: list[str] = [
        "# Evaluation Report",
        "",
        "Automatically generated from benchmark result files.",
        "",
        "## Evaluation Overview",
        "",
        (
            "This report summarizes retrieval, hybrid "
            "retrieval, adaptive retrieval, and generation "
            "regression results produced by the evaluation "
            "pipeline."
        ),
        "",
    ]

    report_lines.extend(
        build_retrieval_section(retrieval_result)
    )

    report_lines.extend(
        build_hybrid_section(hybrid_result)
    )

    report_lines.extend(
        build_adaptive_section(adaptive_result)
    )

    report_lines.extend(
        build_quality_cost_section(quality_cost_result)
    )

    report_lines.extend(
        build_generation_section(generation_result)
    )

    report_lines.extend(
        build_limitations_section()
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(report_lines))

    generation_report = build_generation_detail_report(
        generation_result,
        ragas_summary,
    )

    with GENERATION_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(generation_report))

    print(f"\nReport saved to: {REPORT_PATH}")
    print(
        "Generation report saved to: "
        f"{GENERATION_REPORT_PATH}"
    )


# ============================================================
# ENTRY POINT
# ============================================================


if __name__ == "__main__":
    generate_report()