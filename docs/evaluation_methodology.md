# Evaluation Methodology

Tài liệu này mô tả phương pháp đánh giá của **Vietnamese Labor Law RAG**.

Evaluation được thiết kế theo hướng đánh giá từng thành phần của hệ thống thay vì chỉ đo chất lượng câu trả lời cuối cùng. Các nhóm đánh giá chính gồm:

- Retrieval Quality
- Hybrid Retrieval
- Adaptive Retrieval
- Quality–Cost Trade-off
- Generation Reliability
- Automated Testing

> **Evaluation scope:** Các kết quả hiện tại được đo trên tập benchmark 30 query và phản ánh cấu hình hiện tại của hệ thống. Các kết quả này chưa đại diện cho toàn bộ các câu hỏi pháp luật lao động Việt Nam.

---

## 1. Evaluation Pipeline

Toàn bộ evaluation được tổ chức thành các benchmark độc lập:

~~~mermaid
flowchart TD
    A[Evaluation Dataset] --> B[Retrieval Benchmark]
    A --> C[Hybrid Benchmark]
    A --> D[Adaptive-K Benchmark]
    A --> E[Quality-Cost Benchmark]
    A --> F[Generation Regression]

    B --> G[Evaluation Reports]
    C --> G
    D --> G
    E --> G
    F --> G
~~~

| Benchmark | Mục tiêu |
|---|---|
| Retrieval Benchmark | Đánh giá Dense Retrieval |
| Hybrid Benchmark | Đánh giá Dense + BM25 + RRF |
| Adaptive-K Benchmark | Đánh giá retrieval budget thích ứng |
| Quality–Cost Benchmark | Đánh giá trade-off giữa quality và candidate budget |
| Generation Regression | Đánh giá độ ổn định của generation |

---

## 2. Evaluation Dataset và Ground Truth

Evaluation sử dụng **30 query** được xây dựng cho bài toán Vietnamese Labor Law RAG.

Ground truth được sử dụng để xác định các evidence liên quan và vị trí của evidence đó trong ranking.

Các query được dùng xuyên suốt các benchmark để đảm bảo các phương pháp có thể được so sánh trên cùng một tập dữ liệu.

### Complexity trong Generation Regression

Trong generation regression, có 30 query được chạy và 29 query hoàn thành thành công:

| Complexity | Số query thành công |
|---|---:|
| Simple | 6 |
| Medium | 18 |
| Complex | 5 |
| **Tổng** | **29** |

Một query còn lại phát sinh lỗi trong generation.

### Adaptive-K Benchmark

Adaptive-K benchmark sử dụng toàn bộ 30 query và có phân phối retrieval budget:

| Retrieval K | Số query |
|---|---:|
| K = 5 | 6 |
| K = 10 | 19 |
| K = 20 | 5 |
| **Tổng** | **30** |

Hai bảng trên không mâu thuẫn: bảng đầu chỉ tính **29 query generation thành công**, trong khi Adaptive-K benchmark tính **toàn bộ 30 query**.

---

## 3. Retrieval Metrics

Các metric chính được sử dụng để đánh giá retrieval:

| Metric | Ý nghĩa |
|---|---|
| Hit@1 | Evidence đúng xuất hiện trong Top-1 |
| Hit@3 | Evidence đúng xuất hiện trong Top-3 |
| Hit@5 | Evidence đúng xuất hiện trong Top-5 |
| MRR | Đánh giá vị trí của evidence đúng trong ranking |

### Hit@K

Hit@K kiểm tra xem evidence đúng có xuất hiện trong Top-K hay không.

~~~text
Hit@K =
    1 nếu evidence đúng xuất hiện trong Top-K
    0 nếu không xuất hiện
~~~

Ví dụ:

~~~text
1. Chunk A
2. Chunk B
3. Chunk C  ← Ground Truth
4. Chunk D
5. Chunk E
~~~

Khi đó:

~~~text
Hit@1 = 0
Hit@3 = 1
Hit@5 = 1
~~~

### Mean Reciprocal Rank

MRR đo vị trí của evidence đúng trong ranking.

~~~text
Reciprocal Rank = 1 / rank_of_first_relevant_result
~~~

MRR được tính bằng trung bình Reciprocal Rank trên toàn bộ query.

MRR càng cao nghĩa là evidence đúng có xu hướng xuất hiện càng sớm.

---

## 4. Retrieval Benchmark

Retrieval benchmark đánh giá chất lượng của Dense Retrieval và tác động của Reranking.

Các cấu hình được đánh giá:

| Method | Mô tả |
|---|---|
| Dense | Dense Retrieval bằng BGE-M3 |
| Dense + Reranker | Dense Retrieval + Cross-Encoder |
| Hybrid | Dense + BM25 + RRF |
| Hybrid + Reranker | Hybrid Retrieval + Cross-Encoder |

### Dense Retrieval

Dense Retrieval sử dụng:

~~~text
BGE-M3
~~~

Query được chuyển thành embedding và so sánh với các document chunks đã được vector hóa.

### Dense + Reranker

Pipeline:

~~~mermaid
flowchart LR
    A[Query] --> B[BGE-M3]
    B --> C[Dense Candidates]
    C --> D[Cross-Encoder]
    D --> E[Final Ranking]
~~~

Cross-Encoder đánh giá trực tiếp query–document pair để cải thiện thứ hạng của các ứng viên.

---

## 5. Hybrid Retrieval và RRF

Hybrid Retrieval kết hợp:

~~~text
Dense Retrieval
+
BM25
+
RRF
~~~

Pipeline:

~~~mermaid
flowchart LR
    A[Query] --> B[Dense Retrieval]
    A --> C[BM25]

    B --> D[RRF]
    C --> D

    D --> E[Hybrid Ranking]
~~~

RRF sử dụng:

~~~text
RRF_K = 60
~~~

Với một document có rank `r`, contribution của ranking được tính theo dạng:

~~~text
1 / (RRF_K + r)
~~~

Dense Retrieval và BM25 được hợp nhất thành một ranking chung trước khi đưa sang các bước tiếp theo.

---

## 6. Adaptive-K Evaluation

Adaptive-K đánh giá khả năng điều chỉnh retrieval budget theo độ phức tạp của query.

Quy tắc hiện tại:

| Complexity | Retrieval K |
|---|---:|
| Simple | 5 |
| Medium | 10 |
| Complex | 20 |

Pipeline:

~~~mermaid
flowchart TD
    A[Query] --> B[Complexity Classifier]
    B --> C{Complexity}

    C -->|Simple| D[K = 5]
    C -->|Medium| E[K = 10]
    C -->|Complex| F[K = 20]

    D --> G[Dense + BM25]
    E --> G
    F --> G

    G --> H[RRF]
    H --> I[Cross-Encoder]
~~~

Complexity classifier hiện tại là **rule-based baseline**, chưa phải mô hình Machine Learning.

Các tín hiệu được sử dụng gồm:

- Độ dài câu hỏi.
- Số lượng điều kiện hoặc mệnh đề.
- Phạm vi pháp lý.
- Số lượng yêu cầu hoặc ràng buộc.

---

## 7. Fixed-K Baselines và Adaptive-K Distribution

Adaptive-K được so sánh với các baseline sử dụng K cố định:

| Method | Retrieval K |
|---|---:|
| Fixed-K5 | 5 |
| Fixed-K10 | 10 |
| Fixed-K20 | 20 |
| Adaptive-K | 5 / 10 / 20 |

Trên 30 query của Adaptive-K benchmark:

| Retrieval K | Số query |
|---|---:|
| K = 5 | 6 |
| K = 10 | 19 |
| K = 20 | 5 |
| **Tổng** | **30** |

Average retrieval budget:

~~~text
≈ 10.69
~~~

Adaptive-K không sử dụng cùng một K cho mọi query mà phân bổ budget dựa trên complexity.

---

## 8. Retrieval Results

Kết quả retrieval hiện tại:

| Method | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Dense | 0.6000 | 0.9000 | 1.0000 | 0.7750 |
| Dense + Reranker | 0.8000 | Chưa báo cáo | Chưa báo cáo | 0.8750 |
| Hybrid | Chưa báo cáo | Chưa báo cáo | Chưa báo cáo | 0.8700 |
| Hybrid + Reranker | Chưa báo cáo | Chưa báo cáo | Chưa báo cáo | 0.8750 |
| Adaptive-K | 0.8000 | 0.9667 | 1.0000 | 0.8917 |

> Các ô ghi **“Chưa báo cáo”** là những metric chưa có trong kết quả benchmark hiện tại; không suy diễn hoặc nội suy từ các metric khác.

Adaptive-K đạt:

| Metric | Result |
|---|---:|
| Hit@1 | **0.8000** |
| Hit@3 | **0.9667** |
| Hit@5 | **1.0000** |
| MRR | **0.8917** |

---

## 9. Quality–Cost Evaluation

Quality–Cost Benchmark đánh giá trade-off giữa retrieval quality và số lượng candidate được xử lý.

Do hệ thống hiện tại chưa có benchmark đầy đủ về latency và monetary inference cost, **candidate count** được sử dụng làm proxy cho retrieval budget.

| Method | Tổng candidate |
|---|---:|
| Fixed-K5 | 150 |
| Fixed-K10 | 300 |
| Adaptive-K | 320 |
| Fixed-K20 | 600 |

### So sánh Adaptive-K

| So sánh | Chênh lệch candidate |
|---|---:|
| Adaptive-K vs Fixed-K5 | +113.33% |
| Adaptive-K vs Fixed-K10 | +6.67% |
| Adaptive-K vs Fixed-K20 | -46.67% |

Adaptive-K sử dụng nhiều candidate hơn Fixed-K5, gần tương đương Fixed-K10 và ít hơn đáng kể so với Fixed-K20.

Do đó, kết quả hiện tại cho thấy Adaptive-K nằm giữa các baseline về candidate budget trong khi đạt MRR `0.8917`.

---

## 10. Generation Regression

Generation Regression đánh giá độ ổn định của toàn bộ pipeline khi thực hiện generation.

Benchmark chạy trên:

~~~text
30 queries
~~~

Kết quả hiện tại:

| Metric | Kết quả |
|---|---:|
| Successful queries | 29 / 30 |
| Success rate | 96.67% |
| Average retrieval budget | 10.69 |
| Average citations | 1.24 |

Một query phát sinh:

~~~text
RuntimeError
"Gemini không trả về nội dung"
~~~

Lỗi này thuộc generation layer và được ghi nhận riêng với retrieval metrics.

---

## 11. Generation Configuration

Generation regression sử dụng retry mechanism cho một số lỗi tạm thời.

| Configuration | Value |
|---|---:|
| `max_503_retries` | 3 |
| `initial_retry_seconds` | 5 |
| `stop_on_quota_429` | `true` |

Retry được sử dụng cho lỗi server tạm thời.

Đối với quota `429`, hệ thống dừng thay vì retry vô hạn.

---

## 12. Automated Testing

Software testing và evaluation benchmark được xem là hai lớp kiểm tra khác nhau.

Automated tests kiểm tra:

- API behavior.
- Retrieval components.
- Generation components.
- Integration.
- End-to-end behavior.

Chạy test:

~~~bash
python -m pytest tests/unit tests/integration tests/e2e -q
~~~

Kết quả hiện tại:

~~~text
62 passed
1 warning
~~~

Warning hiện tại đến từ dependency của Starlette và không phải lỗi của application code.

---

## 13. Evaluation Scripts

Các benchmark được triển khai trong:

~~~text
evaluation/scripts/
~~~

| Script | Mục đích |
|---|---|
| `run_retrieval_benchmark.py` | Dense Retrieval benchmark |
| `run_hybrid_benchmark.py` | Hybrid Retrieval benchmark |
| `run_adaptive_benchmark.py` | Adaptive-K benchmark |
| `run_quality_cost_benchmark.py` | Quality–Cost benchmark |
| `run_generation_regression.py` | Generation regression |
| `run_full_evaluation.py` | Chạy toàn bộ evaluation |

---

## 14. Chạy Evaluation

### Chạy từng benchmark

~~~bash
python evaluation/scripts/run_retrieval_benchmark.py
python evaluation/scripts/run_hybrid_benchmark.py
python evaluation/scripts/run_adaptive_benchmark.py
python evaluation/scripts/run_quality_cost_benchmark.py
python evaluation/scripts/run_generation_regression.py
~~~

### Chạy toàn bộ evaluation

~~~bash
python evaluation/scripts/run_full_evaluation.py
~~~

Pipeline:

~~~mermaid
flowchart TD
    A[run_full_evaluation.py]
    A --> B[Retrieval Benchmark]
    A --> C[Hybrid Benchmark]
    A --> D[Adaptive Benchmark]
    A --> E[Quality-Cost Benchmark]
    A --> F[Generation Regression]

    B --> G[Evaluation Reports]
    C --> G
    D --> G
    E --> G
    F --> G
~~~

---

## 15. Evaluation Reports

Kết quả evaluation được lưu trong:

~~~text
evaluation/reports/
~~~

Các report chính:

~~~text
evaluation/reports/evaluation_report.md
evaluation/reports/generation_evaluation_report.md
~~~

Các report được sử dụng để lưu lại kết quả benchmark và phục vụ phân tích sau mỗi lần evaluation.

---

## 16. Evaluation và Testing

Hai lớp đánh giá có mục đích khác nhau:

| Layer | Mục đích |
|---|---|
| Unit Tests | Kiểm tra từng component |
| Integration Tests | Kiểm tra tương tác giữa các component |
| E2E Tests | Kiểm tra toàn bộ application flow |
| Retrieval Benchmark | Đo retrieval quality |
| Adaptive Benchmark | Đo retrieval budget strategy |
| Quality–Cost Benchmark | Đo quality–budget trade-off |
| Generation Regression | Đo generation reliability |

Một hệ thống có thể pass toàn bộ software tests nhưng vẫn có retrieval quality thấp.

Ngược lại, retrieval metric cao không đảm bảo API hoặc application code không có lỗi.

Vì vậy, cả automated testing và evaluation benchmark đều cần thiết.

---

## 17. Evaluation Results Snapshot

Snapshot của evaluation hiện tại:

| Metric | Result |
|---|---:|
| Adaptive-K MRR | **0.8917** |
| Adaptive-K Hit@1 | **0.8000** |
| Adaptive-K Hit@3 | **0.9667** |
| Adaptive-K Hit@5 | **1.0000** |
| Generation Success | **29/30 (96.67%)** |
| Average Retrieval Budget | **10.69** |
| Average Citations | **1.24** |
| Automated Tests | **62 passed** |

Các kết quả này được đo trên benchmark hiện tại và không nên được hiểu là kết quả tổng quát cho toàn bộ domain.

---

## 18. Interpretation

### Retrieval Quality

Dense Retrieval đạt MRR `0.7750`.

Khi thêm Cross-Encoder Reranking:

~~~text
0.7750 → 0.8750
~~~

Điều này cho thấy reranking cải thiện ranking trong benchmark hiện tại.

### Hybrid Retrieval

Hybrid Retrieval đạt MRR `0.8700`.

Kết quả này cho thấy việc kết hợp Dense Retrieval và BM25 tạo ra ranking cạnh tranh với Dense + Reranker trong benchmark hiện tại.

### Adaptive Retrieval

Adaptive-K đạt MRR `0.8917` với:

~~~text
Hit@1 = 0.8000
Hit@3 = 0.9667
Hit@5 = 1.0000
~~~

Adaptive-K đồng thời sử dụng budget khác nhau cho các query khác nhau thay vì một K cố định.

### Generation

Generation regression đạt:

~~~text
29 / 30 successful queries
96.67% success rate
~~~

---

## 19. Limitations

Evaluation hiện tại có một số giới hạn.

### Dataset nhỏ

Benchmark hiện tại chỉ sử dụng 30 query.

Dataset lớn hơn và đa dạng hơn sẽ cần thiết để đánh giá khả năng tổng quát hóa.

### Adaptive-K là rule-based

Complexity classifier hiện tại sử dụng các luật dựa trên đặc điểm query và chưa phải một mô hình học được retrieval budget.

### Candidate Count là proxy

Quality–Cost benchmark hiện sử dụng số lượng candidate làm proxy cho cost.

Chưa có benchmark đầy đủ về:

- Retrieval latency.
- Reranking latency.
- LLM latency.
- Token usage.
- Monetary inference cost.

### Generation phụ thuộc external LLM

Generation regression phụ thuộc provider LLM được cấu hình, trong đó Gemini là provider mặc định.

### Citation correctness chưa được đánh giá độc lập

Hệ thống có Evidence Selection và citations nhưng chưa có benchmark riêng để đo citation precision, recall hoặc faithfulness.

---

## 20. Những gì Evaluation hiện tại chưa chứng minh

Các kết quả hiện tại chưa đủ để kết luận rằng:

- Adaptive-K luôn tốt hơn Fixed-K trên mọi dataset.
- Adaptive-K luôn giảm inference latency.
- Adaptive-K luôn giảm monetary cost.
- Subject-aware Adjustment luôn cải thiện retrieval quality.
- LLM luôn tạo citation chính xác.
- Hệ thống bao phủ toàn bộ pháp luật lao động Việt Nam.
- Hệ thống có thể thay thế tư vấn pháp lý chuyên nghiệp.

Những kết luận này cần benchmark bổ sung.

---

## 21. Hướng mở rộng Evaluation

Các hướng tiếp theo:

| Hướng | Mục tiêu |
|---|---|
| Mở rộng evaluation dataset | Tăng độ tin cậy của benchmark |
| Citation Evaluation | Đánh giá chất lượng citation |
| Latency Benchmark | Đo thời gian retrieval, reranking và generation |
| Token Benchmark | Đo context và generation tokens |
| Cost Benchmark | Ước tính inference cost |
| Complexity Evaluation | Đánh giá complexity classifier |
| Adaptive-K Learning | Học retrieval budget thay vì rule-based |
| Error Analysis | Phân tích các query thất bại |
| Legal-RAG Metrics | Bổ sung metric chuyên biệt cho domain pháp luật |

---

## 22. Reproducibility

Để so sánh kết quả giữa các lần chạy, các yếu tố sau nên được giữ nhất quán:

- Evaluation dataset.
- Ground truth.
- Retrieval configuration.
- `RRF_K`.
- Reranker.
- Adaptive-K rules.
- LLM provider.
- Generation configuration.

Khi thay đổi một thành phần, thay đổi đó cần được ghi nhận trong evaluation report để tránh so sánh không đồng nhất.

---

## 23. Tổng kết

Evaluation methodology của Vietnamese Labor Law RAG được tổ chức thành bốn lớp chính:

~~~mermaid
flowchart TD
    A[Evaluation Dataset]
    A --> B[Retrieval Quality]
    A --> C[Adaptive Retrieval]
    A --> D[Quality-Cost]
    A --> E[Generation Reliability]

    B --> F[Hit@K + MRR]
    C --> F
    C --> G[Candidate Budget]
    D --> G
    E --> H[Success Rate + Statistics]

    F --> I[Evaluation Reports]
    G --> I
    H --> I
~~~

Kết quả hiện tại:

| Nhóm | Kết quả |
|---|---|
| Adaptive-K MRR | **0.8917** |
| Adaptive-K Hit@1 | **0.8000** |
| Adaptive-K Hit@3 | **0.9667** |
| Adaptive-K Hit@5 | **1.0000** |
| Generation Success | **29/30 (96.67%)** |
| Automated Tests | **62 passed** |

Các kết quả trên là **benchmark snapshot trên tập 30 query**, được sử dụng để theo dõi và so sánh các thay đổi trong hệ thống, không phải tuyên bố về khả năng tổng quát của hệ thống trên toàn bộ dữ liệu pháp luật lao động Việt Nam.

---

## 24. Disclaimer

Hệ thống được xây dựng cho mục đích nghiên cứu và đánh giá kỹ thuật. Kết quả retrieval hoặc generation không thay thế cho tư vấn pháp lý chuyên nghiệp hoặc cách giải thích chính thức của cơ quan có thẩm quyền.