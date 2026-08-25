import os
import io
import json
import base64
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from gtts import gTTS
from dotenv import load_dotenv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

app = FastAPI(title="Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── TF-IDF vector store ───────────────────────────────────────────────────────

DB_PATH = Path("./vector_db.json")


def _load_db() -> list[dict]:
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return []


def _save_db(records: list[dict]) -> None:
    DB_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def search_db(query: str, top_k: int = 3) -> list[str]:
    records = _load_db()
    if not records:
        return []
    docs = [r["text"] for r in records]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(docs + [query])
    scores = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
    indices = np.argsort(scores)[::-1][:top_k]
    return [docs[i] for i in indices if scores[i] > 0.01]


def add_to_db(documents: list[str], ids: list[str] | None = None) -> int:
    records = _load_db()
    existing_ids = {r["id"] for r in records}
    new_ids = ids or [str(uuid.uuid4()) for _ in documents]
    for doc, did in zip(documents, new_ids):
        if did not in existing_ids:
            records.append({"id": did, "text": doc})
    _save_db(records)
    return len(records)


def count_db() -> int:
    return len(_load_db())


def clear_db() -> None:
    _save_db([])


# ─────────────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    text: str
    history: list[dict] = []


class TTSRequest(BaseModel):
    text: str
    lang: str = "en"


class IngestRequest(BaseModel):
    documents: list[str]
    ids: list[str] | None = None


@app.get("/")
async def root():
    return FileResponse("index.html")


def detect_lang(tts_text: str) -> str:
    """Detect language from TTS text (Urdu script chars = ur, else en)."""
    urdu_chars = sum(1 for c in tts_text if "؀" <= c <= "ۿ")
    if urdu_chars > len(tts_text) * 0.2:
        return "ur"
    return "en"


SYSTEM_PROMPT = """\
You are the official admissions voice assistant for Foundation University Islamabad, School of Science and Technology (FUSST), Rawalpindi Campus. Your job is to help prospective students with admissions queries about programmes, fees, scholarships, eligibility, entry tests, and deadlines.

Always answer from the provided knowledge base context first. If the context does not cover the question, say you don't have that information and suggest contacting the admissions office:
- UAN: 051-111-387-211 Ext 245, 247, 243
- Direct: 051-5151436
- WhatsApp: 03178962192
- Apply online: admissions.fui.edu.pk

ALWAYS reply in English regardless of what language the user writes in.

ALWAYS output valid JSON in this exact format — nothing else:
{"reply": "<display text>", "tts": "<speech text>"}

Both "reply" and "tts" must contain the same English text.

IMPORTANT RULES:
- Keep replies to 2-3 short sentences. This is a voice assistant — brevity is key.
- No markdown, no bullet points, no asterisks or special symbols inside the text values.
- Sound warm, helpful and professional — like a knowledgeable admissions officer.
- When quoting fees, say exact rupee amounts clearly.
"""


@app.post("/chat")
async def chat(request: ChatRequest):
    context_docs = search_db(request.text, top_k=3)
    context = "\n---\n".join(context_docs) if context_docs else ""

    system_prompt = SYSTEM_PROMPT
    if context:
        system_prompt += f"\n\nUse this knowledge base context when answering:\n{context}"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.history[-6:]:
        messages.append(msg)
    messages.append({"role": "user", "content": request.text})

    llm_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=350,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    raw = llm_response.choices[0].message.content

    try:
        data = json.loads(raw)
        reply_text = (data.get("reply") or "").strip()
        tts_text = (data.get("tts") or reply_text).strip()
    except (json.JSONDecodeError, AttributeError):
        reply_text = raw.strip()
        tts_text = raw.strip()

    if not reply_text:
        reply_text = tts_text

    lang = detect_lang(tts_text)
    return {"response": reply_text, "tts_text": tts_text, "lang": lang}


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    tts = gTTS(text=request.text, lang=request.lang, slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    audio_b64 = base64.b64encode(buf.read()).decode("utf-8")
    return {"audio": audio_b64, "format": "mp3"}


@app.post("/ingest")
async def ingest(request: IngestRequest):
    if not request.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    total = add_to_db(request.documents, request.ids)
    return {"message": f"Ingested {len(request.documents)} documents", "total": total}


@app.get("/stats")
async def stats():
    return {"documents_in_db": count_db()}


@app.delete("/reset")
async def reset_db():
    clear_db()
    return {"message": "Knowledge base cleared"}
