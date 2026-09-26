from collections import defaultdict
from statistics import mean
from threading import Lock

_latency_records: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def record_latency(stage: str, milliseconds: float) -> None:
    """Record latency for an application stage."""
    if not stage:
        raise ValueError("Stage must not be empty.")

    if milliseconds < 0:
        raise ValueError("Latency must be non-negative.")

    with _lock:
        _latency_records[stage].append(float(milliseconds))


def get_latency_summary() -> dict[str, dict[str, float | int]]:
    """Return latency statistics grouped by stage."""
    with _lock:
        return {
            stage: {
                "count": len(values),
                "average_ms": mean(values),
                "min_ms": min(values),
                "max_ms": max(values),
            }
            for stage, values in _latency_records.items()
            if values
        }


def reset_latency() -> None:
    """Clear all recorded latency data."""
    with _lock:
        _latency_records.clear()