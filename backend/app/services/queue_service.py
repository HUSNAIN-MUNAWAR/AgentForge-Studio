from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models import Run
from backend.app.queue.rq_queue import enqueue_run_job
from backend.app.services.run_service import execute_run


def enqueue_or_execute(db: Session, run: Run, file_ids: list[str] | None = None, resume: bool = False) -> Run:
    result = enqueue_run_job(run.id, file_ids or [], resume=resume)
    run.queue_name = result.queue_name
    run.job_id = result.job_id
    run.queued_at = datetime.utcnow()
    if result.enqueued:
        run.status = "queued"
        db.commit()
        return run
    db.commit()
    execute_run(db, run.id, file_ids=file_ids or [], resume=resume)
    db.refresh(run)
    return run
