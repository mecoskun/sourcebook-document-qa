import asyncio
import hashlib
import json
import secrets
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import ROOT, settings
from app.limits import BodyLimitMiddleware
from app.mcp_client import MCPBridge
from app.model import LocalModel


@dataclass
class Workspace:
    id: str
    expires: float
    questions: int = 0


sessions: dict[str, Workspace] = {}
bridge = MCPBridge()
model = LocalModel()
operation_lock = asyncio.Lock()
budget = {"date": datetime.now(UTC).date(), "questions": 0, "uploads": 0, "sessions": 0}


def reserve(kind: str, limit: int):
    if budget["date"] != datetime.now(UTC).date():
        budget.update(date=datetime.now(UTC).date(), questions=0, uploads=0, sessions=0)
    if budget[kind] >= limit:
        raise HTTPException(429, "Today's demo allowance is used up. Please try again tomorrow.")
    budget[kind] += 1


async def reap():
    while True:
        await asyncio.sleep(30)
        async with operation_lock:
            for key, workspace in list(sessions.items()):
                if workspace.expires <= time.monotonic():
                    await bridge.call("delete_document", session_id=workspace.id)
                    sessions.pop(key, None)


@asynccontextmanager
async def lifespan(app):
    worker = asyncio.create_task(bridge.run())
    await asyncio.wait_for(bridge.ready.wait(), 30)
    if bridge.error:
        await worker
        raise RuntimeError("Could not start MCP server") from bridge.error
    cleaner = asyncio.create_task(reap())
    try:
        yield
    finally:
        cleaner.cancel()
        await asyncio.gather(cleaner, return_exceptions=True)
        await bridge.queue.put(None)
        await worker
        await model.client.aclose()


app = FastAPI(title="Sourcebook", lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware, limit=settings.max_file_bytes + 65536)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_methods=["GET", "POST", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def headers_and_size(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


def workspace(authorization: str = Header(default="")) -> Workspace:
    token = authorization.removeprefix("Bearer ")
    item = sessions.get(hashlib.sha256(token.encode()).hexdigest())
    if item is None or item.expires <= time.monotonic():
        raise HTTPException(401, "Your workspace expired. Reload the page to start a new one.")
    return item


async def available():
    if operation_lock.locked():
        raise HTTPException(429, "The demo is handling another request. Please try again shortly.")
    async with operation_lock:
        yield


@app.get("/api/health")
async def health():
    return {"status": "ok", "model_ready": await model.ready(),
            "retrieval": "MCP + local embeddings", "retention_seconds": settings.session_ttl_seconds}


@app.post("/api/sessions")
async def create_session():
    if len(sessions) >= settings.max_sessions:
        raise HTTPException(429, "The demo is at capacity. Please try again later.")
    reserve("sessions", 100)
    token = secrets.token_urlsafe(32)
    sessions[hashlib.sha256(token.encode()).hexdigest()] = Workspace(
        id=secrets.token_hex(16), expires=time.monotonic() + settings.session_ttl_seconds)
    return {"token": token, "expires_in": settings.session_ttl_seconds}


@app.get("/api/documents")
async def documents(ws=Depends(workspace)):
    return await bridge.call("list_documents", session_id=ws.id)


async def index(data: bytes, name: str, ws: Workspace):
    existing = await bridge.call("list_documents", session_id=ws.id)
    if len(existing) >= settings.max_documents:
        raise HTTPException(400, "Remove a document before adding another (maximum five).")
    reserve("uploads", settings.daily_uploads)
    parser = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "app.parse_worker", name, cwd=str(ROOT),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL)
    try:
        output, _ = await asyncio.wait_for(parser.communicate(data), 20)
        parsed = json.loads(output)
        if "error" in parsed:
            raise HTTPException(400, parsed["error"])
        sections = parsed["sections"]
    except (TimeoutError, ValueError, KeyError) as exc:
        raise HTTPException(400, "This document is too complex or could not be parsed.") from exc
    finally:
        if parser.returncode is None:
            parser.kill()
            await parser.wait()
    try:
        return await bridge.call("index_document", session_id=ws.id, name=name, sections=sections)
    except (RuntimeError, TimeoutError) as exc:
        raise HTTPException(503, "Indexing failed. Check that the embedding model is downloaded.") from exc


@app.post("/api/documents", dependencies=[Depends(available)])
async def upload(ws=Depends(workspace), file: UploadFile = File()):
    try:
        data = await file.read(settings.max_file_bytes + 1)
        if len(data) > settings.max_file_bytes:
            raise HTTPException(413, "Files must be 10 MB or smaller.")
        name = (file.filename or "document").replace("\\", "/").split("/")[-1][:160]
        return await index(data, name, ws)
    finally:
        await file.close()


@app.post("/api/sample", dependencies=[Depends(available)])
async def sample(ws=Depends(workspace)):
    return await index((ROOT / "samples" / "employee-handbook.txt").read_bytes(),
                       "Employee handbook.txt", ws)


@app.delete("/api/documents/{document_id}", dependencies=[Depends(available)])
async def delete(document_id: str, ws=Depends(workspace)):
    existing = await bridge.call("list_documents", session_id=ws.id)
    if document_id not in {d["id"] for d in existing}:
        raise HTTPException(404, "Document not found in this workspace.")
    return await bridge.call("delete_document", session_id=ws.id, document_id=document_id)


@app.delete("/api/documents", dependencies=[Depends(available)])
async def clear(ws=Depends(workspace)):
    return await bridge.call("delete_document", session_id=ws.id)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@app.post("/api/questions", dependencies=[Depends(available)])
async def question(payload: Question, ws=Depends(workspace)):
    text = payload.question.strip()
    if not text:
        raise HTTPException(400, "Please enter a question.")
    if ws.questions >= settings.per_session_questions:
        raise HTTPException(429, "This workspace has reached its 20-question allowance.")
    if not await bridge.call("list_documents", session_id=ws.id):
        raise HTTPException(400, "Add a document before asking a question.")
    reserve("questions", settings.daily_questions)
    ws.questions += 1
    start = time.perf_counter()
    try:
        sources = await bridge.call("search_documents", session_id=ws.id, question=text)
        answer = await model.answer(text, sources)
    except (RuntimeError, TimeoutError) as exc:
        raise HTTPException(503, "The document service is unavailable. Please try again.") from exc
    return {**answer, "elapsed_ms": round((time.perf_counter() - start) * 1000)}


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
