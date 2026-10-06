# Development Documentation

Tài liệu này mô tả quy trình phát triển, kiểm thử, linting và evaluation workflow của **Vietnamese Labor Law RAG**.

> **Scope:** Tài liệu phản ánh development workflow hiện tại của project, tập trung vào Python 3.11+, pytest, Ruff, Docker Compose và evaluation pipeline.

## 1. Development Environment

| Thành phần | Công nghệ |
|---|---|
| Language | Python 3.11+ |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | PostgreSQL + pgvector |
| Dense Retrieval | BGE-M3 |
| Sparse Retrieval | BM25 |
| Reranking | BGE-reranker-v2-m3 |
| Generation | Gemini / OpenAI |
| Testing | pytest |
| Linting | Ruff |
| Containerization | Docker Compose |
| CI | GitHub Actions |

---

## 2. Project Setup

Clone repository:

    git clone https://github.com/kimngoc2520/vietnamese-labor-law-rag.git
    cd vietnamese-labor-law-rag

Tạo file environment:

    cp .env.example .env

Trên Windows PowerShell:

    Copy-Item .env.example .env

Sau đó cấu hình các biến môi trường cần thiết trong `.env`.

> Không commit `.env` lên repository.

---

## 3. Python Environment

Project yêu cầu Python `>=3.11`.

Cài project:

    python -m pip install -e .

Cài development dependencies:

    python -m pip install -e ".[dev]"

Development dependencies hiện tại gồm:

- `pytest`
- `pytest-asyncio`
- `ruff`

---

## 4. Project Structure

Các thư mục chính liên quan đến development:

    vietnamese-labor-law-rag/
    ├── src/
    │   ├── api/
    │   ├── agent/
    │   ├── generation/
    │   ├── retrieval/
    │   ├── verification/
    │   └── ...
    │
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    │
    ├── evaluation/
    │   ├── scripts/
    │   └── reports/
    │
    ├── docs/
    ├── scripts/
    ├── app.py
    ├── Dockerfile
    ├── docker-compose.yml
    ├── pyproject.toml
    └── .env.example

---

## 5. Development Workflow

Development workflow chính:

    Modify Code
        ↓
    Run Tests
        ↓
    Run Ruff
        ↓
    Run Application
        ↓
    Smoke Test
        ↓
    Run Evaluation if RAG logic changed
        ↓
    Review Git Diff
        ↓
    Commit / Push

Không phải mọi thay đổi đều cần chạy toàn bộ evaluation.

Các thay đổi liên quan đến retrieval, reranking, adaptive retrieval hoặc generation nên được kiểm tra bằng evaluation benchmark tương ứng.

---

## 6. Running the Backend

FastAPI application được khai báo tại:

    src/api/main.py

Chạy local:

    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Các URL chính:

| Resource | URL |
|---|---|
| FastAPI | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

## 7. Running the Frontend

Streamlit application nằm tại:

    app.py

Chạy local:

    streamlit run app.py

UI mặc định:

    http://localhost:8501

Trong Docker Compose, Streamlit được chạy như một service riêng và giao tiếp với FastAPI thông qua API.

---

## 8. Running with Docker Compose

Build và khởi động toàn bộ hệ thống:

    docker compose up -d --build

Kiểm tra service:

    docker compose ps

Xem toàn bộ logs:

    docker compose logs

Xem log API:

    docker compose logs api

Xem log Streamlit:

    docker compose logs streamlit

Xem log PostgreSQL:

    docker compose logs postgres

Dừng hệ thống:

    docker compose down

---

## 9. Testing Strategy

Project sử dụng ba nhóm automated tests:

| Test type | Mục đích |
|---|---|
| Unit | Kiểm tra component hoặc logic riêng lẻ |
| Integration | Kiểm tra sự tương tác giữa nhiều component |
| E2E | Kiểm tra workflow ở mức application |

Test files nằm trong:

    tests/
    ├── unit/
    ├── integration/
    └── e2e/

---

## 10. Running Tests

Chạy toàn bộ test suite:

    python -m pytest tests/unit tests/integration tests/e2e -q

Kết quả gần nhất:

| Metric | Result |
|---|---:|
| Tests passed | 62 |
| Warnings | 1 |

Warning hiện tại đến từ dependency/framework và không làm test suite fail.

> Kết quả test có thể thay đổi khi source code hoặc dependencies được cập nhật.

---

## 11. Unit Tests

Unit tests kiểm tra các component có thể được kiểm thử độc lập.

Chạy:

    python -m pytest tests/unit -q

Unit tests phù hợp để kiểm tra các thay đổi như:

- API client.
- Retrieval components.
- Reranking logic.
- Adaptive retrieval logic.
- Utility functions.
- Generation-related components.

---

## 12. Integration Tests

Integration tests kiểm tra sự tương tác giữa nhiều component.

Chạy:

    python -m pytest tests/integration -q

Một integration flow có thể có dạng:

    API
      ↓
    Generation Pipeline
      ↓
    Retrieval / Generation Components
      ↓
    Response

Integration tests giúp phát hiện các lỗi xảy ra khi các component riêng lẻ kết hợp với nhau.

---

## 13. End-to-End Tests

E2E tests kiểm tra workflow ở mức application:

    User Query
        ↓
    API
        ↓
    RAG Pipeline
        ↓
    Answer

Chạy:

    python -m pytest tests/e2e -q

---

## 14. Linting

Project sử dụng Ruff để kiểm tra code quality.

Chạy:

    ruff check .

Cấu hình Ruff nằm trong `pyproject.toml`.

Các cấu hình chính:

| Setting | Value |
|---|---|
| Target version | `py311` |
| Line length | `88` |
| Ruff version | `0.16.9` |

---

## 15. Pre-Commit Checks

Trước khi commit:

    python -m pytest tests/unit tests/integration tests/e2e -q
    ruff check .

Sau đó kiểm tra thay đổi:

    git status
    git diff

Mục tiêu là đảm bảo:

- Test suite pass.
- Ruff không phát hiện lỗi.
- Không có thay đổi ngoài ý muốn.
- Không có secret trong diff.

---

## 16. API Development

API layer nằm trong:

    src/api/

Cấu trúc chính:

    src/api/
    ├── main.py
    ├── routes/
    │   ├── chat.py
    │   ├── health.py
    │   ├── feedback.py
    │   └── ingest.py
    └── schemas/
        └── chat.py

API route chịu trách nhiệm:

- Nhận HTTP request.
- Validate input.
- Gọi application/service layer.
- Serialize response.
- Xử lý HTTP errors.

RAG logic không nên được triển khai trực tiếp trong API route.

Chi tiết API:

    docs/api.md

---

## 17. RAG Pipeline Development

RAG pipeline hiện tại có flow khái quát:

    Query
      ↓
    Complexity Classification
      ↓
    Adaptive Retrieval
      ↓
    Dense + BM25
      ↓
    RRF
      ↓
    Cross-Encoder Reranking
      ↓
    Subject-aware Adjustment
      ↓
    Evidence Selection
      ↓
    LLM Generation
      ↓
    Answer + Citations

Khi thay đổi một thành phần trong flow này, nên chạy automated tests và evaluation benchmark tương ứng.

Chi tiết architecture:

    docs/architecture.md

---

## 18. Evaluation Development

Evaluation scripts nằm trong:

    evaluation/scripts/

Các benchmark chính:

| Script | Mục đích |
|---|---|
| `run_retrieval_benchmark.py` | Đánh giá retrieval |
| `run_hybrid_benchmark.py` | Đánh giá hybrid retrieval |
| `run_adaptive_benchmark.py` | Đánh giá Adaptive-K |
| `run_quality_cost_benchmark.py` | Đánh giá quality–cost |
| `run_generation_regression.py` | Đánh giá generation regression |
| `run_full_evaluation.py` | Chạy toàn bộ evaluation pipeline |

Chạy toàn bộ:

    python evaluation/scripts/run_full_evaluation.py

---

## 19. Khi Nào Cần Chạy Evaluation?

| Thay đổi | Automated Tests | Evaluation |
|---|---|---|
| UI | Có | Không bắt buộc |
| API validation | Có | Không bắt buộc |
| API response schema | Có | Không bắt buộc |
| Retrieval | Có | Nên chạy |
| Reranking | Có | Nên chạy |
| Adaptive-K | Có | Nên chạy |
| Generation prompt | Có | Nên chạy generation regression |
| LLM configuration | Có | Nên chạy generation regression |
| Embedding / database retrieval | Có | Nên chạy retrieval benchmark |
| Evaluation scripts | Có | Chạy benchmark liên quan |

---

## 20. Generation Regression

Generation regression được sử dụng để kiểm tra độ ổn định của generation trên evaluation queries.

Chạy:

    python evaluation/scripts/run_generation_regression.py

Các thông tin được theo dõi gồm:

- Success rate.
- Query complexity.
- Retrieval budget.
- Citation count.
- Generation errors.

Kết quả gần nhất:

| Metric | Result |
|---|---:|
| Successful queries | 29 / 30 |
| Success rate | 96.67% |
| Average retrieval budget | 10.69 |
| Average citations | 1.24 |

---

## 21. Git Workflow

Kiểm tra trạng thái:

    git status

Xem thay đổi:

    git diff

Stage files:

    git add <files>

Commit:

    git commit -m "type: short description"

Push:

    git push

Một số commit message phù hợp:

| Type | Ví dụ |
|---|---|
| `feat` | `feat: add adaptive retrieval benchmark` |
| `fix` | `fix: handle invalid chat response` |
| `refactor` | `refactor: simplify RAG workflow` |
| `docs` | `docs: update API documentation` |
| `test` | `test: add chat client tests` |

Commit message nên mô tả ngắn gọn thay đổi chính.

---

## 22. Continuous Integration

Project sử dụng GitHub Actions cho evaluation workflow.

Workflow:

    .github/workflows/evaluation.yml

CI sử dụng Python 3.11, cài project cùng development dependencies và chạy:

    python evaluation/scripts/run_full_evaluation.py

Workflow hiện có thể được kích hoạt:

- Theo schedule.
- Thủ công thông qua `workflow_dispatch`.

---

## 23. Debugging Workflow

Khi application gặp lỗi, nên kiểm tra theo thứ tự:

    Environment
        ↓
    Docker / Process
        ↓
    API Health
        ↓
    API Logs
        ↓
    Automated Tests
        ↓
    RAG Pipeline
        ↓
    Evaluation

Một số lệnh hữu ích:

    docker compose ps
    docker compose logs api
    curl http://localhost:8000/health

Sau đó chạy:

    python -m pytest tests/unit tests/integration tests/e2e -q

---

## 24. Common Development Issues

### Streamlit không tìm thấy module

Nếu chạy Streamlit trực tiếp và gặp `ModuleNotFoundError`, kiểm tra Python environment hiện tại và development dependencies.

Có thể chạy thông qua Docker Compose:

    docker compose up -d --build

### API không phản hồi

Kiểm tra:

    docker compose ps
    docker compose logs api

Sau đó:

    curl http://localhost:8000/health

### Test fail sau khi sửa API

Chạy test liên quan trước:

    python -m pytest tests/unit/test_chat_client.py -q

Sau khi sửa:

    python -m pytest tests/unit tests/integration tests/e2e -q

### Retrieval quality giảm

Không chỉ dựa vào automated tests.

Chạy benchmark:

    python evaluation/scripts/run_retrieval_benchmark.py
    python evaluation/scripts/run_adaptive_benchmark.py

So sánh:

- Hit@1.
- Hit@3.
- Hit@5.
- MRR.
- Retrieval budget.

---

## 25. Development Principles

### Keep API Thin

API route nên tập trung vào HTTP layer và không chứa toàn bộ RAG logic.

### Keep Components Separated

Retrieval, reranking, generation và verification nên được tổ chức thành các component riêng.

### Test Before Commit

Mọi thay đổi quan trọng nên được kiểm tra bằng automated tests.

### Evaluate RAG Changes

Automated tests kiểm tra correctness, nhưng không đủ để chứng minh retrieval hoặc generation quality.

### Avoid Unnecessary Complexity

Chỉ thêm abstraction hoặc component mới khi có requirement thực tế.

### Keep Configuration External

API keys, database credentials và environment-specific configuration không được hard-code trong source code.

---

## 26. Development Checklist

### Trước khi code

- [ ] Xác định component cần thay đổi.
- [ ] Kiểm tra implementation hiện tại.
- [ ] Kiểm tra test liên quan.
- [ ] Kiểm tra documentation nếu behavior thay đổi.

### Sau khi code

- [ ] Chạy unit tests.
- [ ] Chạy integration tests.
- [ ] Chạy E2E tests nếu liên quan.
- [ ] Chạy Ruff.
- [ ] Kiểm tra Git diff.

### Nếu thay đổi RAG

- [ ] Chạy retrieval benchmark.
- [ ] Chạy adaptive benchmark nếu liên quan.
- [ ] Chạy generation regression nếu liên quan.
- [ ] So sánh kết quả với baseline.

### Trước khi push

- [ ] Không có secret trong diff.
- [ ] `.env` không được tracked.
- [ ] Tests pass.
- [ ] Ruff pass.
- [ ] Commit message rõ ràng.

---

## 27. Related Documentation

| Document | Nội dung |
|---|---|
| `README.md` | Project overview và quick start |
| `docs/architecture.md` | System architecture |
| `docs/api.md` | API documentation |
| `docs/deployment.md` | Docker deployment |
| `docs/evaluation_methodology.md` | Evaluation methodology |
| `evaluation/README.md` | Evaluation workflow |

---

## 28. Disclaimer

Development workflow trong tài liệu này phản ánh trạng thái hiện tại của project và có thể thay đổi khi hệ thống tiếp tục được phát triển.

Các evaluation metrics phản ánh kết quả trên evaluation dataset hiện tại và không nên được hiểu là đảm bảo chất lượng trong mọi tình huống sử dụng thực tế.