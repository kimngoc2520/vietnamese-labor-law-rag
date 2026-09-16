import sys
import os
# Thêm thư mục gốc vào path để import được src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from src.db.connection import engine
from src.db.models import Base

def init_db():
    print(" Đang kiểm tra kết nối PostgreSQL...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(" Kết nối PostgreSQL thành công!")
    except Exception as e:
        print(f" Lỗi kết nối database: {e}")
        print(" Hãy kiểm tra lại docker-compose đang chạy và biến DATABASE_URL trong file .env")
        return

    print(" Đang bật extension pgvector...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        print(" Extension pgvector đã sẵn sàng.")
    except Exception as e:
        print(f"️ Lưu ý khi tạo extension: {e}")

    print(" Đang tạo bảng documents và chunks...")
    Base.metadata.create_all(bind=engine)
    print(" Tạo bảng thành công!")

    print("\n Database initialization hoàn tất.")
    print(" Tiếp theo, chạy lệnh dưới đây để kiểm tra bảng đã tạo:")
    print('docker compose exec db psql -U postgres -d legal_rag -c "\\dt"')

if __name__ == "__main__":
    init_db()