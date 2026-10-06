# Kiến trúc hệ thống

Vietnamese Labor Law RAG là hệ thống Retrieval-Augmented Generation (RAG) được xây dựng để trả lời câu hỏi trên tập tài liệu pháp luật lao động Việt Nam.

Hệ thống kết hợp **Hybrid Retrieval**, **Adaptive Retrieval**, **Reciprocal Rank Fusion (RRF)**, **Cross-Encoder Reranking**, **Subject-aware Adjustment**, **Evidence Selection** và **LLM Generation** nhằm cải thiện chất lượng truy xuất và khả năng trả lời dựa trên bằng chứng pháp lý.

---

## 1. Tổng quan kiến trúc

~~~mermaid
flowchart TD
    A[Người dùng] --> B[Streamlit UI]
    B --> C[FastAPI]
    C --> D[Phân loại độ phức tạp]

    D --> E[Adaptive Retrieval Budget]

    E --> F[Dense Retrieval<br/>BGE-M3]
    E --> G[Sparse Retrieval<br/>BM25]

    F --> H[RRF Fusion<br/>RRF_K = 60]
    G --> H

    H --> I[Tập ứng viên]
    I --> J[Cross-Encoder Reranking]
    J --> K[Subject-aware Adjustment]
    K --> L[Top-5 Evidence]

    L --> M[Generation Prompt]
    M --> N[Gemini / OpenAI]
    N --> O[Câu trả lời]

    O --> P[Evidence Selection]
    P --> Q[Citations]
~~~

Kiến trúc được tổ chức thành các lớp chính:

| Lớp | Trách nhiệm | Thành phần |
|---|---|---|
| Giao diện | Nhận câu hỏi và hiển thị kết quả | Streamlit |
| API | Tiếp nhận và xử lý request/response | FastAPI |
| Ứng dụng | Điều phối RAG pipeline | Generation Pipeline |
| Truy xuất | Tìm kiếm và hợp nhất ứng viên | BGE-M3, BM25, RRF |
| Xếp hạng | Tinh chỉnh mức độ liên quan | Cross-Encoder |
| Bằng chứng | Chọn evidence và citation | Verification |
| Sinh câu trả lời | Tạo câu trả lời từ context | Gemini / OpenAI |
| Dữ liệu | Lưu trữ tài liệu và vector | PostgreSQL + pgvector |
| Đánh giá | Đo chất lượng hệ thống | Evaluation scripts |
| Kiểm thử | Kiểm tra tự động | pytest |
| Triển khai | Chạy hệ thống trong container | Docker Compose |

---

## 2. Luồng xử lý end-to-end

Một câu hỏi của người dùng đi qua các bước:

1. Người dùng nhập câu hỏi trên Streamlit.
2. Streamlit gửi request đến FastAPI.
3. Hệ thống chuẩn hóa và kiểm tra câu hỏi.
4. Bộ phân loại rule-based xác định độ phức tạp.
5. Hệ thống chọn ngân sách retrieval tương ứng.
6. Dense Retrieval và BM25 thực hiện truy xuất.
7. Hai bảng xếp hạng được hợp nhất bằng RRF.
8. Candidate Pool được đưa qua Cross-Encoder Reranking.
9. Subject-aware Adjustment điều chỉnh thứ hạng theo chủ thể pháp lý.
10. Hệ thống chọn Top-5 evidence.
11. Generation Prompt được xây dựng từ `SYSTEM_PROMPT`, câu hỏi và context đã chọn.
12. Gemini hoặc OpenAI tạo câu trả lời.
13. Verification layer thực hiện Evidence Selection.
14. Hệ thống xây dựng citations và trả kết quả về giao diện.

---

## 3. Phân loại độ phức tạp câu hỏi

Hệ thống sử dụng **bộ phân loại dựa trên luật (rule-based)** thay vì mô hình Machine Learning.

Việc phân loại dựa trên:

- Độ dài câu hỏi
- Số lượng điều kiện hoặc mệnh đề
- Phạm vi pháp lý
- Số lượng yêu cầu hoặc ràng buộc

| Mức độ | Ngân sách retrieval |
|---|---:|
| Simple | 5 |
| Medium | 10 |
| Complex | 20 |

Đây là một baseline nhẹ để điều chỉnh chi phí retrieval mà không cần huấn luyện thêm mô hình.

---

## 4. Adaptive Retrieval

Sau khi xác định độ phức tạp, hệ thống chọn `K` cho Dense Retrieval và BM25.

~~~mermaid
flowchart LR
    A[Câu hỏi] --> B[Phân loại độ phức tạp]
    B --> C{Mức độ}

    C -->|Simple| D[K = 5]
    C -->|Medium| E[K = 10]
    C -->|Complex| F[K = 20]

    D --> G[Dense + BM25]
    E --> G
    F --> G
~~~

Việc sử dụng ngân sách thích ứng giúp các câu hỏi đơn giản không phải sử dụng cùng lượng ứng viên như những câu hỏi phức tạp.

---

## 5. Hybrid Retrieval

Hybrid Retrieval kết hợp Dense Retrieval và Sparse Retrieval.

| Thành phần | Vai trò |
|---|---|
| Dense Retrieval | Tìm kiếm dựa trên tương đồng ngữ nghĩa |
| BM25 | Tìm kiếm dựa trên từ khóa |
| RRF | Hợp nhất hai bảng xếp hạng |

~~~mermaid
flowchart LR
    A[Câu hỏi] --> B[Dense Retrieval<br/>BGE-M3]
    A --> C[BM25]

    B --> D[RRF Fusion]
    C --> D

    D --> E[Tập ứng viên]
~~~

Dense Retrieval phù hợp với các trường hợp khác nhau về cách diễn đạt nhưng tương đồng về ý nghĩa, trong khi BM25 giúp khai thác các thuật ngữ và cụm từ pháp lý cụ thể.

---

## 6. RRF Fusion

Hệ thống sử dụng **Reciprocal Rank Fusion (RRF)** để hợp nhất kết quả từ Dense Retrieval và BM25.

~~~text
RRF_K = 60
~~~

~~~mermaid
flowchart LR
    A[Dense Ranking] --> C[RRF<br/>K = 60]
    B[BM25 Ranking] --> C
    C --> D[Bảng xếp hạng hợp nhất]
~~~

RRF tạo ra một thứ hạng chung dựa trên vị trí của ứng viên trong hai nguồn retrieval.

Kết quả sau RRF được sử dụng làm Candidate Pool cho Cross-Encoder Reranking.

---

## 7. Candidate Pool và Cross-Encoder Reranking

Candidate Pool chứa các chunk được truy xuất từ cả Dense Retrieval và BM25.

Các ứng viên này tiếp tục được đánh giá bằng Cross-Encoder:

~~~text
BGE-reranker-v2-m3
~~~

Cross-Encoder đánh giá trực tiếp mối quan hệ giữa query và từng ứng viên để tạo ra thứ hạng chính xác hơn.

Sau reranking:

~~~text
final_top_k = 5
~~~

Chỉ các ứng viên có thứ hạng cao nhất tiếp tục được xử lý.

---

## 8. Subject-aware Adjustment

Sau Cross-Encoder Reranking, hệ thống áp dụng **Subject-aware Adjustment** thông qua `_apply_subject_boost`.

Bước này xem xét chủ thể pháp lý được đề cập trong câu hỏi, chẳng hạn:

- Người lao động
- Người sử dụng lao động
- Các chủ thể pháp lý khác

~~~mermaid
flowchart LR
    A[Kết quả Reranking] --> B[Xác định Subject]
    B --> C[Subject-aware Adjustment]
    C --> D[Thứ hạng cuối]
~~~

Bước điều chỉnh này giúp phân biệt các ứng viên có mức độ liên quan ngữ nghĩa tương tự nhưng khác nhau về chủ thể hoặc góc nhìn pháp lý.

---

## 9. Retrieval Pipeline hoàn chỉnh

Thứ tự xử lý của retrieval pipeline là:

~~~mermaid
flowchart TD
    A[Câu hỏi] --> B[Phân loại độ phức tạp]
    B --> C[Adaptive K]

    C --> D[Dense Retrieval]
    C --> E[BM25]

    D --> F[RRF<br/>K = 60]
    E --> F

    F --> G[Candidate Pool]
    G --> H[Cross-Encoder Reranking]
    H --> I[Subject-aware Adjustment]
    I --> J[Top-5 Evidence]
~~~

Điểm quan trọng là **Adaptive K được xác định trước Dense Retrieval và BM25**, sau đó kết quả mới được hợp nhất bằng RRF và đưa qua Cross-Encoder.

---

## 10. Generation Layer

Generation Layer chuyển evidence đã chọn thành câu trả lời tự nhiên.

**Gemini** là LLM mặc định. **OpenAI** có thể được cấu hình làm provider thay thế.

Generation Prompt được xây dựng từ:

~~~text
SYSTEM_PROMPT
+
Selected Legal Context
+
User Query
~~~

~~~mermaid
flowchart LR
    A[System Prompt] --> D[Generation Prompt]
    B[Selected Legal Context] --> D
    C[User Query] --> D

    D --> E[Gemini / OpenAI]
    E --> F[Câu trả lời]
~~~

LLM chỉ nhận context đã được lựa chọn thay vì toàn bộ Candidate Pool.

---

## 11. Verification và Evidence Selection

Generation và citation được xử lý thành các bước riêng biệt.

Sau khi câu trả lời được tạo, verification layer thực hiện **Evidence Selection** để xác định các đoạn evidence hỗ trợ.

Logic này nằm tại:

~~~text
src/verification/evidence.py
~~~

với hàm:

~~~text
select_evidence(...)
~~~

~~~mermaid
flowchart LR
    A[Câu trả lời] --> C[Evidence Selection]
    B[Retrieved Evidence] --> C
    C --> D[Evidence hỗ trợ]
    D --> E[Citations]
~~~

Việc tách Evidence Selection khỏi Generation giúp logic citation có thể được cải thiện độc lập với LLM.

---

## 12. Data Layer

Data Layer chịu trách nhiệm lưu trữ corpus pháp luật và dữ liệu phục vụ retrieval.

| Thành phần | Vai trò |
|---|---|
| PostgreSQL | Lưu trữ dữ liệu |
| pgvector | Lưu trữ và truy xuất vector |
| Document chunks | Đơn vị dữ liệu được truy xuất |
| Embeddings | Biểu diễn cho Dense Retrieval |

Retrieval hoạt động trên các chunk thay vì đưa toàn bộ tài liệu vào mỗi request.

---

## 13. Document Ingestion

Tài liệu pháp luật được xử lý trước khi đưa vào retrieval pipeline.

Quy trình khái quát:

~~~mermaid
flowchart LR
    A[Tài liệu pháp luật] --> B[Xử lý tài liệu]
    B --> C[Chia chunk]
    C --> D[Tạo embedding]
    D --> E[Corpus đã lập chỉ mục]
    E --> F[Retrieval]
~~~

Việc tách ingestion khỏi query-time retrieval giúp quá trình lập chỉ mục không phải thực hiện lại cho mỗi câu hỏi.

---

## 14. Evaluation Layer

Evaluation được tách khỏi serving pipeline để đánh giá từng thành phần của hệ thống.

| Nhóm đánh giá | Nội dung |
|---|---|
| Retrieval Benchmark | Đánh giá Dense Retrieval |
| Hybrid Benchmark | Đánh giá Hybrid Retrieval |
| Adaptive Benchmark | Đánh giá Adaptive-K |
| Quality-Cost Benchmark | Đánh giá trade-off chất lượng và ngân sách |
| Generation Regression | Kiểm tra độ ổn định của generation |

~~~mermaid
flowchart TD
    A[Bộ dữ liệu đánh giá] --> B[Retrieval Benchmarks]
    A --> C[Generation Regression]

    B --> D[Báo cáo đánh giá]
    C --> D

    D --> E[Phân tích hệ thống]
~~~

Cách tổ chức này cho phép đánh giá retrieval và generation độc lập.

---

## 15. Kiến trúc triển khai

Hệ thống được triển khai local bằng Docker Compose.

~~~mermaid
flowchart TB
    U[Trình duyệt]

    U --> S[Streamlit<br/>Port 8501]
    S --> A[FastAPI<br/>Port 8000]

    A --> R[RAG Pipeline]
    R --> D[PostgreSQL + pgvector]
    R --> L[Gemini / OpenAI]
~~~

| Thành phần | Trách nhiệm |
|---|---|
| Streamlit | Giao diện người dùng |
| FastAPI | Backend API |
| PostgreSQL | Lưu trữ dữ liệu |
| pgvector | Vector retrieval |
| RAG Pipeline | Retrieval, reranking, evidence và generation |
| Gemini / OpenAI | Sinh câu trả lời |

---

## 16. Ánh xạ kiến trúc với mã nguồn

| Thành phần | Vị trí |
|---|---|
| Agent / Workflow | `src/agent/` |
| API | `src/api/` |
| Retrieval | `src/retrieval/` |
| Generation | `src/generation/` |
| Verification | `src/verification/` |
| Database | `src/db/` |
| Configuration | `src/config/` |
| Evaluation | `evaluation/scripts/` |
| Evaluation Reports | `evaluation/reports/` |
| Tests | `tests/` |
| Streamlit UI | `app.py` |
| Docker | `Dockerfile`, `docker-compose.yml` |

---

## 17. Nguyên tắc thiết kế

### Tách biệt Retrieval và Generation

Chất lượng retrieval được đánh giá độc lập với generation để xác định rõ vấn đề nằm ở bước truy xuất hay bước sinh câu trả lời.

### Retrieval thích ứng

Ngân sách retrieval được điều chỉnh theo độ phức tạp của câu hỏi thay vì sử dụng một giá trị cố định.

### Kết hợp Dense và Sparse Retrieval

Dense Retrieval khai thác tương đồng ngữ nghĩa, trong khi BM25 tận dụng tín hiệu từ khóa. Hai nguồn được hợp nhất bằng RRF.

### Reranking sau Candidate Retrieval

Cross-Encoder được áp dụng sau retrieval và RRF để tập trung chi phí tính toán vào Candidate Pool đã được thu hẹp.

### Điều chỉnh theo chủ thể pháp lý

Subject-aware Adjustment giúp phân biệt các ứng viên có mức độ liên quan ngữ nghĩa tương tự nhưng khác nhau về chủ thể pháp lý.

### Generation dựa trên Evidence

LLM nhận context đã được lựa chọn thay vì toàn bộ Candidate Pool.

### Citation tách khỏi Generation

Evidence Selection được thực hiện riêng để xác định evidence hỗ trợ và xây dựng citations.

### LLM có thể cấu hình

Gemini là provider mặc định, trong khi OpenAI có thể được cấu hình làm provider thay thế.

---

## 18. Tóm tắt kiến trúc

Toàn bộ pipeline:

~~~mermaid
flowchart TD
    A[Câu hỏi người dùng]
    B[Rule-based Complexity Classifier]
    C[Adaptive Retrieval Budget]
    D[Dense + BM25 Retrieval]
    E[RRF Fusion<br/>K = 60]
    F[Candidate Pool]
    G[Cross-Encoder Reranking<br/>Top-5]
    H[Subject-aware Adjustment]
    I[Legal Evidence]
    J[Generation Prompt]
    K[Gemini / OpenAI]
    L[Câu trả lời]
    M[Verification / Evidence Selection]
    N[Citations]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    I --> M
    M --> N
~~~

| Giai đoạn | Thành phần chính | Kết quả |
|---|---|---|
| Truy xuất | Dense + BM25 + RRF | Candidate Pool |
| Xếp hạng | Cross-Encoder + Subject-aware Adjustment | Evidence được xếp hạng |
| Sinh câu trả lời | Generation Prompt + Gemini/OpenAI | Câu trả lời |
| Kiểm chứng | Evidence Selection | Evidence hỗ trợ và citations |

---

## 19. Lưu ý

Hệ thống được xây dựng cho mục đích nghiên cứu và trình diễn kỹ thuật. Kết quả từ hệ thống không thay thế cho tư vấn pháp lý chuyên nghiệp hoặc cách giải thích chính thức của cơ quan có thẩm quyền.