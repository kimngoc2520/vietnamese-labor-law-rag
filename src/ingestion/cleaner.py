import re


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # 1. Chuẩn hóa line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Xóa ký tự điều khiển / artifact từ PDF
        text = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "",
            text,
        )

        # 3. Chuẩn hóa khoảng trắng trong từng dòng
        text = re.sub(r"[ \t]+", " ", text)

        # 4. Chuẩn hóa định dạng Điều / Khoản / Điểm
        text = re.sub(r"Điều\s+(\d+)", r"Điều \1", text)
        text = re.sub(r"Khoản\s+(\d+)", r"Khoản \1", text)
        text = re.sub(r"Điểm\s+([a-z])\s*\)", r"Điểm \1)", text)

        # 5. Giảm số dòng trống liên tiếp
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()