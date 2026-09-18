from typing import List, Dict, Any


class HybridRetriever:
    """
    Kết hợp nhiều retrieval methods bằng Reciprocal Rank Fusion (RRF).

    Công thức:
        score(d) = Σ 1 / (k + rank_i(d))

    RRF_K = 60 theo cấu hình thường dùng.
    """

    RRF_K = 60

    def fuse(
        self,
        ranking_lists: List[List[Dict[str, Any]]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Fuse nhiều ranking lists thành một ranking duy nhất.

        Args:
            ranking_lists:
                Danh sách các ranking lists.
                Mỗi list đã được sort theo relevance giảm dần.

            top_k:
                Số kết quả cuối cùng trả về.
        """

        doc_scores: Dict[str, Dict[str, Any]] = {}

        # Source tương ứng với thứ tự ranking_lists:
        # [Dense results, BM25 results]
        source_names = ["dense", "bm25"]

        for source_index, ranking_list in enumerate(ranking_lists):
            if source_index < len(source_names):
                source_name = source_names[source_index]
            else:
                source_name = f"retriever_{source_index}"

            for rank, doc in enumerate(ranking_list, start=1):
                doc_id = (
                    f"{doc['document_id']}_"
                    f"{doc['chunk_index']}"
                )

                rrf_score = 1.0 / (self.RRF_K + rank)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "doc": doc,
                        "rrf_score": 0.0,
                        "sources": [],
                    }

                doc_scores[doc_id]["rrf_score"] += rrf_score

                if source_name not in doc_scores[doc_id]["sources"]:
                    doc_scores[doc_id]["sources"].append(
                        source_name
                    )

        # Sort theo RRF score giảm dần.
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        results = []

        for item in sorted_docs[:top_k]:
            doc = item["doc"].copy()

            doc["rrf_score"] = item["rrf_score"]
            doc["retrieval_sources"] = item["sources"]

            results.append(doc)

        return results