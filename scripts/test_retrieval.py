import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.connection import SessionLocal
from src.retrieval.dense import DenseRetriever
from src.retrieval.reranker import CrossEncoderReranker

def main():
    print(" Testing Retrieval Pipeline...\n")
    
    query = "Người lao động đơn phương chấm dứt hợp đồng lao động thì phải báo trước bao nhiêu ngày?"
    print(f"Query: '{query}'\n")
    
    db = SessionLocal()
    try:
        # 1. Dense Retrieval
        print(" Đang chạy Dense Retrieval (Top 10)...")
        dense_retriever = DenseRetriever(db)
        candidates = dense_retriever.retrieve(query, top_k=10)
        print(f"   → Tìm thấy {len(candidates)} chunks\n")
        
        if not candidates:
            print(" Không tìm thấy kết quả nào. Hãy kiểm tra lại database.")
            return

        # 2. Reranking
        print(" Đang chạy Cross-Encoder Reranker (Top 3)...")
        reranker = CrossEncoderReranker()
        final_results = reranker.rerank(query, candidates, top_k=3)
        
        print("\nKẾT QUẢ CUỐI CÙNG:")
        for i, res in enumerate(final_results, 1):
            print(f"\n--- Kết quả {i} (Rerank Score: {res['rerank_score']:.4f}) ---")
            print(f"Tài liệu: {res['metadata'].get('document_title')}")
            print(f"Điều khoản: {res['article_title']}")
            print(f"Nội dung: {res['content'][:200]}...")
            
    except Exception as e:
        print(f" Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()