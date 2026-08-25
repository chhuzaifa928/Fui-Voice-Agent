"""
Ingest all DOCX documents from data/doc_extracted/documents/ into vector_db.json.

Usage:
    python ingest_docs.py           # ingest all docs (appends, skips duplicates)
    python ingest_docs.py --clear   # wipe DB first, then ingest
"""
import sys
import uuid
import json
import re
from pathlib import Path
from docx import Document

DOCS_DIR = Path("./data/doc_extracted/documents")
DB_PATH = Path("./vector_db.json")

DOCX_FILES = [
    "D BS Programmes Details.docx",
    "D MS Programmes Details.docx",
    "D FAQs.docx",
    "D Scholarships (1).docx",
    "D FUI Admission Campaign on Social Media for Session Spring 2024.docx",
    "D content for social media.docx",
]

CHUNK_SIZE = 900  # target characters per chunk


def clean(text: str) -> str:
    text = re.sub(r'&amp;', '&', text)
    # Remove all emoji and symbol Unicode ranges
    text = re.sub(
        r'[\U0001F000-\U0001FFFF'  # emoji / symbols
        r'\U00002600-\U000027BF'   # misc symbols & dingbats
        r'\U0000FE00-\U0000FE0F'   # variation selectors
        r'\U00002702-\U000027B0'   # dingbats
        r'️‍]',          # VS-16, ZWJ
        '', text, flags=re.UNICODE
    )
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_paragraphs(docx_path: Path) -> list[str]:
    doc = Document(str(docx_path))
    paras = []
    for para in doc.paragraphs:
        text = clean(para.text)
        if text:
            paras.append(text)
    return paras


def chunk_paragraphs(paras: list[str], source: str) -> list[str]:
    chunks = []
    current = f"[Source: {source}]\n"
    for para in paras:
        if len(current) + len(para) + 1 > CHUNK_SIZE and len(current) > len(f"[Source: {source}]\n"):
            chunks.append(current.strip())
            current = f"[Source: {source}]\n" + para + " "
        else:
            current += para + " "
    if current.strip() and current.strip() != f"[Source: {source}]":
        chunks.append(current.strip())
    return chunks


def load_db() -> list[dict]:
    return json.loads(DB_PATH.read_text(encoding="utf-8")) if DB_PATH.exists() else []


def save_db(records: list[dict]) -> None:
    DB_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    clear = "--clear" in sys.argv

    if clear:
        save_db([])
        print("Knowledge base cleared.")

    records = load_db()
    existing_texts = {r["text"] for r in records}
    total_added = 0

    for fname in DOCX_FILES:
        fpath = DOCS_DIR / fname
        if not fpath.exists():
            print(f"  [skip] not found: {fname}")
            continue

        paras = extract_paragraphs(fpath)
        chunks = chunk_paragraphs(paras, fname.replace(".docx", "").replace("D ", "").strip())
        added = 0
        for chunk in chunks:
            if chunk not in existing_texts:
                records.append({"id": str(uuid.uuid4()), "text": chunk})
                existing_texts.add(chunk)
                added += 1
        print(f"  {fname}: {added} chunks added ({len(chunks)} total)")
        total_added += added

    save_db(records)
    print(f"\nDone. Added {total_added} chunks. Total in DB: {len(records)}")


if __name__ == "__main__":
    main()
