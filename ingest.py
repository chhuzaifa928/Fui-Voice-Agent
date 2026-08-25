"""Bulk-ingest text files or raw text into the vector DB from the command line.

Usage:
    python ingest.py document.txt
    python ingest.py --text "Paragraph one.\n\nParagraph two."
    python ingest.py --clear
"""
import sys
import uuid
import json
from pathlib import Path

DB_PATH = Path("./vector_db.json")


def load_db():
    return json.loads(DB_PATH.read_text(encoding="utf-8")) if DB_PATH.exists() else []


def save_db(records):
    DB_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def add_chunks(text: str):
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if not chunks:
        print("No content to ingest.")
        return
    records = load_db()
    for chunk in chunks:
        records.append({"id": str(uuid.uuid4()), "text": chunk})
    save_db(records)
    print(f"Ingested {len(chunks)} chunk(s). Total in DB: {len(records)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--clear":
        save_db([])
        print("Knowledge base cleared.")
        return

    if sys.argv[1] == "--text":
        raw = " ".join(sys.argv[2:]).replace("\\n", "\n")
        add_chunks(raw)
        return

    filepath = sys.argv[1]
    with open(filepath, "r", encoding="utf-8") as f:
        add_chunks(f.read())


if __name__ == "__main__":
    main()
