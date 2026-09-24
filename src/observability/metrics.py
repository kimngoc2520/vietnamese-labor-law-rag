from collections import defaultdict
from statistics import mean
from threading import Lock


_metric_records: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def record_metric(name: str, value: float) -> None:
    """Record a numeric application metric."""
    if not name:
        raise ValueError("Metric name must not be empty.")

    with _lock:
        _metric_records[name].append(float(value))


def get_metric_summary() -> dict[str, dict[str, float | int]]:
    """Return metric statistics grouped by metric name."""
    with _lock:
        return {
            name: {
                "count": len(values),
                "average": mean(values),
                "min": min(values),
                "max": max(values),
            }
            for name, values in _metric_records.items()
            if values
        }


def reset_metrics() -> None:
    """Clear all recorded metrics."""
    with _lock:
        _metric_records.clear()