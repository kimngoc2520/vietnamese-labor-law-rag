# API Documentation

API của **Vietnamese Labor Law RAG** được xây dựng bằng **FastAPI**, đóng vai trò là lớp giao tiếp giữa giao diện người dùng và RAG pipeline.

Backend tiếp nhận câu hỏi, thực hiện retrieval → reranking → evidence selection → generation và trả về câu trả lời cùng các thông tin liên quan.

> **API scope:** Tài liệu này mô tả API theo implementation hiện tại của project. Các endpoint hoặc response field chưa được xác nhận trong source code không được giả định thêm.

---

## 1. Tổng quan

| Thuộc tính | Giá trị |
|---|---|
| Framework | FastAPI |
| API Style | REST |
| Default Host | `localhost` |
| Default Port | `8000` |
| Base URL | `http://localhost:8000` |
| API Documentation | `/docs` |
| Alternative Documentation | `/redoc` |
| Request Content-Type | `application/json` |

Khi chạy bằng Docker Compose:

~~~text
FastAPI:  http://localhost:8000
Swagger:  http://localhost:8000/docs
ReDoc:    http://localhost:8000/redoc
~~~

---

## 2. Kiến trúc API

~~~mermaid
flowchart LR
    A[Client / Streamlit] --> B[FastAPI]

    B --> C[Chat Route]
    B --> D[Health Route]
    B --> E[Feedback Route]
    B --> F[Ingest Route]

    C --> G[Generation Pipeline]
    G --> H[Retrieval]
    G --> I[Reranking]
    G --> J[Generation]
    G --> K[Evidence Selection]
~~~

API được tổ chức trong:

~~~text
src/api/
├── main.py
├── schemas/
└── routes/
    ├── chat.py
    ├── health.py
    ├── feedback.py
    └── ingest.py
~~~

---

## 3. API Endpoints

| Method | Endpoint | Mục đích |
|---|---|---|
| `POST` | `/chat` | Gửi câu hỏi và nhận câu trả lời RAG |
| `GET` | `/health` | Kiểm tra trạng thái backend |
| `POST` | `/feedback` | Xử lý feedback |
| `POST` | `/ingest` | Xử lý document ingestion |

Endpoint chính của ứng dụng là:

~~~text
POST /chat
~~~

---

## 4. Chat API

### `POST /chat`

Gửi một câu hỏi pháp luật lao động và nhận kết quả từ RAG pipeline.

**Request header:**

~~~http
Content-Type: application/json
~~~

### Request Body

Request sử dụng `ChatRequest`.

~~~json
{
  "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?"
}
~~~

### Request Schema

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `query` | `string` | Có | Câu hỏi của người dùng |

`query` phải có ít nhất một ký tự.

---

## 5. Request Validation

API thực hiện validation trước khi chạy `GenerationPipeline`.

### Request hợp lệ

~~~json
{
  "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?"
}
~~~

Request được tiếp tục xử lý.

### Request rỗng

~~~json
{
  "query": ""
}
~~~

API trả về:

~~~text
HTTP 400 Bad Request
~~~

với response:

~~~json
{
  "detail": "Query must not be empty."
}
~~~

### Request thiếu field

Ví dụ:

~~~json
{}
~~~

FastAPI thực hiện schema validation và trả về:

~~~text
HTTP 422 Unprocessable Entity
~~~

---

## 6. Chat Response

Response sử dụng `ChatResponse`.

Ví dụ:

~~~json
{
  "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?",
  "answer": "Theo quy định của pháp luật lao động...",
  "citations": [
    "Bộ luật Lao động 2019, Điều ..."
  ],
  "complexity": "Medium",
  "retrieval_budget": 10,
  "retrieved_chunks": [
    {
      "content": "..."
    }
  ]
}
~~~

### Response Schema

| Field | Type | Mô tả |
|---|---|---|
| `query` | `string` | Câu hỏi đã được xử lý |
| `answer` | `string` | Câu trả lời được sinh bởi LLM |
| `citations` | `list[string]` | Các citation được chọn |
| `complexity` | `string` | Mức độ phức tạp của query |
| `retrieval_budget` | `integer` | Ngân sách retrieval được sử dụng |
| `retrieved_chunks` | `list[object]` | Các chunk được truy xuất |

### `retrieved_chunks`

`retrieved_chunks` là danh sách các object chứa thông tin về các chunk được retrieval pipeline trả về.

Các field cụ thể của từng chunk phụ thuộc vào object được trả về bởi retrieval pipeline.

Ví dụ khái quát:

~~~json
{
  "content": "Nội dung chunk...",
  "score": 0.91
}
~~~

> Không nên xem các field minh họa như `score`, `article_title` là API contract bắt buộc nếu chúng chưa được khai báo cố định trong response schema.

### `citations`

`citations` là danh sách string đại diện cho các nguồn được lựa chọn để hỗ trợ câu trả lời.

Ví dụ:

~~~json
{
  "citations": [
    "Bộ luật Lao động 2019, Điều ..."
  ]
}
~~~

---

## 7. Chat Processing Flow

Khi nhận `POST /chat`, API thực hiện:

~~~mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant P as GenerationPipeline
    participant R as Retrieval
    participant G as LLM
    participant V as Verification

    C->>A: POST /chat
    A->>A: Validate request
    A->>P: run(query)
    P->>R: Retrieve evidence
    R-->>P: Ranked candidates
    P->>G: Generate answer
    G-->>P: Answer
    P->>V: Select evidence
    V-->>P: Citations
    P-->>A: GenerationResult
    A-->>C: ChatResponse
~~~

Luồng xử lý khái quát:

~~~text
ChatRequest
    ↓
Validation
    ↓
GenerationPipeline
    ↓
Retrieval
    ↓
Reranking
    ↓
Evidence Selection
    ↓
LLM Generation
    ↓
ChatResponse
~~~

---

## 8. Generation Pipeline

Route `/chat` không trực tiếp triển khai toàn bộ retrieval và generation logic.

Thay vào đó, route gọi:

~~~python
GenerationPipeline().run(query=query)
~~~

Pipeline chịu trách nhiệm điều phối các bước RAG.

~~~text
POST /chat
    │
    ▼
ChatRequest
    │
    ▼
GenerationPipeline
    │
    ├── Complexity Classification
    ├── Adaptive Retrieval
    ├── Dense Retrieval
    ├── BM25
    ├── RRF Fusion
    ├── Cross-Encoder Reranking
    ├── Subject-aware Adjustment
    ├── Evidence Selection
    └── LLM Generation
    │
    ▼
ChatResponse
~~~

Chi tiết kiến trúc pipeline được mô tả trong:

~~~text
docs/architecture.md
~~~

---

## 9. Error Handling

API sử dụng HTTP status code để biểu diễn trạng thái request.

| Status | Trường hợp |
|---|---|
| `200` | Request thành công |
| `400` | Request không hợp lệ |
| `422` | Request không đáp ứng schema |
| `500` | Lỗi trong quá trình generation |

### Generation Error

Nếu xảy ra exception trong `GenerationPipeline`, route chuyển exception thành HTTP `500`.

Response có dạng:

~~~json
{
  "detail": "Generation failed: <error message>"
}
~~~

Điều này giúp client nhận được response có cấu trúc thay vì để exception thoát trực tiếp khỏi API layer.

---

## 10. Health API

### `GET /health`

Endpoint dùng để kiểm tra trạng thái backend.

~~~text
GET http://localhost:8000/health
~~~

Endpoint này phù hợp để:

- Kiểm tra FastAPI container.
- Kiểm tra backend trước khi sử dụng UI.
- Kiểm tra service trong quá trình development.
- Sử dụng cho health check khi triển khai.

Ví dụ:

~~~bash
curl http://localhost:8000/health
~~~

> **Implementation note:** Response body cụ thể của `/health` cần được xem theo implementation hiện tại trong `src/api/routes/health.py`; tài liệu này không giả định một response schema chưa được xác nhận.

---

## 11. Feedback API

### `POST /feedback`

Endpoint dành cho feedback từ client.

~~~text
POST http://localhost:8000/feedback
~~~

Route được đăng ký tại:

~~~text
src/api/routes/feedback.py
~~~

> **Implementation note:** Request/response schema cụ thể của endpoint này phụ thuộc implementation hiện tại. Không nên xem endpoint này là API contract hoàn chỉnh nếu schema chưa được mô tả trong tài liệu.

---

## 12. Ingestion API

### `POST /ingest`

Endpoint dành cho document ingestion.

~~~text
POST http://localhost:8000/ingest
~~~

Route được đăng ký tại:

~~~text
src/api/routes/ingest.py
~~~

Endpoint phục vụ quá trình đưa dữ liệu tài liệu vào hệ thống để phục vụ retrieval.

> **Implementation note:** Request/response schema cụ thể cần được xem trực tiếp trong implementation của `src/api/routes/ingest.py`.

---

## 13. Swagger UI và ReDoc

FastAPI tự động cung cấp Swagger UI:

~~~text
http://localhost:8000/docs
~~~

Swagger UI cho phép:

- Xem endpoint.
- Xem request schema.
- Xem response schema.
- Gửi request trực tiếp.
- Kiểm tra API trong quá trình development.

ReDoc:

~~~text
http://localhost:8000/redoc
~~~

ReDoc cung cấp một giao diện tài liệu API phù hợp để đọc và tham khảo.

---

## 14. Gọi API bằng cURL

### Chat

~~~bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Người lao động được nghỉ phép năm bao nhiêu ngày?\"}"
~~~

### Health Check

~~~bash
curl "http://localhost:8000/health"
~~~

---

## 15. Gọi API bằng Python

Có thể sử dụng `requests` để gọi Chat API:

~~~python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?"
    },
)

data = response.json()

print(data["answer"])
print(data["citations"])
~~~

---

## 16. Tích hợp với Streamlit

Streamlit đóng vai trò client chính của hệ thống.

~~~mermaid
sequenceDiagram
    participant U as Người dùng
    participant S as Streamlit
    participant A as FastAPI
    participant P as RAG Pipeline

    U->>S: Nhập câu hỏi
    S->>A: POST /chat
    A->>P: run(query)
    P-->>A: GenerationResult
    A-->>S: ChatResponse
    S-->>U: Answer + Evidence
~~~

Streamlit giao tiếp với backend thông qua API thay vì trực tiếp phụ thuộc vào implementation bên trong RAG pipeline.

~~~text
Streamlit
    ↓
FastAPI
    ↓
RAG Pipeline
    ↓
Retrieval + Reranking + Generation
~~~

---

## 17. API Contract

Contract chính giữa frontend và backend:

~~~text
Client
  │
  │  ChatRequest
  ▼
POST /chat
  │
  │  query
  ▼
GenerationPipeline
  │
  │  GenerationResult
  ▼
ChatResponse
  │
  ├── query
  ├── answer
  ├── citations
  ├── complexity
  ├── retrieval_budget
  └── retrieved_chunks
  │
  ▼
Client
~~~

API layer chịu trách nhiệm HTTP communication, trong khi RAG pipeline chịu trách nhiệm xử lý domain logic.

---

## 18. Source Code Mapping

| API Component | Source |
|---|---|
| FastAPI application | `src/api/main.py` |
| Chat route | `src/api/routes/chat.py` |
| Chat schemas | `src/api/schemas/chat.py` |
| Health route | `src/api/routes/health.py` |
| Feedback route | `src/api/routes/feedback.py` |
| Ingestion route | `src/api/routes/ingest.py` |
| Generation pipeline | `src/generation/pipeline.py` |
| Evidence selection | `src/verification/evidence.py` |
| Streamlit client | `app.py` |

---

## 19. Chạy API bằng Docker

Khởi động hệ thống:

~~~bash
docker compose up -d --build
~~~

Kiểm tra container:

~~~bash
docker compose ps
~~~

Sau khi FastAPI khởi động:

~~~text
API:
http://localhost:8000

Swagger:
http://localhost:8000/docs

ReDoc:
http://localhost:8000/redoc
~~~

---

## 20. Development và Testing

Trong quá trình phát triển, chạy automated tests:

~~~bash
python -m pytest tests/unit tests/integration tests/e2e -q
~~~

Kiểm tra lint:

~~~bash
ruff check .
~~~

API có thể được kiểm tra qua:

1. Unit tests.
2. Integration tests.
3. End-to-end tests.
4. Swagger UI.
5. Streamlit UI.

---

## 21. CORS và Timeout

### CORS

Tài liệu hiện tại không giả định cấu hình CORS nếu chưa được khai báo trong FastAPI application.

Nếu frontend và backend được triển khai trên các origin khác nhau, CORS cần được cấu hình tại FastAPI.

Trong deployment hiện tại, Streamlit và FastAPI được chạy cùng hệ thống Docker Compose nên client có thể giao tiếp với backend thông qua API URL được cấu hình.

### Timeout

Không có một timeout SLA cố định được khai báo trong API contract hiện tại.

Thời gian response phụ thuộc vào:

- Retrieval.
- Cross-Encoder Reranking.
- LLM provider.
- Network.
- Backend resources.

Do đó không nên đưa ra một expected latency cố định nếu chưa có benchmark latency riêng.

---

## 22. Design Principles

### Tách API khỏi RAG Logic

Route chỉ chịu trách nhiệm HTTP request/response. Retrieval và generation nằm trong các module chuyên biệt.

### Schema rõ ràng

Request và response được định nghĩa bằng Pydantic models.

### Validation ở API Boundary

Input không hợp lệ được phát hiện trước khi đi vào pipeline.

### Error Handling

Exception trong pipeline được chuyển thành HTTP response phù hợp.

### Frontend độc lập

Streamlit giao tiếp với hệ thống thông qua API thay vì phụ thuộc trực tiếp vào implementation bên trong.

### Có thể mở rộng

Các route `feedback` và `ingest` được tách riêng để có thể mở rộng mà không làm phức tạp `chat` endpoint.

---

## 23. API Summary

~~~mermaid
flowchart TD
    A[Client] --> B[FastAPI]
    B --> C[Validation]
    C --> D[Generation Pipeline]

    D --> E[Adaptive Retrieval]
    E --> F[Hybrid Retrieval]
    F --> G[RRF]
    G --> H[Reranking]
    H --> I[Evidence Selection]
    I --> J[LLM Generation]

    J --> K[ChatResponse]
    K --> B
    B --> A
~~~

Endpoint chính:

~~~text
POST /chat
~~~

Endpoint hỗ trợ:

~~~text
GET  /health
POST /feedback
POST /ingest
~~~

API documentation:

~~~text
http://localhost:8000/docs
~~~

---

## 24. Lưu ý

API là lớp giao tiếp của hệ thống và không trực tiếp đảm bảo chất lượng pháp lý của câu trả lời.

Chất lượng đầu ra phụ thuộc vào:

- Retrieval.
- Reranking.
- Evidence Selection.
- Dữ liệu pháp luật.
- LLM provider.
- Cấu hình hệ thống.

Kết quả từ hệ thống phục vụ mục đích nghiên cứu và hỗ trợ tra cứu, không thay thế tư vấn pháp lý chuyên nghiệp hoặc cách giải thích chính thức của cơ quan có thẩm quyền.