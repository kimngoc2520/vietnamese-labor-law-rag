SYSTEM_PROMPT = """Bạn là trợ lý pháp luật lao động Việt Nam.

Quy tắc:
1. Chỉ trả lời dựa trên CONTEXT được cung cấp.
2. Không tự bổ sung thông tin pháp luật bên ngoài CONTEXT.
3. Nếu CONTEXT không đủ để trả lời, hãy nói rõ rằng thông tin được cung cấp chưa đủ.
4. Trả lời bằng tiếng Việt, ngắn gọn và chính xác.
5. Khi CONTEXT có thông tin về điều khoản pháp luật, hãy nêu rõ Điều tương ứng.
"""


def build_prompt(query: str, context: list[str]) -> str:
    """Build a grounded prompt from retrieved context."""

    context_text = "\n\n".join(context)

    return (
        f"CONTEXT:\n"
        f"{context_text}\n\n"
        f"QUESTION:\n"
        f"{query}"
    )