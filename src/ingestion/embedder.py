
from sentence_transformers import SentenceTransformer


class LegalEmbedder:
    _instance = None

    def __new__(cls):
        # Singleton pattern để không load model nhiều lần
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("Đang tải model BGE-M3 vào bộ nhớ...")
            cls._instance.model = SentenceTransformer('BAAI/bge-m3')
        return cls._instance

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Batch encoding để tối ưu hiệu suất
        embeddings = self.model.encode(
            texts,
            batch_size=8,
            show_progress_bar=False,
            normalize_embeddings=True,  # Quan trọng cho cosine similarity
        )
        return embeddings.tolist()