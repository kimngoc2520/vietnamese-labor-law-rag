# 🇻🇳 Vietnamese Labor Law RAG

<p align="center">
  <img src="assets/hero-banner.png" alt="Vietnamese Labor Law RAG" width="100%">
</p>

<p align="center">
  <strong>Evaluation-Driven RAG System for Vietnamese Labor Law</strong>
</p>

<p align="center">
  Hybrid Retrieval · Adaptive Retrieval · Reranking · Evidence Selection · Grounded Generation
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-336791)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-62%20passed-success)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-blue)

</p>

---

## 📌 Mục lục

- [🎯 Tổng quan](#-tổng-quan)
- [📊 Benchmark Snapshot](#-benchmark-snapshot)
- [✨ Tính năng chính](#-tính-năng-chính)
- [🏗️ Kiến trúc hệ thống](#️-kiến-trúc-hệ-thống)
- [🔍 Retrieval Pipeline](#-retrieval-pipeline)
- [⚡ Adaptive Retrieval](#-adaptive-retrieval)
- [🤖 Generation & Evidence](#-generation--evidence)
- [📥 Document Ingestion](#-document-ingestion)
- [📈 Evaluation](#-evaluation)
- [🛠️ Tech Stack](#️-tech-stack)
- [🖥️ Demo](#️-demo)
- [🚀 Quick Start](#-quick-start)
- [🐳 Docker](#-docker)
- [🔌 API](#-api)
- [🧪 Testing](#-testing)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration](#️-configuration)
- [🔄 Development Workflow](#-development-workflow)
- [🤖 CI / Evaluation](#-ci--evaluation)
- [🖼️ Documentation Assets](#️-documentation-assets)
- [⚠️ Common Issues](#️-common-issues)
- [📌 Limitations](#-limitations)
- [⚖️ Disclaimer](#️-disclaimer)
- [📚 Documentation](#-documentation)

---

# 🎯 Tổng quan

**Vietnamese Labor Law RAG** là hệ thống Retrieval-Augmented Generation (RAG) chuyên biệt cho bài toán **hỏi đáp pháp luật lao động Việt Nam**.

Thay vì để Large Language Model tự trả lời dựa trên kiến thức nội tại, hệ thống trước tiên truy xuất các đoạn văn bản pháp luật liên quan, rerank candidate pool, lựa chọn evidence phù hợp và sau đó sử dụng LLM để tạo câu trả lời dựa trên nguồn đã truy xuất.

Dự án được xây dựng theo hướng **evaluation-driven development**:

> **Retrieve → Rerank → Select Evidence → Generate → Evaluate → Improve**

Mục tiêu chính là nghiên cứu sự đánh đổi giữa:

- Retrieval quality
- Evidence relevance
- Retrieval budget
- Reranking cost
- Answer grounding
- Citation quality

### 📚 Corpus hiện tại

Hệ thống hiện sử dụng:

- **5 văn bản pháp luật**
- khoảng **470 chunks**
- Dense Retrieval với **BGE-M3**
- Sparse Retrieval với **BM25**
- **RRF** để hợp nhất kết quả
- Cross-Encoder để rerank candidate pool
- Gemini cho generation

---

# 📊 Benchmark Snapshot

Evaluation hiện tại sử dụng bộ **30 queries** cho retrieval và generation regression.

## Retrieval

| Pipeline | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Dense Retrieval | 0.600 | 0.900 | 1.000 | 0.775 |
| Dense + Reranker | **0.800** | — | — | **0.875** |
| Hybrid Retrieval | — | — | — | 0.870 |
| Hybrid + Reranker | — | — | — | **0.875** |

## Adaptive Retrieval

| Method | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Fixed K = 5 | 0.800 | 0.967 | 1.000 | 0.892 |
| Fixed K = 10 | 0.800 | 0.967 | 1.000 | 0.892 |
| Fixed K = 20 | 0.800 | 0.967 | 1.000 | 0.892 |
| Adaptive K | **0.800** | **0.967** | **1.000** | **0.892** |

> Trên tập 30 query hiện tại, các cấu hình đạt kết quả retrieval tương đương. Lợi ích chính của Adaptive-K nằm ở việc điều chỉnh retrieval budget theo độ phức tạp của query, với average retrieval budget khoảng **10.69**, thấp hơn Fixed-K = 20.

### Adaptive-K Distribution

| Retrieval Budget | Số queries |
|---|---:|
| K = 5 | 6 |
| K = 10 | 19 |
| K = 20 | 5 |
| **Total** | **30** |

## Generation Regression

| Metric | Result |
|---|---:|
| Total queries | 30 |
| Successful | 29 |
| Errors | 1 |
| Success rate | **96.67%** |
| Avg. retrieval budget | **10.69** |
| Avg. citations | **1.24** |

Generation regression hiện tại có 1 lỗi `Gemini không trả về nội dung`. Đây là lỗi runtime/provider response và không phải lỗi của test pipeline.

---

# ✨ Tính năng chính

## 🔎 Hybrid Retrieval

Kết hợp:

- **BM25** — lexical / sparse retrieval
- **BGE-M3** — semantic / dense retrieval
- **RRF** — Reciprocal Rank Fusion

Hybrid retrieval giúp hệ thống vừa xử lý tốt các trường hợp cần exact matching như:

- tên văn bản pháp luật;
- số điều;
- thuật ngữ pháp lý;

vừa xử lý được các query có cách diễn đạt khác với nội dung trong văn bản nhưng vẫn cùng ý nghĩa.

## ⚡ Adaptive Retrieval

Không sử dụng cùng một retrieval budget cho mọi query.

Query được phân loại thành:

| Complexity | Retrieval Budget |
|---|---:|
| Simple | K = 5 |
| Medium | K = 10 |
| Complex | K = 20 |

Complexity classifier hiện tại là **rule-based baseline**, dựa trên các đặc trưng có thể giải thích như:

- độ dài query;
- số lượng mệnh đề;
- điều kiện và quan hệ được đề cập;
- phạm vi pháp lý.

## 🎯 Cross-Encoder Reranking

Candidate pool được rerank bằng:

`BAAI/bge-reranker-v2-m3`

Reranking được thực hiện trên candidate pool thay vì toàn bộ corpus nhằm cân bằng:

> **Retrieval Quality ↔ Inference Cost**

## 👤 Subject-aware Adjustment

Sau reranking, hệ thống thực hiện điều chỉnh nhẹ dựa trên **chủ thể pháp lý** được đề cập trong query.

Ví dụ:

- người lao động;
- người sử dụng lao động.

Điều này giúp giảm trường hợp các điều luật có nội dung hoặc từ khóa tương tự nhưng áp dụng cho các chủ thể khác nhau bị xếp sai thứ tự.

## 📚 Evidence-grounded Generation

LLM được cung cấp các evidence đã được retrieval và reranking lựa chọn cùng với generation instructions.

LLM không trực tiếp truy vấn toàn bộ database hoặc corpus.

## 🔗 Citation & Evidence Selection

Sau khi câu trả lời được tạo, verification layer đối chiếu câu trả lời với retrieved evidence để xác định evidence phù hợp và xây dựng citations.

Nhờ đó, câu trả lời có thể truy nguyên về các nguồn pháp lý được hệ thống sử dụng.

## 🧪 Evaluation-driven Development

Evaluation được tách khỏi runtime application để benchmark độc lập:

- Dense Retrieval
- Hybrid Retrieval
- Reranking
- Adaptive-K
- Quality–Cost trade-off
- Generation Regression

---

# 🏗️ Kiến trúc hệ thống

Tổng thể hệ thống được tổ chức thành các lớp từ giao diện người dùng, API, RAG pipeline, retrieval/generation đến database và evaluation.

<p align="center">
  <img src="assets/architecture.png" alt="Vietnamese Labor Law RAG Architecture" width="95%">
</p>

### High-level Flow

**User Query → Streamlit → FastAPI → Generation Pipeline → Retrieval → Reranking → Evidence Selection → Gemini → Answer + Citations**

---

# 🔍 Retrieval Pipeline

Retrieval là phần cốt lõi của hệ thống. Pipeline kết hợp adaptive budget, sparse retrieval, dense retrieval, RRF và cross-encoder reranking.

<p align="center">
  <img src="assets/pipeline.png" alt="Vietnamese Labor Law RAG Pipeline" width="95%">
</p>

## 1. Query Complexity

Query được phân loại trước khi retrieval:

| Complexity | K |
|---|---:|
| Simple | 5 |
| Medium | 10 |
| Complex | 20 |

Đây là **rule-based classifier**, không phải machine-learning classifier.

## 2. Dense Retrieval

Sử dụng **BGE-M3** để biểu diễn query và document chunk dưới dạng vector.

Dense retrieval phù hợp khi:

- query và document sử dụng từ ngữ khác nhau;
- cần tìm các đoạn có cùng ý nghĩa;
- semantic similarity quan trọng hơn exact keyword matching.

## 3. Sparse Retrieval

Sử dụng **BM25** để tìm kiếm dựa trên lexical matching.

BM25 đặc biệt hữu ích với:

- tên văn bản pháp luật;
- số điều;
- thuật ngữ pháp lý;
- từ khóa chính xác.

## 4. Reciprocal Rank Fusion

Kết quả từ Dense Retrieval và BM25 được hợp nhất bằng **RRF** với:

`RRF_K = 60`

RRF giúp kết hợp ranking từ nhiều retrieval source mà không cần phụ thuộc trực tiếp vào thang điểm của từng retriever.

## 5. Cross-Encoder Reranking

Candidate pool được đưa vào:

`BAAI/bge-reranker-v2-m3`

Cross-Encoder đánh giá trực tiếp mức độ liên quan giữa:

> Query + Candidate Chunk

Reranking là bước computationally expensive hơn retrieval, vì vậy candidate pool được giới hạn trước khi chạy cross-encoder.

## 6. Subject-aware Adjustment

Sau reranking, hệ thống điều chỉnh nhẹ ranking dựa trên chủ thể pháp lý.

Mục tiêu là ưu tiên evidence phù hợp với chủ thể được đề cập trong query.

## 7. Final Evidence

Sau reranking và subject-aware adjustment, hệ thống lấy:

`final_top_k = 5`

Các chunk này được đưa vào generation context.

<p align="center">
  <img src="assets/retrieval-pipeline.png" alt="Retrieval Pipeline" width="95%">
</p>

---

# ⚡ Adaptive Retrieval

Adaptive Retrieval là một trong những thành phần chính của hệ thống.

Thay vì sử dụng cùng một budget cho mọi query, hệ thống điều chỉnh số lượng candidate dựa trên độ phức tạp:

| Complexity | Retrieval Budget |
|---|---:|
| Simple | K = 5 |
| Medium | K = 10 |
| Complex | K = 20 |

Trên 30 queries hiện tại:

| K | Số queries |
|---:|---:|
| 5 | 6 |
| 10 | 19 |
| 20 | 5 |

Average retrieval budget:

**10.69 candidates/query**

<p align="center">
  <img src="assets/retrieval-strategy-comparison.png" alt="Retrieval Strategy Comparison" width="90%">
</p>

> Trên benchmark hiện tại, Fixed-K và Adaptive-K đạt cùng các chỉ số retrieval. Vì vậy, Adaptive-K được xem như cơ chế điều chỉnh budget theo query complexity; lợi ích về chất lượng chưa thể hiện rõ trên bộ 30 query hiện tại.

---

# 🤖 Generation & Evidence

Sau retrieval và reranking, hệ thống chuyển sang generation với evidence đã được lựa chọn.

## Generation

LLM mặc định:

**Gemini**

OpenAI có thể được cấu hình thông qua environment/configuration.

Generation input gồm:

- User Query
- Selected Evidence
- System Prompt
- Generation Instructions

Luồng xử lý:

**User Query + Selected Evidence → Prompt Construction → Gemini → Generated Answer**

LLM không trực tiếp truy vấn PostgreSQL hoặc toàn bộ corpus.

## Evidence Selection

Sau khi câu trả lời được tạo, verification layer đối chiếu câu trả lời với retrieved evidence để xác định evidence phù hợp và xây dựng citations.

**Retrieved Evidence → Generation → Answer → Evidence Selection → Citations**

Điều này giúp câu trả lời có khả năng truy nguyên về nguồn pháp lý đã được retrieval.

---

# 📥 Document Ingestion

Tài liệu pháp luật được đưa vào hệ thống theo pipeline:

**Legal Documents → Document Loading → PDF Extraction / OCR → Chunking → Metadata Extraction → BGE-M3 Embedding → PostgreSQL + pgvector**

Hệ thống hỗ trợ:

- PDF text extraction;
- OCR cho scanned PDF;
- Vietnamese OCR với Tesseract;
- chunking;
- metadata extraction;
- vector embedding.

Corpus hiện tại gồm **5 văn bản pháp luật** với khoảng **470 chunks**.

---

# 📈 Evaluation

Evaluation được thiết kế thành một pipeline độc lập với runtime application.

## Retrieval Evaluation

Các metrics chính:

- Hit@1
- Hit@3
- Hit@5
- MRR

Ground truth được xác định theo:

`document_id + chunk_index`

thay vì chỉ sử dụng substring matching ở mức article, giúp tránh các trường hợp nhầm giữa các điều khoản có số gần nhau.

## Adaptive-K Evaluation

So sánh:

- Fixed K = 5
- Fixed K = 10
- Fixed K = 20
- Adaptive K

Mục tiêu:

> Giữ chất lượng retrieval trong khi điều chỉnh retrieval budget theo từng query.

## Quality–Cost Evaluation

Quality–Cost benchmark được dùng để quan sát trade-off giữa:

- retrieval budget;
- số candidate được xử lý;
- retrieval quality.

Adaptive retrieval hiện có average retrieval budget khoảng **10.69**, thấp hơn Fixed K = 20 và gần Fixed K = 10.

## Generation Regression

Generation regression chạy trên 30 queries và theo dõi:

- success rate;
- complexity distribution;
- retrieval budget;
- citation count;
- generation errors.

Kết quả gần nhất:

- **29/30** queries thành công;
- **96.67%** success rate;
- **10.69** average retrieval budget;
- **1.24** average citations.

## Evaluation Commands

### Full Evaluation

~~~bash
python evaluation/scripts/run_full_evaluation.py
~~~

### Retrieval Benchmark

~~~bash
python evaluation/scripts/run_retrieval_benchmark.py
~~~

### Hybrid Benchmark

~~~bash
python evaluation/scripts/run_hybrid_benchmark.py
~~~

### Adaptive Benchmark

~~~bash
python evaluation/scripts/run_adaptive_benchmark.py
~~~

### Quality–Cost Benchmark

~~~bash
python evaluation/scripts/run_quality_cost_benchmark.py
~~~

### Generation Regression

~~~bash
python evaluation/scripts/run_generation_regression.py
~~~

### Adaptive Diagnostic

~~~bash
python evaluation/scripts/diagnose_adaptive.py
~~~

---

# 🛠️ Tech Stack

Tech stack được chia theo vai trò thực tế trong project thay vì liệt kê các thư viện không trực tiếp phục vụ hệ thống.

## 🐍 Programming

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)

</p>

## 🤖 Retrieval & AI

<p align="center">

![RAG](https://img.shields.io/badge/RAG-Retrieval--Augmented%20Generation-6366F1)
![BM25](https://img.shields.io/badge/BM25-Sparse%20Retrieval-0EA5E9)
![BGE-M3](https://img.shields.io/badge/BGE--M3-Dense%20Retrieval-2563EB)
![RRF](https://img.shields.io/badge/RRF-Reciprocal%20Rank%20Fusion-14B8A6)
![Reranking](https://img.shields.io/badge/Cross--Encoder-Reranking-8B5CF6)
![Gemini](https://img.shields.io/badge/Gemini-LLM-4285F4?logo=google&logoColor=white)
![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-Embeddings-FF6F00)

</p>

## 📄 Document Processing

<p align="center">

![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF%20Processing-555555)
![pypdf](https://img.shields.io/badge/pypdf-PDF%20Processing-555555)
![Tesseract](https://img.shields.io/badge/Tesseract-Vietnamese%20OCR-5A5A5A)

</p>

## 🌐 Application & Deployment

<p align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?logo=docker&logoColor=white)

</p>

## 🗄️ Database & Vector Search

<p align="center">

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-Vector%20Search-336791)

</p>

## 🧪 Testing & Engineering

<p align="center">

![pytest](https://img.shields.io/badge/pytest-Testing-0A9EDC?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-Linting-D7FF64?logo=ruff&logoColor=black)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?logo=githubactions&logoColor=white)

</p>

---

# 🖥️ Demo

Giao diện Streamlit cung cấp quy trình hỏi đáp pháp luật, hiển thị câu trả lời kèm căn cứ pháp lý và dashboard đánh giá hệ thống.

<p align="center">
  <img src="assets/ui-screenshot.png" alt="Vietnamese Labor Law RAG - Streamlit UI" width="100%">
</p>

<p align="center">
  <em>Giao diện hỏi đáp, hiển thị căn cứ pháp lý và thông tin đánh giá retrieval.</em>
</p>

---

# 🚀 Quick Start

## 1. Clone repository

~~~bash
git clone https://github.com/kimngoc2520/vietnamese-labor-law-rag.git
cd vietnamese-labor-law-rag
~~~

## 2. Cấu hình environment

Python yêu cầu:

`Python >= 3.11`

Tạo file `.env` từ `.env.example`.

### Windows PowerShell

~~~powershell
Copy-Item .env.example .env
~~~

### Linux / macOS

~~~bash
cp .env.example .env
~~~

Sau đó cấu hình các biến môi trường cần thiết.

> **Không commit `.env` hoặc API keys lên GitHub.**

## 3. Chạy bằng Docker — Recommended

Đây là cách được khuyến nghị để chạy toàn bộ hệ thống:

~~~bash
docker compose up -d --build
~~~

Sau khi containers khởi động:

| Service | URL |
|---|---|
| Streamlit | http://localhost:8501 |
| FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

## 4. Local Development

Nếu cần phát triển hoặc debug trực tiếp trên host:

~~~bash
pip install -e ".[dev]"
~~~

Sau đó chạy các thành phần theo hướng dẫn trong [`docs/development.md`](docs/development.md).

---

# 🐳 Docker

Docker Compose khởi động các service chính:

| Service | Port | Role |
|---|---:|---|
| PostgreSQL | 5432 | Database + pgvector |
| FastAPI | 8000 | Backend / RAG API |
| Streamlit | 8501 | User interface |

## Start

~~~bash
docker compose up -d --build
~~~

## Check containers

~~~bash
docker compose ps
~~~

## View API logs

~~~bash
docker compose logs -f api
~~~

## View Streamlit logs

~~~bash
docker compose logs -f ui
~~~

## Stop

~~~bash
docker compose down
~~~

Dockerfile sử dụng **CPU-only PyTorch** nhằm tránh việc Docker image tự kéo CUDA-enabled PyTorch build không cần thiết cho môi trường hiện tại.

---

# 🔌 API

FastAPI backend cung cấp các endpoint chính:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Kiểm tra trạng thái service |
| `/chat` | POST | Hỏi đáp pháp luật bằng RAG |
| `/feedback` | POST | Gửi feedback |
| `/ingest` | POST | Ingest tài liệu |

## POST `/chat`

### Request

~~~json
{
  "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?"
}
~~~

### Response

~~~json
{
  "query": "Người lao động được nghỉ phép năm bao nhiêu ngày?",
  "answer": "...",
  "citations": ["..."],
  "complexity": "Medium",
  "retrieval_budget": 10,
  "retrieved_chunks": []
}
~~~

### Request Flow

**POST `/chat` → Validate Request → Normalize Query → GenerationPipeline → Retrieval → Reranking → Evidence Selection → Generation → ChatResponse**

Chi tiết API được mô tả trong [`docs/api.md`](docs/api.md).

---

# 🧪 Testing

Project sử dụng `pytest`.

Chạy toàn bộ test suite:

~~~bash
python -m pytest tests/unit tests/integration tests/e2e -q
~~~

Kết quả hiện tại:

~~~text
62 passed, 1 warning
~~~

Warning hiện tại đến từ dependency:

~~~text
DeprecationWarning:
anyio.abc.BlockingPortal
~~~

Đây không phải lỗi của project code.

### Lint

~~~bash
ruff check .
~~~

---

# 📁 Project Structure

Repository được tổ chức theo hướng tách biệt giữa application runtime, retrieval, generation, evaluation và testing.

~~~text
vietnamese-labor-law-rag/
│
├── app.py                         # Streamlit frontend
│
├── src/
│   ├── api/                       # FastAPI routes & schemas
│   ├── agent/                     # Workflow orchestration
│   ├── cache/                     # Router & semantic cache
│   ├── common/                    # Shared utilities & types
│   ├── config/                    # Settings, prompts & constants
│   ├── db/                        # PostgreSQL / pgvector
│   ├── generation/                # LLM & generation pipeline
│   ├── ingestion/                 # Document processing & indexing
│   ├── observability/             # Metrics, latency & tracing
│   ├── retrieval/                 # Dense, BM25, hybrid, adaptive & reranking
│   └── verification/              # Evidence & claim verification
│
├── data/
│   ├── raw/                       # Raw source documents
│   ├── processed/                 # Processed documents
│   └── samples/                   # Sample documents
│
├── evaluation/
│   ├── datasets/                  # Evaluation datasets & ground truth
│   ├── reports/                   # Generated evaluation reports
│   └── scripts/                   # Benchmark & regression scripts
│
├── scripts/                       # Utility & ingestion scripts
│
├── tests/
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
│
├── notebooks/                     # Retrieval & model experiments
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── deployment.md
│   ├── development.md
│   ├── evaluation_methodology.md
│   └── diagrams/
│
├── assets/                        # README & project visuals
│
├── infra/
│   ├── docker/                    # Development / production images
│   ├── k8s/                       # Kubernetes configuration
│   └── terraform/                 # Infrastructure configuration
│
├── .github/
│   └── workflows/                 # CI, deployment & evaluation
│
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── pyproject.toml
├── ruff.toml
└── README.md
~~~

## Repository Mapping

| Component | Location | Responsibility |
|---|---|---|
| Streamlit UI | `app.py` | User interface |
| API | `src/api/` | HTTP API |
| Workflow | `src/agent/` | Application orchestration |
| Generation | `src/generation/` | RAG generation pipeline |
| Dense Retrieval | `src/retrieval/dense.py` | BGE-M3 |
| Sparse Retrieval | `src/retrieval/sparse.py` | BM25 |
| Hybrid Retrieval | `src/retrieval/hybrid.py` | Dense + BM25 + RRF |
| Adaptive Retrieval | `src/retrieval/adaptive.py` | Retrieval budget |
| Reranking | `src/retrieval/reranker.py` | Cross-Encoder |
| Verification | `src/verification/` | Evidence & claim verification |
| Database | `src/db/` | PostgreSQL / pgvector |
| Evaluation | `evaluation/` | Benchmark + regression |
| Tests | `tests/` | Unit / integration / E2E |
| Documentation | `docs/` | Technical documentation |
| Images | `assets/` | README / project visuals |
| CI | `.github/workflows/` | Automated CI / evaluation |

---

# ⚙️ Configuration

Các cấu hình nhạy cảm nên được đặt trong `.env`.

Ví dụ:

~~~env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/database
API_BASE_URL=http://localhost:8000
~~~

Các giá trị thực tế không được commit vào repository.

`.env` được giữ local và `.env.example` được dùng làm template.

> **Không chia sẻ API keys hoặc database credentials trong source code, commit hoặc README.**

---

# 🔄 Development Workflow

Development flow của project:

**Implement → Run Tests → Run Ruff → Run Evaluation → Inspect Metrics → Update Pipeline**

## Test

~~~bash
python -m pytest tests/unit tests/integration tests/e2e -q
~~~

## Lint

~~~bash
ruff check .
~~~

## Evaluation

~~~bash
python evaluation/scripts/run_full_evaluation.py
~~~

Các thay đổi liên quan đến retrieval hoặc generation nên được kiểm tra lại bằng evaluation benchmark trước khi commit.

---

# 🤖 CI / Evaluation

GitHub Actions được sử dụng để chạy evaluation pipeline theo lịch và thủ công.

Workflow:

**Checkout Repository → Setup Python 3.11 → Install Dependencies → Run Full Evaluation → Evaluation Reports**

Workflow file:

`.github/workflows/evaluation.yml`

Evaluation có thể được trigger:

- theo schedule;
- manually bằng `workflow_dispatch`.

---

# 🖼️ Documentation Assets

Các visual assets được sử dụng để minh họa những thành phần quan trọng của project.

| Asset | Purpose |
|---|---|
| `hero-banner.png` | Hero image của project |
| `architecture.png` | High-level system architecture |
| `pipeline.png` | End-to-end RAG pipeline |
| `retrieval-pipeline.png` | Dense + BM25 + RRF + reranking |
| `retrieval-strategy-comparison.png` | So sánh retrieval strategies |
| `failure-modes.png` | Diagnostic / failure analysis |
| `ui-screenshot.png` | Streamlit application |

Các hình ảnh này phục vụ **documentation và presentation**, không phải runtime dependency của hệ thống.

---

# ⚠️ Common Issues

Một số lỗi thường gặp khi chạy project được tóm tắt dưới đây. Với hướng dẫn chi tiết hơn, xem thêm [`docs/development.md`](docs/development.md) và [`docs/deployment.md`](docs/deployment.md).

| Vấn đề | Nguyên nhân | Cách khắc phục |
|---|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Chưa cài dependencies hoặc đang sử dụng sai Python environment | Kích hoạt đúng environment rồi chạy `pip install -e .`; hoặc chạy application bằng Docker |
| `Connection refused` khi truy cập API | FastAPI container chưa chạy hoặc API chưa khởi động hoàn tất | Kiểm tra `docker compose ps` và `docker compose logs -f api` |
| Streamlit không kết nối được backend | API chưa chạy hoặc `API_BASE_URL` không đúng | Kiểm tra cấu hình API URL và đảm bảo FastAPI service đang `Up` |
| `GEMINI_API_KEY` / `429` quota error | API key chưa được cấu hình, quota hết hoặc provider giới hạn request | Kiểm tra `.env`, API quota và API logs |
| PostgreSQL connection error | Database container chưa sẵn sàng hoặc `DATABASE_URL` không đúng | Kiểm tra `docker compose ps`, PostgreSQL logs và `DATABASE_URL` |
| Docker chạy code cũ sau khi sửa source | Image/container chưa được rebuild | Chạy `docker compose up -d --build`; nếu cần dùng `docker compose build --no-cache` |

> Xem thêm tại [`docs/development.md`](docs/development.md) và [`docs/deployment.md`](docs/deployment.md).

---

# 📌 Limitations

Project hiện vẫn là **research / engineering prototype**, chưa phải production legal service.

Một số giới hạn hiện tại:

1. Corpus còn giới hạn về số lượng văn bản.
2. Complexity classifier hiện tại là rule-based.
3. Adaptive-K chưa sử dụng learned policy.
4. Generation phụ thuộc vào external LLM provider.
5. LLM response có thể gặp lỗi provider, quota hoặc network.
6. Evaluation dataset hiện tại còn tương đối nhỏ.
7. Retrieval quality không đồng nghĩa với factual/legal correctness tuyệt đối.
8. Hệ thống chưa thay thế quá trình review pháp lý bởi chuyên gia.

---

# ⚖️ Disclaimer

> **Vietnamese Labor Law RAG là công cụ hỗ trợ tra cứu và nghiên cứu thông tin pháp luật bằng AI.**
>
> Câu trả lời được tạo dựa trên các tài liệu được hệ thống truy xuất và không đảm bảo hoàn toàn chính xác hoặc đầy đủ trong mọi trường hợp.
>
> Hệ thống **không phải là dịch vụ tư vấn pháp lý** và không thể thay thế việc tham vấn luật sư hoặc chuyên gia pháp luật.
>
> Đối với các quyết định có ý nghĩa pháp lý thực tế, cần kiểm tra lại văn bản pháp luật chính thức và tham khảo chuyên gia có thẩm quyền.

---

# 📚 Documentation

Các tài liệu kỹ thuật liên quan:

| Document | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Kiến trúc hệ thống |
| [`docs/api.md`](docs/api.md) | API documentation |
| [`docs/deployment.md`](docs/deployment.md) | Deployment guide |
| [`docs/development.md`](docs/development.md) | Development guide |
| [`docs/evaluation_methodology.md`](docs/evaluation_methodology.md) | Evaluation methodology |
| [`docs/diagrams/`](docs/diagrams/) | Technical diagrams |

---
