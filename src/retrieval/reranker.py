from typing import Any

from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("Đang tải Cross-Encoder Reranker (BGE-v2-m3)...")
            cls._instance.model = CrossEncoder('BAAI/bge-reranker-v2-m3')
        return cls._instance

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Rerank danh sách candidates dựa trên điểm số của Cross-Encoder.
        """
        if not candidates:
            return []

        # 1. Tạo cặp (query, content)
        pairs = [(query, candidate["content"]) for candidate in candidates]
        
        # 2. Dự đoán điểm số
        scores = self.model.predict(pairs, show_progress_bar=False)
        
        # 3. Gán điểm số mới
        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(scores[i])
            
        # 4. Sắp xếp giảm dần
        reranked_candidates = sorted(
            candidates, 
            key=lambda x: x["rerank_score"], 
            reverse=True
        )
        
        return reranked_candidates[:top_k]