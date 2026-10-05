from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

BENCHMARKS = [
    "run_retrieval_benchmark.py",
    "run_hybrid_benchmark.py",
    "run_adaptive_benchmark.py",
    "run_quality_cost_benchmark.py",
]


def run_benchmark(script_name: str) -> None:
    """Run one evaluation benchmark script."""
    script_path = Path(__file__).parent / script_name

    print("\n" + "=" * 80)
    print(f"RUNNING: {script_name}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT_DIR,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Benchmark failed: {script_name} "
            f"(exit code {result.returncode})"
        )


def main() -> None:
    """Run the complete evaluation suite."""
    print("=" * 80)
    print("FULL EVALUATION")
    print("=" * 80)

    for benchmark in BENCHMARKS:
        run_benchmark(benchmark)

    print("\n" + "=" * 80)
    print("FULL EVALUATION COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()