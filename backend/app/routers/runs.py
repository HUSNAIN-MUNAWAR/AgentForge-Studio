import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Run, AgentPack
from backend.app.schemas import RunCreate, RunOut
from backend.app.services.queue_service import enqueue_or_execute
from agent_engine.hashing import sha256_text
from agent_engine.pack_schema import validate_pack_yaml

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunOut)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    pack = db.get(AgentPack, payload.pack_id)
    if not pack:
        raise HTTPException(404, "Pack not found")
    parsed = validate_pack_yaml(pack.yaml_text)
    run = Run(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        pack_version=pack.version,
        input_text=payload.input_text,
        status="queued",
        model_provider=parsed.models.default_provider,
        model_name=parsed.models.default_model,
        tools_enabled=parsed.tools,
        input_hash=sha256_text(payload.input_text),
        file_ids=payload.file_ids,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue_or_execute(db, run, payload.file_ids)
    db.refresh(run)
    return run


@router.get("", response_model=list[RunOut])
def list_runs(db: Session = Depends(get_db)):
    return db.query(Run).order_by(Run.created_at.desc()).limit(100).all()


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/{run_id}/retry", response_model=RunOut)
def retry_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status not in {"failed", "stopped", "rejected"}:
        raise HTTPException(409, f"Cannot retry run with status {run.status}")
    run.retry_count += 1
    run.status = "queued"
    run.error_message = None
    db.commit()
    enqueue_or_execute(db, run, run.file_ids or [])
    db.refresh(run)
    return run


@router.post("/{run_id}/stop")
def stop_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status not in {"completed", "failed", "rejected"}:
        run.status = "stopped"
    db.commit()
    return {"status": run.status}


@router.get("/{run_id}/output")
def get_output(run_id: str, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {"run_id": run.id, "status": run.status, "output": run.final_output, "error": run.error_message}
