import json
import os
import re
from pathlib import Path

from pypdf import PdfReader


def clean_text(text: str) -> str:
    """Làm sạch text: xóa khoảng trắng thừa, chuẩn hóa dấu câu"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Điều\s+(\d+)', r'Điều \1', text)
    text = re.sub(r'Khoản\s+(\d+)', r'Khoản \1', text)
    return text.strip()

def main():
    print("Bắt đầu chuyển đổi PDF sang Markdown...")
    
    # 1. Load metadata
    with open("data/raw/metadata.json", "r", encoding="utf-8") as f:
        metadata_config = json.load(f)
    
    doc_map = {doc["filename"]: doc for doc in metadata_config["documents"]}
    
    # 2. Tạo thư mục output
    output_dir = Path("data/processed/legal_texts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Xử lý từng file
    for filename, meta in doc_map.items():
        pdf_path = f"data/raw/{filename}"
        if not os.path.exists(pdf_path):
            print(f" Bỏ qua: {filename} (Không tìm thấy file)")
            continue
            
        print(f"📄 Đang xử lý: {meta['title']}")
        
        # Extract text từ PDF
        reader = PdfReader(pdf_path)
        raw_text = ""
        for page in reader.pages:
            raw_text += page.extract_text() + "\n"
            
        clean_txt = clean_text(raw_text)
        
        # Tạo YAML Frontmatter cho Metadata
        yaml_header = f"""---
document_id: "{meta['document_id']}"
title: "{meta['title']}"
document_type: "{meta['document_type']}"
year: {meta['year']}
source: "{meta['source']}"
effective_date: "{meta['effective_date']}"
status: "{meta['status']}"
---

"""
        # Nội dung chính
        md_content = f"{yaml_header}# {meta['title']}\n\n{clean_txt}"
        
        # Lưu file
        md_filename = meta["document_id"].lower() + ".md"
        md_path = output_dir / md_filename
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"   ✅ Đã lưu: {md_filename} ({len(clean_txt)} ký tự)")

    print("Hoàn tất chuyển đổi PDF sang Markdown!")

if __name__ == "__main__":
    main()