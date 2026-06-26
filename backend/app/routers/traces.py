from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import TraceSpan

router = APIRouter(tags=["traces"])


@router.get("/runs/{run_id}/traces")
def list_traces(run_id: str, db: Session = Depends(get_db)):
    return db.query(TraceSpan).filter(TraceSpan.run_id == run_id).order_by(TraceSpan.timestamp.asc()).all()


@router.get("/traces/{span_id}")
def get_trace(span_id: str, db: Session = Depends(get_db)):
    span = db.get(TraceSpan, span_id)
    if not span:
        raise HTTPException(404, "Trace span not found")
    return span
