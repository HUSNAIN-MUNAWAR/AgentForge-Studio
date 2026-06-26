from __future__ import annotations
from backend.app.database import SessionLocal
from backend.app.services.run_service import execute_run


def execute_run_job(run_id: str, file_ids: list[str] | None = None, resume: bool = False) -> dict:
    db = SessionLocal()
    try:
        execute_run(db, run_id, file_ids=file_ids or [], resume=resume)
        return {"run_id": run_id, "status": "done", "resume": resume}
    finally:
        db.close()
