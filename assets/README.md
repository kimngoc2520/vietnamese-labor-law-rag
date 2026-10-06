# Assets

Thư mục `assets/` chứa các tài nguyên trực quan được sử dụng cho documentation và presentation của **Vietnamese Labor Law RAG**.

## 1. Purpose

Assets được tách khỏi source code để quản lý các tài nguyên như:

- Architecture diagrams.
- Pipeline diagrams.
- UI screenshots.
- Evaluation visualizations.
- Các hình ảnh minh họa cho README và documentation.

Các assets không chứa application logic.

---

## 2. Directory

Cấu trúc hiện tại:

    assets/
    └── README.md

Các tài nguyên trực quan có thể được bổ sung trong quá trình hoàn thiện documentation.

---

## 3. Asset Categories

| Category | Purpose |
|---|---|
| Architecture | Minh họa system architecture |
| Pipeline | Minh họa RAG workflow |
| UI | Screenshot của Streamlit application |
| Evaluation | Visualization của benchmark results |
| Documentation | Hình ảnh hỗ trợ README và docs |

---

## 4. Architecture Diagrams

Architecture diagrams dùng để minh họa các thành phần và luồng xử lý chính của hệ thống.

Pipeline tổng quát:

    User Query
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

Chi tiết implementation được mô tả trong:

    docs/architecture.md

---

## 5. UI Screenshots

UI screenshots có thể được sử dụng trong:

- Root `README.md`.
- Project presentation.
- Documentation.
- Demo section.

Các screenshot nên thể hiện rõ:

- Query input.
- Generated answer.
- Evidence / citations.
- Retrieval information.
- Evaluation metrics.

Không đưa thông tin nhạy cảm hoặc API credentials vào screenshot.

---

## 6. Evaluation Visualizations

Evaluation visualizations có thể được sử dụng để minh họa:

- Retrieval performance.
- MRR.
- Hit@K.
- Adaptive-K distribution.
- Quality–cost trade-off.
- Generation success rate.

Các visualization phải phản ánh đúng evaluation results hiện tại.

Không nên tạo visualization từ số liệu chưa được benchmark hoặc không có nguồn rõ ràng.

---

## 7. Naming Convention

Tên asset nên:

- Dùng lowercase.
- Dùng `-` để phân tách từ.
- Mô tả rõ nội dung.
- Tránh tên chung như `image1.png` hoặc `final.png`.

Ví dụ:

    architecture-overview.png
    retrieval-pipeline.png
    adaptive-k-results.png
    quality-cost-comparison.png
    streamlit-ui.png

---

## 8. Image Formats

Ưu tiên:

| Format | Use case |
|---|---|
| PNG | Diagrams, screenshots |
| SVG | Vector diagrams |
| WebP | Web-oriented images |

Không nên lưu các file ảnh có kích thước quá lớn nếu không cần thiết.

---

## 9. Mermaid Diagrams

Đối với các architecture diagrams đơn giản, có thể ưu tiên Mermaid trực tiếp trong Markdown thay vì tạo thêm image file.

Ví dụ:

    ```mermaid
    flowchart LR
        A[User Query] --> B[Complexity Classification]
        B --> C[Adaptive Retrieval]
        C --> D[Dense + BM25]
        D --> E[RRF]
        E --> F[Cross-Encoder Reranking]
        F --> G[Evidence Selection]
        G --> H[LLM Generation]
        H --> I[Answer + Citations]
    ```

Mermaid phù hợp với các diagram cần dễ chỉnh sửa và version control.

---

## 10. Documentation Usage

Assets có thể được tham chiếu từ:

- `README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/deployment.md`
- `docs/evaluation_methodology.md`

Khi thêm asset mới, nên cập nhật tài liệu liên quan để tránh file không được sử dụng.

---

## 11. Version Control

Assets được quản lý cùng repository để documentation có thể được reproduce.

Khi thay đổi asset:

1. Kiểm tra nội dung.
2. Kiểm tra kích thước file.
3. Kiểm tra đường dẫn reference.
4. Kiểm tra Markdown rendering.
5. Commit cùng documentation change nếu phù hợp.

---

## 12. What Should Not Be Stored

Không lưu trong `assets/`:

- API keys.
- Database credentials.
- `.env`.
- Private documents.
- Raw user data.
- Temporary debug files.
- Build artifacts.
- Model checkpoints lớn.

Assets chỉ nên chứa tài nguyên cần thiết cho project presentation và documentation.

---

## 13. Current Status

Hiện tại thư mục `assets/` chủ yếu đóng vai trò placeholder cho các tài nguyên trực quan sẽ được bổ sung khi documentation và project presentation được hoàn thiện.

Architecture có thể được biểu diễn trực tiếp bằng Mermaid trong Markdown, vì vậy không bắt buộc phải tạo image cho mọi diagram.

---

## 14. Related Documentation

| Document | Nội dung |
|---|---|
| `README.md` | Project overview |
| `docs/architecture.md` | System architecture |
| `docs/evaluation_methodology.md` | Evaluation methodology |
| `docs/development.md` | Development workflow |
| `evaluation/reports/` | Evaluation results |

---

## 15. Summary

`assets/` là nơi quản lý các tài nguyên trực quan phục vụ documentation và presentation của Vietnamese Labor Law RAG.

Nguyên tắc chính:

    Source Code
        → src/

    Tests
        → tests/

    Evaluation
        → evaluation/

    Documentation
        → docs/

    Documentation Assets
        → assets/

Assets nên nhỏ gọn, có tên rõ ràng, được version control và luôn phản ánh đúng trạng thái hiện tại của project.