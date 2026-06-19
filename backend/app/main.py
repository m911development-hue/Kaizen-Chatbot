"""
Kaizen AI - FastAPI Application Entry Point
=============================================
Run from the project root:
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

The application:
  • Serves the frontend SPA from /static and / (index.html)
  • Exposes REST + SSE APIs under /api/
  • Initializes the RAG service and data directories on startup
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.routers import chat, voice
from backend.app.services.rag_service import rag_service

# ──────────────────────────────────────────────
# Logging configuration
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("kaizen.main")


# ──────────────────────────────────────────────
# Application lifespan (startup / shutdown)
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.
    - Creates required directories
    - Relocates company PDF to backend/knowledge if found in old data directory
    - Initializes the RAG service (ChromaDB + embeddings)
    """
    # --- Startup ---
    logger.info("🚀 Starting Kaizen AI …")

    import shutil

    # Ensure directories exist
    knowledge_dir = Path(settings.KNOWLEDGE_DIR)
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    chromadb_dir = Path(settings.CHROMADB_DIR)
    chromadb_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if there is an existing Kaizen.pdf in old location and relocate it
    old_pdf_path = Path("data/uploads/Kaizen.pdf")
    new_pdf_path = Path(settings.COMPANY_PDF_PATH)
    if old_pdf_path.exists() and not new_pdf_path.exists():
        logger.info(f"Relocating company PDF from {old_pdf_path} to {new_pdf_path}")
        shutil.move(str(old_pdf_path), str(new_pdf_path))
        # Remove old meta JSON if it exists
        old_meta = Path("data/uploads/Kaizen.pdf.meta.json")
        if old_meta.exists():
            old_meta.unlink()

    logger.info("Data directories ready: %s, %s", settings.KNOWLEDGE_DIR, settings.CHROMADB_DIR)

    # Initialize the RAG pipeline (loads ChromaDB, creates embeddings model)
    try:
        rag_service.initialize()
        logger.info("RAG service initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize RAG service: %s", exc, exc_info=True)

    yield  # ← application is running

    # --- Shutdown ---
    logger.info("👋 Shutting down Kaizen AI.")


# ──────────────────────────────────────────────
# FastAPI application instance
# ──────────────────────────────────────────────

app = FastAPI(
    title="Kaizen AI",
    description=(
        "Intelligent knowledge-base chatbot powered by RAG. "
        "Upload PDFs, ask questions, and get accurate answers "
        "grounded in your documents — with voice support."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# CORS middleware (permissive for development)
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Static files & templates
# ──────────────────────────────────────────────
# Paths are relative to the project root (where uvicorn is invoked).
# The frontend directory sits at:  <project_root>/frontend/

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")


# ──────────────────────────────────────────────
# Include API routers
# ──────────────────────────────────────────────

app.include_router(chat.router)
app.include_router(voice.router)


# ──────────────────────────────────────────────
# Root route — serve the SPA
# ──────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Serve the frontend index.html page."""
    return templates.TemplateResponse(request, "index.html")


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Lightweight health check endpoint.
    Returns service status and knowledge base stats.
    """
    try:
        stats = rag_service.get_stats()
    except Exception:
        stats = {"has_documents": False, "total_documents": 0, "total_chunks": 0}

    return {
        "status": "healthy",
        "service": "Kaizen AI",
        "version": "1.0.0",
        "knowledge_base": stats,
    }


# ──────────────────────────────────────────────
# Global exception handler
# ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unhandled exceptions.
    Returns a clean JSON error instead of an HTML traceback.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )
