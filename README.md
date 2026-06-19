# 🤖 Kaizen AI — Intelligent Knowledge Assistant

A production-ready AI chatbot that answers questions based on your uploaded PDF documents. Features text and voice conversations, powered by OpenAI and a RAG (Retrieval-Augmented Generation) pipeline.

![Kaizen AI](frontend/assets/kaizen-avatar.png)

---

## ✨ Features

- **📄 PDF Knowledge Base** — Upload PDFs, extract & index content, answer questions grounded in your documents
- **💬 Smart Text Chat** — ChatGPT-style interface with typing indicators, timestamps, and conversation history
- **🎙️ Voice Chat** — Speak your questions (Speech-to-Text) and hear natural responses (Text-to-Speech)
- **🔒 No Hallucination** — Responses are strictly based on uploaded documents; politely declines if info isn't available
- **🎨 Premium UI** — Glassmorphism design, smooth animations, fully responsive (desktop, tablet, mobile)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) |
| **AI/LLM** | OpenAI GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-3-small |
| **Vector Database** | ChromaDB |
| **RAG Pipeline** | LangChain (LCEL) |
| **PDF Parsing** | pdfplumber |
| **Speech-to-Text** | OpenAI Whisper |
| **Text-to-Speech** | OpenAI TTS-1-HD (nova voice) |
| **Frontend** | Vanilla HTML, CSS, JavaScript |

---

## 📋 Prerequisites

- **Python 3.10+** installed
- **OpenAI API Key** with access to:
  - Chat Completions (GPT-4o-mini)
  - Embeddings (text-embedding-3-small)
  - Audio (Whisper, TTS)
- **Git** (optional)

---

## 🚀 Installation

### 1. Clone or navigate to the project

```bash
cd "Kaizen Chatbot"
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

**Activate it:**

- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```bash
# Copy the example
copy backend\.env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 5. Start the server

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open in browser

Navigate to: **http://localhost:8000**

---

## 📖 Usage

### Upload PDFs
1. In the left sidebar, find the **Knowledge Base** section
2. **Drag & drop** PDF files onto the upload zone, or click to browse
3. Wait for processing (extraction → chunking → embedding → indexing)
4. Your documents appear in the list below

### Text Chat
1. Type your question in the input field
2. Press **Enter** or click the **Send** button
3. The AI will search your documents and respond with sourced answers
4. Conversation history is maintained during the session

### Voice Chat
1. Click the **🎤 Microphone** button to start recording
2. Speak your question
3. Click again to stop recording
4. The AI will transcribe your speech, generate an answer, and read it aloud
5. Use **Stop** / **Replay** controls for audio playback

---

## 📁 Project Structure

```
Kaizen Chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings configuration
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── routers/
│   │   │   ├── chat.py          # Chat API endpoints
│   │   │   ├── documents.py     # PDF management endpoints
│   │   │   └── voice.py         # Voice API endpoints
│   │   └── services/
│   │       ├── pdf_service.py   # PDF parsing & chunking
│   │       ├── rag_service.py   # RAG pipeline
│   │       └── voice_service.py # STT & TTS
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html               # Main page
│   ├── css/
│   │   └── styles.css           # Premium UI styles
│   ├── js/
│   │   ├── app.js               # App orchestrator
│   │   ├── chat.js              # Chat module
│   │   ├── voice.js             # Voice module
│   │   └── ui.js                # UI interactions
│   └── assets/
│       └── kaizen-avatar.png    # AI avatar
├── data/
│   ├── uploads/                 # Uploaded PDFs
│   └── chromadb/                # Vector store
├── .env                         # API keys (not in git)
├── .gitignore
└── README.md
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve frontend |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Send text message |
| `POST` | `/api/chat/stream` | Stream chat response (SSE) |
| `POST` | `/api/documents/upload` | Upload PDF(s) |
| `GET` | `/api/documents` | List documents |
| `GET` | `/api/documents/status` | Knowledge base status |
| `DELETE` | `/api/documents/{filename}` | Delete document |
| `POST` | `/api/voice/transcribe` | Speech to text |
| `POST` | `/api/voice/synthesize` | Text to speech |
| `POST` | `/api/voice/chat` | Full voice pipeline |

---

## ⚙️ Configuration

All settings can be configured via the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `CHAT_MODEL` | `gpt-4o-mini` | Chat completion model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `TTS_MODEL` | `tts-1-hd` | Text-to-speech model (HD for natural voice) |
| `TTS_VOICE` | `nova` | TTS voice (nova, alloy, shimmer, etc.) |
| `STT_MODEL` | `whisper-1` | Speech-to-text model |
| `CHUNK_SIZE` | `1000` | Text chunk size for splitting |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `MAX_FILE_SIZE` | `52428800` | Max upload size (50MB) |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Module not found"** | Make sure virtual environment is activated and dependencies installed |
| **"Invalid API key"** | Check your `.env` file has a valid `OPENAI_API_KEY` |
| **"No documents uploaded"** | Upload at least one PDF before chatting |
| **Microphone not working** | Allow browser microphone access; use HTTPS in production |
| **Slow responses** | Normal for first request (model loading). Subsequent requests are faster |
| **Large PDF fails** | Max file size is 50MB. Split large PDFs into smaller ones |

---

## 📄 License

This project is for educational and personal use.

---

Built with ❤️ by **Kaizen AI**
