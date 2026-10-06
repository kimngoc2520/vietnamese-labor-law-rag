# Sample Data

Thư mục `data/samples/` chứa dữ liệu mẫu được sử dụng cho development, testing và kiểm tra nhanh của **Vietnamese Labor Law RAG**.

## 1. Purpose

Sample data phục vụ các mục đích:

- Kiểm tra ingestion pipeline.
- Kiểm tra retrieval.
- Phát triển và debug local.
- Tạo dữ liệu nhỏ để test workflow.
- Hỗ trợ reproducible development environment.

Sample data không đại diện cho toàn bộ corpus pháp luật được sử dụng trong evaluation.

---

## 2. Directory

Cấu trúc:

    data/
    └── samples/
        └── README.md

Các sample files có thể được bổ sung hoặc thay đổi trong quá trình phát triển project.

---

## 3. Data Flow

Sample documents đi qua ingestion pipeline:

    Sample Documents
          ↓
    Document Loading
          ↓
    Text Extraction
          ↓
    Cleaning / Normalization
          ↓
    Chunking
          ↓
    Embedding
          ↓
    Database
          ↓
    Retrieval

Sau khi ingestion, dữ liệu có thể được sử dụng để kiểm tra retrieval và RAG pipeline.

---

## 4. Supported Document Sources

Project tập trung vào tài liệu pháp luật Việt Nam.

Các document source có thể bao gồm:

- Bộ luật.
- Luật.
- Nghị định.
- Thông tư.
- Văn bản pháp luật liên quan đến lao động.

Sample data nên giữ cấu trúc gần với dữ liệu thực tế để giúp phát hiện các vấn đề trong document processing.

---

## 5. Document Processing

Một document được xử lý qua các bước chính:

    Document
       ↓
    Text Extraction
       ↓
    Normalization
       ↓
    Chunking
       ↓
    Metadata
       ↓
    Embedding
       ↓
    Indexing

Metadata có thể được sử dụng để truy xuất nguồn evidence và tạo citation trong answer.

---

## 6. Chunking

Documents được chia thành các chunks trước khi indexing.

Chunking giúp:

- Giảm kích thước context mỗi retrieval result.
- Tăng khả năng tìm đúng đoạn liên quan.
- Hỗ trợ dense retrieval.
- Hỗ trợ BM25 retrieval.
- Cung cấp evidence cụ thể cho reranker và generation.

Chunking strategy cần được giữ nhất quán giữa ingestion và evaluation để kết quả benchmark có ý nghĩa.

---

## 7. Metadata

Metadata của document/chunk có vai trò quan trọng trong legal RAG.

Các thông tin có thể được sử dụng gồm:

| Metadata | Purpose |
|---|---|
| Document identifier | Xác định văn bản |
| Document title | Hiển thị nguồn |
| Chunk identifier | Xác định evidence |
| Section / article | Xác định vị trí pháp lý |
| Source information | Tạo citation |

Cấu trúc metadata thực tế phụ thuộc vào ingestion implementation.

---

## 8. Sample Data vs Evaluation Data

Sample data và evaluation data có mục đích khác nhau.

| Data | Purpose |
|---|---|
| Sample data | Development và smoke testing |
| Evaluation data | Benchmark retrieval và generation |
| Ground truth | Reference để đánh giá retrieval |

Không nên sử dụng sample data để thay thế evaluation dataset khi báo cáo performance.

---

## 9. Adding New Sample Documents

Khi thêm document mẫu:

1. Đặt document vào thư mục sample phù hợp.
2. Kiểm tra file có thể đọc được.
3. Chạy ingestion pipeline.
4. Kiểm tra số lượng chunks.
5. Kiểm tra metadata.
6. Kiểm tra retrieval.
7. Chạy relevant tests.

Sau khi ingestion, nên kiểm tra một số query thủ công để đảm bảo evidence được retrieve đúng.

---

## 10. Data Quality Checks

Trước khi sử dụng sample document, nên kiểm tra:

- Document có đọc được hay không.
- Text extraction có đầy đủ hay không.
- Encoding có chính xác hay không.
- Các section/article có bị mất hay không.
- Chunk có bị quá ngắn hoặc quá dài hay không.
- Metadata có đầy đủ hay không.
- Citation có thể truy ngược về source hay không.

Đối với tài liệu PDF scan, OCR có thể được sử dụng trong ingestion pipeline.

---

## 11. Legal Data Considerations

Dữ liệu pháp luật có tính chất đặc thù.

Khi thêm hoặc cập nhật document cần chú ý:

- Tên văn bản.
- Số hiệu văn bản.
- Ngày ban hành.
- Ngày có hiệu lực.
- Điều khoản liên quan.
- Phiên bản văn bản.
- Nguồn tài liệu.

Không nên coi sample document là nguồn pháp lý duy nhất cho quyết định thực tế.

---

## 12. Reproducibility

Khi sử dụng sample data để debug hoặc benchmark nội bộ, nên ghi lại:

- Document version.
- Processing configuration.
- Chunking configuration.
- Embedding model.
- Retrieval configuration.
- Reranker configuration.

Điều này giúp so sánh kết quả giữa các lần chạy.

---

## 13. Development Usage

Sample data phù hợp cho các tác vụ nhanh như:

- Kiểm tra ingestion.
- Kiểm tra database indexing.
- Kiểm tra dense retrieval.
- Kiểm tra BM25.
- Kiểm tra hybrid retrieval.
- Kiểm tra reranking.
- Kiểm tra citation generation.

Các benchmark chính vẫn nên sử dụng evaluation dataset được định nghĩa trong evaluation pipeline.

---

## 14. Related Components

Sample data liên quan trực tiếp đến:

| Component | Role |
|---|---|
| Ingestion | Đọc và xử lý document |
| Chunking | Chia document thành chunks |
| Embedding | Tạo dense representation |
| BM25 | Sparse retrieval |
| pgvector | Lưu và tìm dense vectors |
| Reranker | Xếp hạng lại evidence |
| Generation | Sử dụng evidence để tạo answer |

Chi tiết architecture:

    docs/architecture.md

Chi tiết development:

    docs/development.md

---

## 15. Data Privacy and Repository Hygiene

Không đưa vào repository:

- API keys.
- Database credentials.
- Personal information không cần thiết.
- Private documents.
- Sensitive internal data.

Environment-specific secrets phải được lưu trong `.env` và không được commit.

---

## 16. Summary

`data/samples/` cung cấp dữ liệu nhỏ phục vụ development và testing của Vietnamese Labor Law RAG.

Sample data giúp kiểm tra nhanh toàn bộ data flow:

    Document
      ↓
    Ingestion
      ↓
    Chunking
      ↓
    Embedding / Indexing
      ↓
    Retrieval
      ↓
    Reranking
      ↓
    Generation

Sample data hỗ trợ development nhưng không thay thế evaluation dataset hoặc ground truth dùng để đánh giá hệ thống.