from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.ingestion.embedder import LegalEmbedder

class DenseRetriever:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.embedder = LegalEmbedder()

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Tìm kiếm vector sử dụng pgvector (Cosine Distance).
        """
        # 1. Embed query
        query_embedding = self.embedder.embed([query])[0]
        
        # 2. Query database
        # <=> là cosine distance trong pgvector. Khoảng cách càng nhỏ càng giống nhau.
        # similarity = 1 - distance
        sql = text("""
                        SELECT 
                            document_id,
                            chunk_index,
                            article_title,
                            content,
                            metadata,
                            1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity_score
                        FROM chunks
                        ORDER BY embedding <=> CAST(:query_embedding AS vector)
                        LIMIT :top_k
                    """)
        
        result = self.db.execute(sql, {
            "query_embedding": query_embedding,
            "top_k": top_k
        })
        
        # 3. Format kết quả
        chunks = []
        for row in result:
            chunks.append({
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "article_title": row.article_title,
                "content": row.content,
                "metadata": row.metadata,
                "score": float(row.similarity_score)
            })
            
        return chunks