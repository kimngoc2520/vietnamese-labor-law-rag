import json
import re
import sys
from pathlib import Path

from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.connection import SessionLocal


EVIDENCE_PATH = ROOT_DIR / "evaluation" / "datasets" / "ground_truth_evidence.json"


def extract_article_number(article: str) -> int:
    match = re.search(r"Điều\s+(\d+)", article)
    if not match:
        raise ValueError(f"Invalid article format: {article}")
    return int(match.group(1))


def article_matches(article_title: str, article_number: int) -> bool:
    match = re.match(r"^\s*Điều\s+(\d+)\b", article_title or "")
    return bool(match and int(match.group(1)) == article_number)


def audit_evidence():
    print("=" * 80)
    print("GROUND TRUTH EVIDENCE AUDIT")
    print("=" * 80)

    with open(EVIDENCE_PATH, "r", encoding="utf-8") as file:
        evidence_data = json.load(file)

    db = SessionLocal()

    verified_count = 0

    try:
        for item in evidence_data:
            qid = item["query_id"]
            query = item["query"]

            source = item["source"]
            document_id = source["document_id"]
            article = source["article"]
            expected_chunk_index = source["chunk_index"]

            article_number = extract_article_number(article)

            print("\n" + "=" * 80)
            print(f"{qid}: {query}")
            print("-" * 80)
            print(f"Document : {document_id}")
            print(f"Article  : {article}")
            print(f"Expected chunk : {expected_chunk_index}")

            sql = text(
                """
                SELECT
                    chunk_index,
                    article_title,
                    content
                FROM chunks
                WHERE document_id = :document_id
                  AND chunk_index = :chunk_index
                LIMIT 1
                """
            )

            result = db.execute(
                sql,
                {
                    "document_id": document_id,
                    "chunk_index": expected_chunk_index,
                },
            ).fetchone()

            if result is None:
                print("NOT FOUND: chunk không tồn tại trong DB.")
                continue

            chunk_index, article_title, content = result

            article_ok = article_matches(article_title, article_number)

            if not article_ok:
                print("ARTICLE MISMATCH")
                print(f"   Expected : {article}")
                print(f"   Actual   : {article_title}")
                continue

            print("Document + chunk tồn tại")
            print(f"   Article title: {article_title}")
            print(f"   Chunk index  : {chunk_index}")

            snippet = content[:1000].replace("\n", " ")

            print("\nEvidence snippet:")
            print("-" * 80)
            print(snippet)
            print("-" * 80)

            item["annotation"]["verified_against_db"] = True
            verified_count += 1

        with open(EVIDENCE_PATH, "w", encoding="utf-8") as file:
            json.dump(
                evidence_data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print("\n" + "=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print(f"Total entries       : {len(evidence_data)}")
        print(f"Verified against DB : {verified_count}")
        print(f"Not verified        : {len(evidence_data) - verified_count}")
        print("=" * 80)

        print(
            "\nLưu ý: verified_against_db chỉ xác nhận "
            "document/article/chunk tồn tại và khớp."
        )
        print(
            "Nó KHÔNG thay thế human review về semantic relevance."
        )

    finally:
        db.close()


if __name__ == "__main__":
    audit_evidence()