from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import ApprovalRequest, Run, TraceSpan
from backend.app.schemas import ApprovalAction
from backend.app.services.queue_service import enqueue_or_execute
from backend.app import metrics
import uuid

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).all()


@router.post("/{approval_id}/approve")
def approve(approval_id: str, payload: ApprovalAction | None = None, db: Session = Depends(get_db)):
    item = db.get(ApprovalRequest, approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    item.status = "approved"
    item.resolved_at = datetime.utcnow()
    if payload and payload.edited_tool_input:
        item.tool_input = payload.edited_tool_input
    run = db.get(Run, item.run_id)
    if run and run.status == "waiting_approval":
        run.status = "queued"
        db.add(TraceSpan(span_id=str(uuid.uuid4()), run_id=run.id, event_type="approval_decision", agent_id=item.agent_id, tool_name=item.tool_name, tool_input=item.tool_input, policy_decision="approved", risk_level=item.risk_level, output_summary="Human approved tool action; run queued for resume."))
        db.commit()
        metrics.approvals_total.labels(status="approved").inc()
        enqueue_or_execute(db, run, run.file_ids or [], resume=True)
    else:
        db.commit()
    return {"status": item.status, "run_status": run.status if run else None}


@router.post("/{approval_id}/reject")
def reject(approval_id: str, db: Session = Depends(get_db)):
    item = db.get(ApprovalRequest, approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    item.status = "rejected"
    item.resolved_at = datetime.utcnow()
    run = db.get(Run, item.run_id)
    if run and run.status == "waiting_approval":
        run.status = "rejected"
        run.error_message = f"Human rejected approval for {item.tool_name}"
        run.finished_at = datetime.utcnow()
        db.add(TraceSpan(span_id=str(uuid.uuid4()), run_id=run.id, event_type="approval_decision", agent_id=item.agent_id, tool_name=item.tool_name, tool_input=item.tool_input, policy_decision="rejected", risk_level=item.risk_level, status="blocked", output_summary="Human rejected tool action; run stopped."))
    db.commit()
    metrics.approvals_total.labels(status="rejected").inc()
    return {"status": item.status, "run_status": run.status if run else None}
