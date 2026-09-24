import os


def _get_rate(env_name: str, default: float = 0.0) -> float:
    """Read a USD-per-million-token rate from environment variables."""
    try:
        return float(os.getenv(env_name, str(default)))
    except (TypeError, ValueError):
        return default


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate LLM cost in USD from token counts.

    Pricing is configured through environment variables:
    - LLM_INPUT_COST_PER_1M
    - LLM_OUTPUT_COST_PER_1M

    Rates default to 0.0 when pricing is not configured.
    """
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts must be non-negative.")

    input_rate = _get_rate("LLM_INPUT_COST_PER_1M")
    output_rate = _get_rate("LLM_OUTPUT_COST_PER_1M")

    return (
        (input_tokens / 1_000_000) * input_rate
        + (output_tokens / 1_000_000) * output_rate
    )