# FUI Voice Agent

A voice-powered admissions assistant for **Foundation University Islamabad**, School of Science and Technology (FUSST), Rawalpindi Campus. Built with FastAPI, Groq LLM, and Google TTS.

Users can speak naturally in **English**, **Roman Urdu**, or **Urdu** and receive instant, context-aware answers about admissions, programmes, fees, scholarships, eligibility, and deadlines.

---

## Features

- **Real-time voice interaction** — Web Speech API for speech-to-text in the browser
- **RAG-powered responses** — TF-IDF retrieval from a local knowledge base feeds context to Llama 3.3 70B via Groq
- **Text-to-speech output** — Google TTS generates natural-sounding audio replies
- **Multilingual support** — English, Roman Urdu, and Urdu
- **Built-in knowledge base** — Pre-loaded with BS/MS programme details, FAQs, scholarships, and fee structures from official FUI documents
- **Live KB management** — Add, view, and clear knowledge base entries directly from the UI
- **Animated orb UI** — Visual state indicators for listening, thinking, speaking, and paused states

---

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────┐     ┌──────────┐
│   Browser    │────▶│         FastAPI Backend          │────▶│  Groq    │
│  Web Speech  │     │  /chat  /tts  /ingest  /stats   │     │ Llama 3.3│
│  API (STT)   │◀────│         TF-IDF Vector DB        │◀────│   LLM    │
│  gTTS Audio  │     │         Google TTS               │     └──────────┘
└─────────────┘     └─────────────────────────────────┘
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Vanilla HTML/CSS/JS | Chat UI, speech recognition, audio playback |
| Backend | FastAPI (Python) | REST API serving all endpoints |
| LLM | Groq — Llama 3.3 70B Versatile | Generates structured JSON responses |
| STT | Web Speech API | Browser-native speech recognition |
| TTS | gTTS (Google) | Converts text responses to MP3 audio |
| Vector Store | TF-IDF + Cosine Similarity | Lightweight document retrieval |

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/keys)
- Google Chrome or Edge (required for Web Speech API)

### Installation

```bash
# Clone the repository
git clone https://github.com/chhuzaifa928/Fui-Voice-Agent.git
cd Fui-Voice-Agent

# Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the example env file and add your API key
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

### Ingest the Knowledge Base

```bash
# Load official FUI documents into the vector DB
python ingest_docs.py --clear
```

### Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in Chrome or Edge.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the web interface |
| `/chat` | POST | Sends a message and returns an LLM-generated response with TTS text |
| `/tts` | POST | Converts text to base64-encoded MP3 audio |
| `/ingest` | POST | Adds documents to the knowledge base |
| `/stats` | GET | Returns the number of documents in the knowledge base |
| `/reset` | DELETE | Clears all documents from the knowledge base |

### POST `/chat`

```json
// Request
{ "text": "What are the BSSE admission requirements?", "history": [] }

// Response
{ "response": "For BSSE you need F.Sc with minimum 50% marks...", "tts_text": "...", "lang": "en" }
```

### POST `/ingest`

```json
// Request
{ "documents": ["Chunk one text.", "Chunk two text."] }

// Response
{ "message": "Ingested 2 documents", "total": 47 }
```

---

## Project Structure

```
FUI-voice-agent/
├── main.py               # FastAPI application and all endpoints
├── ingest_docs.py         # Bulk DOCX ingestion script
├── ingest.py              # CLI tool for text file ingestion
├── index.html             # Single-page web interface
├── requirements.txt       # Python dependencies
├── vector_db.json         # TF-IDF knowledge base (JSON)
├── .env.example           # Environment variable template
├── data/
│   └── doc_extracted/
│       └── documents/     # Source DOCX/PDF documents
└── README.md
```

---

## Adding Custom Documents

### Via the Web UI

1. Expand the **Knowledge Base** panel
2. Paste text (separate chunks with a blank line)
3. Click **Add to Knowledge Base**

### Via CLI

```bash
# Ingest a text file
python ingest.py document.txt

# Ingest raw text
python ingest.py --text "Your text here."

# Clear and re-ingest
python ingest.py --clear
```

### Via API

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"documents": ["chunk one", "chunk two"]}'
```

---

## Technology Decisions

| Choice | Rationale |
|--------|-----------|
| **Groq + Llama 3.3** | Fast inference with structured JSON output support |
| **TF-IDF** | Zero external dependencies, instant indexing, no GPU required |
| **gTTS** | Free, reliable, no API key needed for TTS |
| **Web Speech API** | Native browser support, no third-party STT service required |
| **FastAPI** | Async support, auto-generated docs, minimal boilerplate |

---

## License

This project is for educational and internal use at Foundation University Islamabad.
