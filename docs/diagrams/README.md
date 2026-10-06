# Diagrams

Thư mục `docs/diagrams/` chứa các sơ đồ trực quan mô tả architecture và workflow của **Vietnamese Labor Law RAG**.

Các diagram được dùng để hỗ trợ việc đọc architecture, presentation và technical documentation.

## 1. Purpose

Diagram giúp mô tả trực quan:

- System architecture.
- RAG pipeline.
- Retrieval flow.
- Adaptive-K workflow.
- Generation flow.
- Evaluation workflow.

Các diagram không chứa application logic và không được sử dụng trực tiếp trong runtime.

---

## 2. Directory

Cấu trúc:

    docs/
    └── diagrams/
        ├── README.md
        └── .gitkeep

Các diagram có thể được bổ sung trong quá trình hoàn thiện documentation.

---

## 3. Recommended Diagrams

Project có thể sử dụng các diagram chính sau:

| Diagram | Nội dung |
|---|---|
| System Architecture | Tổng quan toàn bộ hệ thống |
| RAG Pipeline | Luồng xử lý query |
| Retrieval Pipeline | Dense + BM25 + RRF + reranking |
| Adaptive Retrieval | Complexity → Adaptive-K |
| Generation Flow | Evidence → LLM → Answer |
| Evaluation Pipeline | Benchmark và regression workflow |

---

## 4. System Architecture

Architecture tổng quát:

    User
      ↓
    Streamlit UI
      ↓
    FastAPI
      ↓
    RAG Pipeline
      ↓
    Retrieval
      ↓
    Reranking
      ↓
    Evidence Selection
      ↓
    LLM
      ↓
    Answer + Citations

Chi tiết được mô tả trong:

    docs/architecture.md

---

## 5. RAG Pipeline

Pipeline chính:

    Query
      ↓
    Complexity Classification
      ↓
    Adaptive Top-K
      ↓
    Dense Retrieval + BM25
      ↓
    RRF Fusion
      ↓
    Cross-Encoder Reranking
      ↓
    Subject-aware Adjustment
      ↓
    Evidence Selection
      ↓
    Generation
      ↓
    Answer + Citations

Adaptive Top-K được áp dụng trước RRF theo architecture hiện tại.

---

## 6. Retrieval Pipeline

Retrieval layer gồm hai nhánh:

    Query
      ├───────────────┐
      ↓               ↓
    Dense            BM25
    BGE-M3           Sparse
      │               │
      └───────┬───────┘
              ↓
             RRF
              ↓
       Candidate Pool
              ↓
      Cross-Encoder
        Reranking
              ↓
          Top-K Evidence

RRF sử dụng:

    RRF_K = 60

---

## 7. Adaptive Retrieval

Adaptive retrieval sử dụng complexity classifier để lựa chọn retrieval budget.

    Query
      ↓
    Complexity Classifier
      ↓
    ┌─────────┬─────────┬─────────┐
    │ Simple  │ Medium  │ Complex │
    │   K=5   │  K=10   │  K=20   │
    └─────────┴─────────┴─────────┘

Complexity classifier hiện tại là rule-based.

Các yếu tố được sử dụng gồm:

- Query length.
- Number of conditions.
- Legal scope.
- Query complexity.

Đây chưa phải machine-learning classifier.

---

## 8. Generation Flow

Sau retrieval và reranking, evidence phù hợp được đưa vào generation pipeline.

    Selected Evidence
          ↓
    Context Construction
          ↓
    System Prompt
          +
    Selected Context
          ↓
    LLM
          ↓
    Generated Answer
          ↓
    Evidence Selection
          ↓
    Citations

Gemini là LLM mặc định trong configuration hiện tại.

OpenAI có thể được sử dụng thông qua configuration tương ứng.

---

## 9. Evaluation Pipeline

Evaluation workflow:

    Evaluation Dataset
          ↓
    Ground Truth
          ↓
    Retrieval Benchmark
          ↓
    Hybrid Benchmark
          ↓
    Adaptive-K Benchmark
          ↓
    Quality–Cost Benchmark
          ↓
    Generation Regression
          ↓
    Reports

Chi tiết:

    docs/evaluation_methodology.md

---

## 10. Diagram Formats

Có thể sử dụng:

- Mermaid.
- PNG.
- SVG.

Ưu tiên Mermaid cho các diagram architecture đơn giản vì:

- Dễ chỉnh sửa.
- Dễ version control.
- Không cần lưu thêm binary image.
- GitHub hỗ trợ render Mermaid trong Markdown.

PNG hoặc SVG phù hợp khi cần diagram được thiết kế trực quan cho presentation hoặc README.

---

## 11. Naming Convention

Tên file nên mô tả rõ nội dung.

Ví dụ:

    system-architecture.mmd
    rag-pipeline.mmd
    retrieval-pipeline.mmd
    adaptive-retrieval.mmd
    generation-flow.mmd
    evaluation-pipeline.mmd

Nếu sử dụng exported images:

    system-architecture.png
    rag-pipeline.png
    retrieval-pipeline.png

Tránh các tên như:

    diagram1.png
    final.png
    new-diagram.png

---

## 12. Diagram Guidelines

Một diagram nên:

- Có một mục đích rõ ràng.
- Không chứa quá nhiều implementation detail.
- Sử dụng terminology nhất quán với source code.
- Thể hiện đúng thứ tự xử lý.
- Không mô tả component chưa tồn tại như một phần của production pipeline.

Khi architecture thay đổi, diagram liên quan cũng cần được cập nhật.

---

## 13. Documentation Usage

Các diagram có thể được sử dụng trong:

- `README.md`
- `docs/architecture.md`
- `docs/evaluation_methodology.md`
- Project presentation.

Không bắt buộc mọi diagram phải được embed vào tất cả các tài liệu.

Mỗi tài liệu chỉ nên sử dụng diagram thực sự cần thiết để tránh lặp thông tin.

---

## 14. Current Status

Hiện tại thư mục chứa placeholder:

    .gitkeep
    README.md

Các architecture diagram có thể được biểu diễn trực tiếp bằng Mermaid trong documentation trước khi export thành image.

Việc bổ sung image chỉ cần thiết khi diagram cần được sử dụng trong README, presentation hoặc các tài liệu yêu cầu visual asset riêng.

---

## 15. Related Documentation

| Document | Nội dung |
|---|---|
| `docs/architecture.md` | System architecture |
| `docs/api.md` | API architecture |
| `docs/evaluation_methodology.md` | Evaluation workflow |
| `docs/development.md` | Development workflow |
| `assets/README.md` | Documentation assets |

---

## 16. Summary

`docs/diagrams/` là nơi quản lý các sơ đồ phục vụ documentation của project.

Nguyên tắc:

    Architecture
        ↓
    Diagram
        ↓
    Documentation

Diagram phải phản ánh đúng architecture hiện tại và được cập nhật cùng source/documentation khi workflow thay đổi.