import time
from collections.abc import Iterator
from contextlib import contextmanager

from src.common.logging import get_logger
from src.observability.latency import record_latency

logger = get_logger(__name__)


@contextmanager
def trace(name: str) -> Iterator[None]:
    """Trace the execution time of an application stage."""
    if not name:
        raise ValueError("Trace name must not be empty.")

    start = time.perf_counter()

    try:
        yield
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_latency(name, elapsed_ms)
        logger.exception(
            "Stage failed | stage=%s | latency_ms=%.2f",
            name,
            elapsed_ms,
        )
        raise
    else:
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_latency(name, elapsed_ms)
        logger.info(
            "Stage completed | stage=%s | latency_ms=%.2f",
            name,
            elapsed_ms,
        )