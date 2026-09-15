def build_prompt(query: str, context: list[str]) -> str:
    return f"Question: {query}\nContext:\n" + "\n".join(context)
