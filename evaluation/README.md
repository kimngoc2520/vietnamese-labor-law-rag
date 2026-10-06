# Evaluation Reports

Thư mục `evaluation/reports/` lưu các báo cáo kết quả từ evaluation pipeline của **Vietnamese Labor Law RAG**.

Các report được dùng để theo dõi retrieval quality, adaptive retrieval, quality–cost và generation regression.

## 1. Report Structure

    evaluation/reports/
    ├── README.md
    ├── evaluation_report.md
    └── generation_evaluation_report.md

| File | Nội dung |
|---|---|
| `evaluation_report.md` | Retrieval, hybrid retrieval, Adaptive-K và quality–cost |
| `generation_evaluation_report.md` | Generation regression |
| `README.md` | Hướng dẫn sử dụng và diễn giải reports |

---

## 2. Evaluation Report

File:

    evaluation/reports/evaluation_report.md

Report này tổng hợp các kết quả liên quan đến retrieval pipeline.

Các nội dung chính:

- Dense retrieval.
- Dense + reranker.
- Hybrid retrieval.
- Hybrid + reranker.
- Adaptive-K.
- Fixed-K baselines.
- Quality–cost analysis.

Các metric retrieval chính:

| Metric | Ý nghĩa |
|---|---|
| Hit@1 | Relevant result xuất hiện ở vị trí đầu tiên |
| Hit@3 | Relevant result xuất hiện trong top 3 |
| Hit@5 | Relevant result xuất hiện trong top 5 |
| MRR | Đánh giá vị trí trung bình của relevant result |

---

## 3. Generation Evaluation Report

File:

    evaluation/reports/generation_evaluation_report.md

Report này tập trung vào generation regression.

Các thông tin được theo dõi:

- Tổng số queries.
- Số queries thành công.
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

Có một query generation thất bại với lỗi Gemini không trả về nội dung.

---

## 4. Reading the Reports

Evaluation report nên được đọc theo thứ tự:

    Retrieval Quality
          ↓
    Hybrid Retrieval
          ↓
    Adaptive-K
          ↓
    Quality–Cost
          ↓
    Generation Regression

Cách đọc này giúp phân biệt:

- Retrieval có tìm được evidence phù hợp hay không.
- Hybrid retrieval có cải thiện ranking hay không.
- Adaptive-K phân bổ retrieval budget như thế nào.
- Quality có đạt được với candidate budget hợp lý hay không.
- Generation pipeline có ổn định hay không.

---

## 5. Retrieval Results

Kết quả retrieval hiện tại:

| Method | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Dense | 0.6000 | 0.9000 | 1.0000 | 0.7750 |
| Dense + Reranker | 0.8000 | Chưa báo cáo | Chưa báo cáo | 0.8750 |
| Hybrid | Chưa báo cáo | Chưa báo cáo | Chưa báo cáo | 0.8700 |
| Hybrid + Reranker | Chưa báo cáo | Chưa báo cáo | Chưa báo cáo | 0.8750 |
| Adaptive-K | 0.8000 | 0.9667 | 1.0000 | 0.8917 |

`Chưa báo cáo` nghĩa là metric đó không có trong evaluation result hiện tại, không nên tự suy luận từ các metric khác.

---

## 6. Adaptive-K Results

Adaptive-K hiện sử dụng ba mức retrieval budget:

| Complexity | K |
|---|---:|
| Simple | 5 |
| Medium | 10 |
| Complex | 20 |

Phân phối trên 30 queries:

| K | Queries |
|---:|---:|
| 5 | 6 |
| 10 | 19 |
| 20 | 5 |
| **Total** | **30** |

Adaptive-K đạt:

| Metric | Result |
|---|---:|
| Hit@1 | 0.8000 |
| Hit@3 | 0.9667 |
| Hit@5 | 1.0000 |
| MRR | 0.8917 |

---

## 7. Quality–Cost Results

Quality–cost report sử dụng số lượng candidate làm proxy cho retrieval/reranking workload.

| Strategy | Candidates |
|---|---:|
| Fixed K=5 | 150 |
| Fixed K=10 | 300 |
| Adaptive-K | 320 |
| Fixed K=20 | 600 |

So sánh Adaptive-K:

| Baseline | Difference |
|---|---:|
| Fixed K=5 | +113.33% |
| Fixed K=10 | +6.67% |
| Fixed K=20 | −46.67% |

Đây là candidate-count comparison, chưa phải latency benchmark hoặc monetary inference-cost benchmark.

---

## 8. Generation Results

Generation regression hiện tại:

| Metric | Result |
|---|---:|
| Queries | 30 |
| Successful | 29 |
| Failed | 1 |
| Success rate | 96.67% |
| Average retrieval budget | 10.69 |
| Average citations | 1.24 |

Complexity distribution trong generation regression chỉ tính các queries xử lý thành công:

| Complexity | Successful Queries |
|---|---:|
| Simple | 6 |
| Medium | 18 |
| Complex | 5 |
| **Total** | **29** |

Vì vậy distribution này không được dùng để thay thế Adaptive-K distribution trên toàn bộ 30 queries.

---

## 9. Report Generation

Các report có thể được tạo hoặc cập nhật thông qua evaluation scripts.

Chạy toàn bộ evaluation:

    python evaluation/scripts/run_full_evaluation.py

Các benchmark riêng:

    python evaluation/scripts/run_retrieval_benchmark.py
    python evaluation/scripts/run_hybrid_benchmark.py
    python evaluation/scripts/run_adaptive_benchmark.py
    python evaluation/scripts/run_quality_cost_benchmark.py
    python evaluation/scripts/run_generation_regression.py

---

## 10. Report Maintenance

Khi evaluation logic thay đổi:

1. Chạy lại benchmark liên quan.
2. Kiểm tra output.
3. Cập nhật report.
4. Kiểm tra các metric và denominator.
5. Đảm bảo report không sử dụng số liệu từ run cũ.
6. Cập nhật documentation nếu methodology thay đổi.

Đặc biệt cần ghi rõ evaluation dataset và configuration khi so sánh giữa các experiment.

---

## 11. Interpreting Changes

Khi một metric thay đổi, không nên chỉ nhìn vào một con số.

Ví dụ với retrieval:

    MRR ↑
    nhưng
    Candidate Budget ↑↑

có thể cho thấy quality được cải thiện nhưng cost cũng tăng đáng kể.

Ngược lại:

    MRR ≈
    và
    Candidate Budget ↓

có thể là một improvement đáng chú ý đối với adaptive retrieval.

Do đó, quality và cost nên được xem đồng thời.

---

## 12. Limitations

Các report hiện tại có một số giới hạn:

- Evaluation dataset gồm 30 queries.
- Adaptive-K complexity classifier là rule-based.
- Quality–cost sử dụng candidate count thay vì latency thực tế.
- Chưa có citation correctness metric độc lập.
- Generation phụ thuộc vào external LLM API.
- Một số retrieval metrics chưa được báo cáo trong cùng một benchmark.

Các giới hạn này cần được giữ nguyên khi diễn giải kết quả.

---

## 13. Related Documentation

| Document | Nội dung |
|---|---|
| `evaluation/README.md` | Evaluation workflow |
| `docs/evaluation_methodology.md` | Evaluation methodology |
| `docs/development.md` | Development workflow |
| `docs/architecture.md` | System architecture |

---

## 14. Summary

`evaluation/reports/` là nơi lưu kết quả evaluation của project.

Các report chính tập trung vào hai nhóm:

**Retrieval**

    Dense
      ↓
    Hybrid
      ↓
    Reranking
      ↓
    Adaptive-K
      ↓
    Quality–Cost

**Generation**

    Query
      ↓
    Retrieval
      ↓
    Generation
      ↓
    Answer + Citations
      ↓
    Regression Result

Các kết quả trong reports phản ánh evaluation runs hiện tại và cần được cập nhật khi dataset, model, configuration hoặc pipeline thay đổi.