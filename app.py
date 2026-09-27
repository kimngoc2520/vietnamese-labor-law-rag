import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 180
REQUIRED_RESPONSE_FIELDS = (
    "query",
    "answer",
    "citations",
    "complexity",
    "retrieval_budget",
)

EXAMPLE_QUESTIONS = [
    "Người lao động đơn phương chấm dứt hợp đồng lao động phải báo trước bao nhiêu ngày?",
    "Thời gian thử việc tối đa đối với vị trí có trình độ chuyên môn kỹ thuật từ cao đẳng trở lên là bao lâu?",
    "Lao động nữ được nghỉ thai sản trước và sau khi sinh con tổng cộng bao lâu?",
]


class ChatClientError(Exception):
    """User-facing error when the chat API cannot be used."""


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def ask_chat(query: str, api_base_url: str | None = None) -> dict[str, Any]:
    """POST a question to the FastAPI /chat endpoint and return the JSON body."""
    cleaned_query = query.strip()

    if not cleaned_query:
        raise ChatClientError("Please enter a question before submitting.")

    base_url = (api_base_url or get_api_base_url()).rstrip("/")
    request = Request(
        url=f"{base_url}/chat",
        data=json.dumps({"query": cleaned_query}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise ChatClientError(_http_error_message(exc)) from exc
    except URLError:
        raise ChatClientError(
            "The FastAPI backend is unavailable. "
            "Check that the API is running and that the backend URL is correct."
        ) from None
    except TimeoutError:
        raise ChatClientError(
            "The backend did not respond in time. Please try again."
        ) from None

    return _parse_chat_response(raw_body)


def _http_error_message(exc: HTTPError) -> str:
    detail = exc.read().decode("utf-8", errors="replace").strip()

    if detail:
        try:
            payload = json.loads(detail)
        except json.JSONDecodeError:
            return f"The backend returned HTTP {exc.code}: {detail}"

        message = payload.get("detail", detail)
        if isinstance(message, list):
            return f"The backend returned HTTP {exc.code}: {json.dumps(message)}"
        return f"The backend returned HTTP {exc.code}: {message}"

    return f"The backend returned HTTP {exc.code}."


def _parse_chat_response(raw_body: str) -> dict[str, Any]:
    if not raw_body.strip():
        raise ChatClientError("The backend returned an empty response.")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ChatClientError(
            "The backend returned a response that is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ChatClientError("The backend returned an unexpected response format.")

    missing = [field for field in REQUIRED_RESPONSE_FIELDS if field not in payload]
    if missing:
        raise ChatClientError(
            "The backend response is missing required fields: "
            + ", ".join(missing)
        )

    citations = payload["citations"]
    if not isinstance(citations, list):
        raise ChatClientError("The backend returned citations in an unexpected format.")

    return payload


def main() -> None:
    import streamlit as st

    api_base_url = get_api_base_url()

    st.set_page_config(
        page_title="Vietnamese Labor Law AI Agent",
        layout="centered",
    )

    with st.sidebar:
        st.header("Project")
        st.write(
            "Vietnamese Labor Law RAG: an evaluation-driven assistant for "
            "questions about Vietnamese labor law."
        )
        st.caption(f"Backend URL: `{api_base_url}`")
        st.info(
            "Answers are generated from retrieved legal context. "
            "Always check them against the cited legal sources."
        )

    st.title("Vietnamese Labor Law AI Agent")
    st.write(
        "This is an AI/RAG assistant for Vietnamese labor-law questions. "
        "It sends your question to the FastAPI backend, which retrieves "
        "legal context and generates a grounded answer with citations."
    )

    st.subheader("Try an example")
    for index, example in enumerate(EXAMPLE_QUESTIONS):
        if st.button(example, key=f"example_{index}"):
            st.session_state["query_text"] = example

    query = st.text_area(
        "Your question",
        key="query_text",
        height=120,
        placeholder="Ask a question about Vietnamese labor law...",
    )

    if st.button("Ask", type="primary"):
        with st.spinner("Retrieving legal context and generating an answer..."):
            try:
                result = ask_chat(query, api_base_url=api_base_url)
            except ChatClientError as exc:
                st.error(str(exc))
            else:
                st.subheader("Answer")
                st.write(result["answer"])

                st.subheader("Metadata")
                st.write(f"**Complexity:** {result['complexity']}")
                st.write(f"**Retrieval budget:** {result['retrieval_budget']}")

                st.subheader("Sources")
                citations = [str(item).strip() for item in result["citations"] if str(item).strip()]
                if citations:
                    for citation in citations:
                        st.markdown(f"- {citation}")
                else:
                    st.info("No citations were returned for this answer.")


if __name__ == "__main__":
    main()
