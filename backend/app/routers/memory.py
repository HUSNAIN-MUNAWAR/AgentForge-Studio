import re
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import MemoryChunk, MemoryDocument, UploadedFile

router = APIRouter(prefix="/memory", tags=["memory"])


def _chunks(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    out = []
    start = 0
    while start < len(clean):
        out.append(clean[start:start + size])
        start += max(size - overlap, 1)
    return out


def _keywords(text: str) -> str:
    tokens = re.findall(r"[a-zA-Z0-9_]{3,}", text.lower())
    return " ".join(sorted(set(tokens))[:300])


@router.post("/index")
def index_file(file_id: str, db: Session = Depends(get_db)):
    file = db.get(UploadedFile, file_id)
    if not file:
        raise HTTPException(404, "File not found")
    text = Path(file.stored_path).read_text(encoding="utf-8", errors="ignore")
    doc = MemoryDocument(id=str(uuid.uuid4()), file_id=file.id, title=file.original_name, text=text[:100000], metadata_json={"source": "upload", "engine": "keyword"})
    db.add(doc)
    db.flush()
    created = 0
    for idx, chunk_text in enumerate(_chunks(text)):
        db.add(MemoryChunk(id=str(uuid.uuid4()), document_id=doc.id, chunk_index=idx, text=chunk_text, keywords=_keywords(chunk_text), metadata_json={"source_file_id": file.id}))
        created += 1
    db.commit()
    return {"indexed": True, "document_id": doc.id, "chunks": created, "engine": "keyword"}


@router.get("/search")
def search_memory(q: str = Query(""), limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    chunks = db.query(MemoryChunk, MemoryDocument).join(MemoryDocument, MemoryChunk.document_id == MemoryDocument.id).order_by(MemoryChunk.created_at.desc()).limit(500).all()
    q_lower = q.lower().strip()
    q_terms = [t for t in re.findall(r"[a-zA-Z0-9_]{3,}", q_lower)]
    results = []
    for chunk, doc in chunks:
        hay = f"{chunk.text} {chunk.keywords}".lower()
        score = sum(hay.count(term) for term in q_terms) if q_terms else 1
        if q_lower and q_lower in hay:
            score += 5
        if score > 0:
            idx = hay.find(q_lower) if q_lower and q_lower in hay else 0
            snippet = chunk.text[max(idx - 120, 0): idx + 520]
            results.append({"id": chunk.id, "document_id": doc.id, "title": doc.title, "chunk_index": chunk.chunk_index, "score": score, "snippet": snippet, "engine": "keyword"})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


@router.get("/documents")
def list_memory_documents(db: Session = Depends(get_db)):
    docs = db.query(MemoryDocument).order_by(MemoryDocument.created_at.desc()).limit(100).all()
    return [{"id": d.id, "title": d.title, "created_at": d.created_at, "chunks": len(d.chunks), "metadata_json": d.metadata_json} for d in docs]
