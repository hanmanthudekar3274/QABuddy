"""FastAPI app — /chat, /ingest, /health endpoints."""
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

load_dotenv()

from chatbot.qa_chain import ask  # noqa: E402

app = FastAPI(title="QABuddy.ai", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    top_k: int = 8


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]


class IngestRequest(BaseModel):
    source: str = "all"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        result = ask(req.question, top_k=req.top_k)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_ingestion(source: str) -> None:
    logger.info(f"Starting background ingestion: {source}")
    result = subprocess.run(
        ["python", "-m", "ingestion.pipeline", "--source", source],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Ingestion failed: {result.stderr}")
    else:
        logger.info("Ingestion finished successfully")


@app.post("/ingest")
def ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_ingestion, req.source)
    return {"status": "ingestion started", "source": req.source}
