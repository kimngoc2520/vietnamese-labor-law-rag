import html
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 180

REQUIRED_RESPONSE_FIELDS = {
    "query",
    "answer",
    "citations",
    "complexity",
    "retrieval_budget",
}

EXAMPLE_QUESTIONS = [
    "Người lao động đơn phương chấm dứt hợp đồng lao động phải báo trước bao nhiêu ngày?",
    "Thời gian thử việc tối đa đối với vị trí có trình độ chuyên môn kỹ thuật từ cao đẳng trở lên là bao lâu?",
    "Lao động nữ được nghỉ thai sản trước và sau khi sinh con tổng cộng bao lâu?",
]


# =========================================================
# API CLIENT
# =========================================================


class ChatClientError(Exception):
    """User-facing error when the chat API cannot be used."""


def get_api_base_url() -> str:
    """Return the configured FastAPI base URL."""
    return os.getenv(
        "API_BASE_URL",
        DEFAULT_API_BASE_URL,
    ).rstrip("/")


def ask_chat(
    query: str,
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Send a question to the FastAPI /chat endpoint."""
    cleaned_query = query.strip()

    if not cleaned_query:
        raise ChatClientError(
            "Please enter a question before sending."
        )

    base_url = (
        api_base_url or get_api_base_url()
    ).rstrip("/")

    request = Request(
        url=f"{base_url}/chat",
        data=json.dumps(
            {"query": cleaned_query},
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            raw_body = response.read().decode("utf-8")

    except HTTPError as exc:
        raise ChatClientError(
            _http_error_message(exc)
        ) from exc

    except URLError:
        raise ChatClientError(
            "Backend unavailable. "
            "Please check that the FastAPI backend is running "
            "and API_BASE_URL is correct."
        ) from None

    except TimeoutError:
        raise ChatClientError(
            "Backend không phản hồi trong thời gian cho phép. "
            "Vui lòng thử lại."
        ) from None

    return _parse_chat_response(raw_body)


def _http_error_message(exc: HTTPError) -> str:
    """Convert an HTTP error response into a readable message."""
    detail = exc.read().decode(
        "utf-8",
        errors="replace",
    ).strip()

    if not detail:
        return f"Backend trả về HTTP {exc.code}."

    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return f"Backend trả về HTTP {exc.code}: {detail}"

    message = payload.get(
        "detail",
        detail,
    )

    if isinstance(message, list):
        message = json.dumps(
            message,
            ensure_ascii=False,
        )

    return (
        f"Backend trả về HTTP {exc.code}: "
        f"{message}"
    )


def _parse_chat_response(
    raw_body: str,
) -> dict[str, Any]:
    """Validate the response returned by FastAPI."""
    if not raw_body.strip():
        raise ChatClientError(
            "Backend trả về response rỗng."
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ChatClientError(
            "Backend response is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ChatClientError(
            "Backend trả về response không đúng định dạng."
        )

    missing = [
        field
        for field in REQUIRED_RESPONSE_FIELDS
        if field not in payload
    ]

    if missing:
        raise ChatClientError(
            "Backend response is missing required fields: "
            + ", ".join(missing)
        )

    payload.setdefault("retrieved_chunks", [])

    if not isinstance(
        payload["citations"],
        list,
    ):
        raise ChatClientError(
            "Backend trả về citations không đúng định dạng."
        )

    if not isinstance(
        payload["retrieved_chunks"],
        list,
    ):
        raise ChatClientError(
            "Backend trả về retrieved_chunks không đúng định dạng."
        )

    return payload


# =========================================================
# SESSION STATE
# =========================================================


def initialize_session_state(st) -> None:
    """Initialize Streamlit session state."""
    if "query_text" not in st.session_state:
        st.session_state["query_text"] = ""

    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None


def set_example_query(example: str) -> None:
    """Set an example query before the next widget render."""
    import streamlit as st

    st.session_state["query_text"] = example


# =========================================================
# HTML / CSS
# =========================================================


def render_html(
    st,
    content: str,
) -> None:
    """Render raw HTML directly with Streamlit."""
    st.html(content)


def inject_css(st) -> None:
    """Inject application-wide CSS."""
    render_html(
        st,
        """
        <style>

        /* =====================================================
           STREAMLIT CHROME
        ===================================================== */

        /*
         * Do NOT hide stHeader.
         *
         * Streamlit uses the header to provide the sidebar
         * collapse / expand control. Keeping it visible means
         * users can reopen the sidebar after collapsing it.
         */

        [data-testid="stDecoration"] {
            display: none !important;
        }

        #MainMenu {
            visibility: hidden !important;
        }

        footer {
            visibility: hidden !important;
        }

        /* =====================================================
           GLOBAL
        ===================================================== */

        .stApp {
            background:
                radial-gradient(
                    circle at 78% 5%,
                    rgba(59, 130, 246, 0.075),
                    transparent 28%
                ),
                #f7f9fc;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* =====================================================
           SIDEBAR
        ===================================================== */

        [data-testid="stSidebar"] {
            background: #0b1730;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: #dce7f7;
        }

        [data-testid="stSidebar"] .stMarkdown {
            margin-bottom: 0.25rem;
        }

        .sidebar-brand {
            padding: 0.4rem 0 1.45rem 0;
        }

        .sidebar-eyebrow {
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            color: #8db8ff;
            text-transform: uppercase;
        }

        .sidebar-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.2;
            margin-top: 0.3rem;
        }

        .sidebar-subtitle {
            font-size: 0.82rem;
            color: #91a4c2;
            line-height: 1.45;
            margin-top: 0.4rem;
        }

        .pipeline-label {
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            color: #647fa7;
            text-transform: uppercase;
            margin: 1.45rem 0 0.65rem 0;
        }

        .pipeline-item {
            display: flex;
            gap: 0.65rem;
            align-items: flex-start;
            padding: 0.52rem 0;
        }

        .pipeline-number {
            min-width: 24px;
            height: 24px;
            border-radius: 7px;
            background: rgba(59, 130, 246, 0.14);
            color: #8db8ff;
            font-size: 0.67rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .pipeline-text {
            font-size: 0.75rem;
            color: #c3d0e4;
            line-height: 1.35;
        }

        .pipeline-text strong {
            color: #f1f5fb;
        }

        .sidebar-note {
            margin-top: 1.7rem;
            padding: 0.8rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.07);
            font-size: 0.69rem;
            color: #8295b3;
            line-height: 1.5;
        }

        /* =====================================================
           MAIN HEADER
        ===================================================== */

        .eyebrow {
            font-size: 0.71rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            color: #2563eb;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            font-size: 2rem;
            line-height: 1.15;
            font-weight: 850;
            color: #0b1730;
            margin: 0;
        }

        .hero-subtitle {
            color: #65738a;
            font-size: 0.92rem;
            margin-top: 0.45rem;
            margin-bottom: 1.1rem;
        }

        /* =====================================================
           PIPELINE STRIP
        ===================================================== */

        .pipeline-strip {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 0.25rem 0 1.25rem 0;
        }

        .pipeline-chip {
            padding: 0.42rem 0.72rem;
            border-radius: 999px;
            background: #ffffff;
            border: 1px solid #e1e7f0;
            color: #34435a;
            font-size: 0.7rem;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        }

        .pipeline-arrow {
            color: #9aa8bd;
            font-size: 0.8rem;
        }

        /* =====================================================
           QUESTION
        ===================================================== */

        .section-label {
            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #718096;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        div[data-testid="stTextArea"] textarea {
            background: #ffffff;
            border: 1px solid #dfe6ef;
            border-radius: 14px;
            color: #26364f;
            font-size: 0.92rem;
            line-height: 1.6;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.045);
            padding: 1rem;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: #8db4f5;
            box-shadow:
                0 0 0 1px rgba(37, 99, 235, 0.12),
                0 8px 28px rgba(15, 23, 42, 0.045);
        }

        /* =====================================================
           BUTTONS
        ===================================================== */

        div[data-testid="stButton"] > button {
            border-radius: 9px;
            border: 1px solid #dfe6ef;
            background: #ffffff;
            color: #43536b;
            font-size: 0.72rem;
            font-weight: 600;
            min-height: 2.45rem;
            transition:
                border-color 0.15s ease,
                color 0.15s ease,
                transform 0.15s ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #93b4ef;
            color: #2563eb;
            transform: translateY(-1px);
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            background: #2563eb;
            border-color: #2563eb;
            color: #ffffff;
            font-weight: 700;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
            color: #ffffff;
        }

        /* =====================================================
           ANSWER
        ===================================================== */

        .answer-card {
            background: #ffffff;
            border: 1px solid #e1e7f0;
            border-radius: 16px;
            padding: 1.25rem 1.35rem;
            box-shadow: 0 8px 30px rgba(15, 23, 42, 0.045);
            min-height: 230px;
        }

        .answer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.85rem;
        }

        .answer-title {
            font-size: 0.98rem;
            font-weight: 800;
            color: #10203d;
        }

        .status-pill {
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: #eff6ff;
            color: #2563eb;
            font-size: 0.64rem;
            font-weight: 800;
            border: 1px solid #dbeafe;
            white-space: nowrap;
        }

        .answer-text {
            color: #34435a;
            font-size: 0.91rem;
            line-height: 1.72;
            white-space: pre-wrap;
        }

        .metadata-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .metadata-pill {
            padding: 0.3rem 0.55rem;
            border-radius: 7px;
            background: #f5f7fb;
            border: 1px solid #e6ebf2;
            color: #5d6c82;
            font-size: 0.66rem;
            font-weight: 700;
        }

        /* =====================================================
           EVIDENCE
        ===================================================== */

        .evidence-panel {
            background: #0e1d38;
            border-radius: 16px;
            padding: 1.1rem;
            min-height: 230px;
            box-shadow: 0 10px 30px rgba(11, 23, 48, 0.12);
        }

        .evidence-title {
            color: #ffffff;
            font-size: 0.98rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .evidence-subtitle {
            color: #8195b5;
            font-size: 0.7rem;
            margin-bottom: 0.85rem;
        }

        .evidence-card {
            background: rgba(255, 255, 255, 0.055);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 0.7rem;
            margin-bottom: 0.55rem;
        }

        .evidence-card:last-child {
            margin-bottom: 0;
        }

        .evidence-heading {
            color: #dbeafe;
            font-size: 0.72rem;
            font-weight: 800;
            line-height: 1.4;
            margin-bottom: 0.25rem;
        }

        .evidence-content {
            color: #aebdd2;
            font-size: 0.67rem;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .evidence-meta {
            display: flex;
            gap: 0.35rem;
            flex-wrap: wrap;
            margin-top: 0.45rem;
        }

        .evidence-tag {
            color: #91b9f7;
            font-size: 0.59rem;
            font-weight: 700;
        }

        .empty-evidence {
            color: #8195b5;
            font-size: 0.75rem;
            padding: 1rem 0;
        }

        /* =====================================================
           EVALUATION
        ===================================================== */

        .evaluation-header {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 1.7rem;
            margin-bottom: 0.7rem;
        }

        .evaluation-title {
            font-size: 0.9rem;
            font-weight: 850;
            color: #17263f;
        }

        .evaluation-caption {
            font-size: 0.65rem;
            color: #8996a9;
        }

        .metric-card {
            background: #ffffff;
            border: 1px solid #e1e7f0;
            border-radius: 12px;
            padding: 0.85rem 0.9rem;
            min-height: 90px;
        }

        .metric-label {
            color: #718096;
            font-size: 0.62rem;
            font-weight: 700;
            line-height: 1.3;
        }

        .metric-value {
            color: #10203d;
            font-size: 1.25rem;
            font-weight: 850;
            margin-top: 0.25rem;
        }

        .metric-note {
            color: #9aa7b8;
            font-size: 0.58rem;
            margin-top: 0.12rem;
        }

        .comparison-card {
            background: #ffffff;
            border: 1px solid #e1e7f0;
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin-top: 0.75rem;
        }

        .comparison-title {
            font-size: 0.72rem;
            font-weight: 800;
            color: #34435a;
            margin-bottom: 0.65rem;
        }

        .comparison-row {
            display: grid;
            grid-template-columns: 1.7fr 1fr;
            gap: 0.5rem;
            align-items: center;
            padding: 0.35rem 0;
            border-bottom: 1px solid #f0f2f6;
        }

        .comparison-row:last-child {
            border-bottom: 0;
        }

        .comparison-name {
            color: #68778d;
            font-size: 0.65rem;
        }

        .comparison-score {
            color: #17263f;
            font-size: 0.68rem;
            font-weight: 800;
            text-align: right;
        }

        /* =====================================================
           FOOTER
        ===================================================== */

        .footer-note {
            color: #97a3b3;
            font-size: 0.62rem;
            text-align: center;
            margin-top: 1.5rem;
        }

        </style>
        """,
    )


# =========================================================
# SIDEBAR
# =========================================================


def render_sidebar(st) -> None:
    """Render the project sidebar."""
    with st.sidebar:
        render_html(
            st,
            """
            <div class="sidebar-brand">
                <div class="sidebar-eyebrow">
                    AI / RAG PROJECT
                </div>

                <div class="sidebar-title">
                    VN Labor Law RAG
                </div>

                <div class="sidebar-subtitle">
                    Trợ lý Pháp lý Lao động Việt Nam
                </div>
            </div>
            """,
        )

        render_html(
            st,
            """
            <div class="pipeline-label">
                RAG PIPELINE
            </div>
            """,
        )

        pipeline_steps = [
            (
                "01",
                "Hybrid Retrieval",
                "BM25 + BGE-M3",
            ),
            (
                "02",
                "RRF Fusion",
                "Reciprocal Rank Fusion",
            ),
            (
                "03",
                "Cross-Encoder Reranking",
                "BGE-reranker-v2-m3",
            ),
            (
                "04",
                "Adaptive K",
                "K = 5 / 10 / 20",
            ),
            (
                "05",
                "Generation",
                "Gemini",
            ),
        ]

        for number, title, detail in pipeline_steps:
            safe_title = html.escape(title)
            safe_detail = html.escape(detail)

            render_html(
                st,
                f"""
                <div class="pipeline-item">
                    <div class="pipeline-number">
                        {number}
                    </div>

                    <div class="pipeline-text">
                        <strong>{safe_title}</strong><br>
                        {safe_detail}
                    </div>
                </div>
                """,
            )

        render_html(
            st,
            """
            <div class="sidebar-note">
                Evaluation-driven RAG for Vietnamese labor law.
                Answers are generated from retrieved legal context
                and accompanied by supporting evidence.
            </div>
            """,
        )


# =========================================================
# HEADER
# =========================================================


def render_header(st) -> None:
    """Render the main application header."""
    render_html(
        st,
        """
        <div class="eyebrow">
            AI / RAG ENGINEERING PROJECT
        </div>

        <div class="hero-title">
            Trợ lý Pháp lý Lao động Việt Nam
        </div>

        <div class="hero-subtitle">
            Hỏi đáp pháp luật lao động với Hybrid Retrieval,
            Adaptive Retrieval và Grounded Generation.
        </div>
        """,
    )

    render_html(
        st,
        """
        <div class="pipeline-strip">

            <span class="pipeline-chip">
                BM25 + BGE-M3
            </span>

            <span class="pipeline-arrow">
                →
            </span>

            <span class="pipeline-chip">
                RRF
            </span>

            <span class="pipeline-arrow">
                →
            </span>

            <span class="pipeline-chip">
                Cross-Encoder
            </span>

            <span class="pipeline-arrow">
                →
            </span>

            <span class="pipeline-chip">
                Adaptive K
            </span>

            <span class="pipeline-arrow">
                →
            </span>

            <span class="pipeline-chip">
                Gemini
            </span>

        </div>
        """,
    )


# =========================================================
# QUESTION INPUT
# =========================================================


def render_question_input(st) -> str:
    """Render the question input and example questions."""
    render_html(
        st,
        """
        <div class="section-label">
            CÂU HỎI PHÁP LÝ
        </div>
        """,
    )

    st.text_area(
        label="Câu hỏi pháp lý",
        key="query_text",
        height=105,
        placeholder=(
            "Ví dụ: Người lao động đơn phương chấm dứt "
            "hợp đồng lao động phải báo trước bao nhiêu ngày?"
        ),
        label_visibility="collapsed",
    )

    render_html(
        st,
        """
        <div
            class="section-label"
            style="margin-top:0.55rem;"
        >
            CÂU HỎI MẪU
        </div>
        """,
    )

    example_columns = st.columns(3)

    for index, example in enumerate(
        EXAMPLE_QUESTIONS
    ):
        with example_columns[index]:
            st.button(
                f"↗ {example}",
                key=f"example_{index}",
                use_container_width=True,
                on_click=set_example_query,
                args=(example,),
            )

    return st.session_state["query_text"]


# =========================================================
# ANSWER
# =========================================================


def render_answer(
    st,
    result: dict[str, Any],
) -> None:
    """Render the generated legal answer."""
    answer = str(
        result.get("answer", "")
    ).strip()

    complexity = str(
        result.get(
            "complexity",
            "Unknown",
        )
    )

    retrieval_budget = result.get(
        "retrieval_budget",
        "-",
    )

    safe_answer = html.escape(
        answer or "Không có nội dung trả lời."
    )

    safe_complexity = html.escape(
        complexity
    )

    safe_budget = html.escape(
        str(retrieval_budget)
    )

    render_html(
        st,
        f"""
        <div class="answer-card">

            <div class="answer-header">

                <div class="answer-title">
                    Kết luận pháp lý
                </div>

                <div class="status-pill">
                    Grounded Answer
                </div>

            </div>

            <div class="answer-text">
                {safe_answer}
            </div>

            <div class="metadata-row">

                <span class="metadata-pill">
                    Complexity: {safe_complexity}
                </span>

                <span class="metadata-pill">
                    Retrieval budget: K={safe_budget}
                </span>

            </div>

        </div>
        """,
    )


# =========================================================
# EVIDENCE
# =========================================================


def _format_score(value: Any) -> str:
    """Format a retrieval score."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "—"


def _format_sources(value: Any) -> str:
    """Format retrieval source names."""
    if isinstance(value, list):
        return " + ".join(
            str(source).upper()
            for source in value
        )

    if value is None:
        return "—"

    return str(value)


def render_evidence(
    st,
    result: dict[str, Any],
) -> None:
    """Render retrieved legal evidence."""
    chunks = result.get(
        "retrieved_chunks",
        [],
    )

    render_html(
        st,
        """
        <div class="evidence-panel">

            <div class="evidence-title">
                Căn cứ pháp lý
            </div>

            <div class="evidence-subtitle">
                Top evidence sau Cross-Encoder reranking
            </div>
        """,
    )

    if not chunks:
        render_html(
            st,
            """
            <div class="empty-evidence">
                Không có evidence được trả về.
            </div>
            """,
        )

    else:
        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            article_title = str(
                chunk.get("article_title")
                or chunk.get("title")
                or f"Evidence {index}"
            )

            content = str(
                chunk.get(
                    "content",
                    "",
                )
            ).strip()

            source_text = _format_sources(
                chunk.get(
                    "retrieval_sources"
                )
            )

            rrf_score = _format_score(
                chunk.get("rrf_score")
            )

            rerank_score = _format_score(
                chunk.get("rerank_score")
            )

            render_html(
                st,
                f"""
                <div class="evidence-card">

                    <div class="evidence-heading">
                        {index:02d} · {html.escape(article_title)}
                    </div>

                    <div class="evidence-content">
                        {html.escape(content)}
                    </div>

                    <div class="evidence-meta">

                        <span class="evidence-tag">
                            Source:
                            {html.escape(source_text)}
                        </span>

                        <span class="evidence-tag">
                            RRF:
                            {html.escape(rrf_score)}
                        </span>

                        <span class="evidence-tag">
                            Rerank:
                            {html.escape(rerank_score)}
                        </span>

                    </div>

                </div>
                """,
            )

    render_html(
        st,
        """
        </div>
        """,
    )


# =========================================================
# EVALUATION
# =========================================================


def render_evaluation(st) -> None:
    """Render the project's evaluation metrics."""
    render_html(
        st,
        """
        <div class="evaluation-header">

            <div class="evaluation-title">
                System Evaluation
            </div>

            <div class="evaluation-caption">
                30-query evaluation · current project benchmark
            </div>

        </div>
        """,
    )

    metrics = [
        (
            "Adaptive-K MRR",
            "0.8917",
            "retrieval benchmark",
        ),
        (
            "Adaptive-K Hit@3",
            "96.67%",
            "retrieval benchmark",
        ),
        (
            "Generation Success",
            "29 / 30",
            "generation regression",
        ),
        (
            "Avg Retrieval Budget",
            "10.69",
            "successful generations",
        ),
    ]

    metric_columns = st.columns(4)

    for column, (
        label,
        value,
        note,
    ) in zip(
        metric_columns,
        metrics,
    ):
        with column:
            render_html(
                st,
                f"""
                <div class="metric-card">

                    <div class="metric-label">
                        {html.escape(label)}
                    </div>

                    <div class="metric-value">
                        {html.escape(value)}
                    </div>

                    <div class="metric-note">
                        {html.escape(note)}
                    </div>

                </div>
                """,
            )

    render_html(
        st,
        """
        <div class="comparison-card">

            <div class="comparison-title">
                Retrieval quality · MRR
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    Dense
                </div>
                <div class="comparison-score">
                    0.7750
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    Dense + Reranker
                </div>
                <div class="comparison-score">
                    0.8750
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    Hybrid
                </div>
                <div class="comparison-score">
                    0.8700
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    Hybrid + Reranker
                </div>
                <div class="comparison-score">
                    0.8750
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    Adaptive-K
                </div>
                <div class="comparison-score">
                    0.8917
                </div>
            </div>

        </div>
        """,
    )

    render_html(
        st,
        """
        <div class="comparison-card">

            <div class="comparison-title">
                Adaptive-K distribution · 30 queries
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    K = 5
                </div>
                <div class="comparison-score">
                    6 queries
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    K = 10
                </div>
                <div class="comparison-score">
                    19 queries
                </div>
            </div>

            <div class="comparison-row">
                <div class="comparison-name">
                    K = 20
                </div>
                <div class="comparison-score">
                    5 queries
                </div>
            </div>

        </div>
        """,
    )


# =========================================================
# MAIN
# =========================================================


def main() -> None:
    """Run the Streamlit application."""
    import streamlit as st

    st.set_page_config(
        page_title="Vietnamese Labor Law RAG",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state(st)
    inject_css(st)
    render_sidebar(st)

    api_base_url = get_api_base_url()

    render_header(st)

    query = render_question_input(st)

    render_html(
        st,
        """
        <div style="height:0.35rem;"></div>
        """,
    )

    ask_column, info_column = st.columns(
        [1, 4],
    )

    with ask_column:
        ask_clicked = st.button(
            "Phân tích câu hỏi",
            type="primary",
            use_container_width=True,
        )

    with info_column:
        st.caption(
            "Hệ thống truy xuất các căn cứ pháp lý liên quan "
            "trước khi tạo câu trả lời."
        )

    if ask_clicked:
        with st.spinner(
            "Đang truy xuất căn cứ pháp lý và tạo câu trả lời..."
        ):
            try:
                result = ask_chat(
                    query,
                    api_base_url=api_base_url,
                )

                st.session_state["last_result"] = result

            except ChatClientError as exc:
                st.error(str(exc))

    result = st.session_state.get(
        "last_result"
    )

    if result:
        render_html(
            st,
            """
            <div style="height:0.8rem;"></div>
            """,
        )

        answer_column, evidence_column = st.columns(
            [1.45, 1],
            gap="large",
        )

        with answer_column:
            render_answer(
                st,
                result,
            )

        with evidence_column:
            render_evidence(
                st,
                result,
            )

        render_evaluation(st)

    else:
        render_html(
            st,
            """
            <div
                class="answer-card"
                style="margin-top:1rem;"
            >

                <div class="answer-header">

                    <div class="answer-title">
                        Sẵn sàng phân tích
                    </div>

                    <div class="status-pill">
                        RAG ENGINE READY
                    </div>

                </div>

                <div class="answer-text">
                    Nhập một câu hỏi pháp lý hoặc chọn một câu hỏi
                    mẫu để bắt đầu truy xuất và sinh câu trả lời.
                </div>

            </div>
            """,
        )

        render_evaluation(st)

    render_html(
        st,
        """
        <div class="footer-note">
            Vietnamese Labor Law RAG · Evaluation-driven retrieval
            and grounded generation · For research and demonstration
            purposes.
        </div>
        """,
    )


if __name__ == "__main__":
    main()