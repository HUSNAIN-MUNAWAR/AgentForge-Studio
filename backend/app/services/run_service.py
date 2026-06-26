import asyncio
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from agent_engine.hashing import sha256_text
from agent_engine.pack_schema import validate_pack_yaml
from agent_engine.runner import AgentGraphRunner, RunContext
from backend.app.core.config import get_settings
from backend.app.models import AgentPack, ApprovalRequest, AppSetting, MemoryChunk, MemoryDocument, Run, TraceSpan, ToolDefinition, UploadedFile
from backend.app.services.event_bus import event_bus
from backend.app import metrics

logger = logging.getLogger("agentforge.run_service")


def _publish(run_id: str, payload: dict) -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(event_bus.publish(run_id, payload))
        else:
            loop.run_until_complete(event_bus.publish(run_id, payload))
    except RuntimeError:
        asyncio.run(event_bus.publish(run_id, payload))


def _memory_corpus(db: Session) -> list[dict]:
    rows = db.query(MemoryChunk, MemoryDocument).join(MemoryDocument, MemoryChunk.document_id == MemoryDocument.id).order_by(MemoryChunk.created_at.desc()).limit(500).all()
    return [
        {
            "document_id": doc.id,
            "chunk_id": chunk.id,
            "title": doc.title,
            "text": chunk.text,
            "metadata": {**(chunk.metadata_json or {}), "chunk_index": chunk.chunk_index},
        }
        for chunk, doc in rows
    ]


def _tool_permissions(db: Session) -> dict[str, str]:
    rows = db.query(ToolDefinition).all()
    permissions: dict[str, str] = {}
    for tool in rows:
        if not tool.enabled:
            permissions[tool.name] = "block"
        elif tool.permission_status == "approval":
            permissions[tool.name] = "require_human_approval"
        else:
            permissions[tool.name] = tool.permission_status or "allow"
    return permissions


def _approval_maps(db: Session, run_id: str) -> tuple[dict[str, dict], set[str]]:
    approvals = db.query(ApprovalRequest).filter(ApprovalRequest.run_id == run_id).all()
    approved: dict[str, dict] = {}
    rejected: set[str] = set()
    for item in approvals:
        key = f"{item.agent_id}:{item.tool_name}"
        if item.status == "approved":
            approved[key] = item.tool_input
        elif item.status == "rejected":
            rejected.add(key)
    return approved, rejected


def execute_run(db: Session, run_id: str, file_ids: list[str] | None = None, resume: bool = False) -> None:
    run = db.get(Run, run_id)
    if not run:
        return
    pack_row = db.get(AgentPack, run.pack_id)
    if not pack_row:
        run.status = "failed"
        run.error_message = "Pack not found"
        db.commit()
        return

    run.status = "running"
    run.started_at = run.started_at or datetime.utcnow()
    db.commit()
    logger.info("run started", extra={"run_id": run.id, "trace_id": run.id})
    _publish(run.id, {"event_type": "run_started", "run_id": run.id, "resume": resume})

    settings = get_settings()
    runtime = db.get(AppSetting, "runtime")
    runtime_settings = runtime.value if runtime else {}
    pack = validate_pack_yaml(pack_row.yaml_text)
    files = []
    source_file_ids = file_ids or run.file_ids or []
    for fid in source_file_ids:
        f = db.get(UploadedFile, fid)
        if f:
            files.append({"id": f.id, "path": f.stored_path, "name": f.original_name, "size_bytes": f.size_bytes})

    def trace_writer(event: dict) -> None:
        span_id = event.get("span_id", str(uuid.uuid4()))
        span = TraceSpan(
            span_id=span_id,
            run_id=run.id,
            parent_span_id=event.get("parent_span_id"),
            agent_id=event.get("agent_id"),
            node_id=event.get("node_id"),
            event_type=event.get("event_type", "event"),
            input_summary=event.get("input_summary", ""),
            output_summary=event.get("output_summary", ""),
            tool_name=event.get("tool_name"),
            tool_input=event.get("tool_input", {}),
            tool_output=event.get("tool_output", {}),
            policy_decision=event.get("policy_decision"),
            risk_level=event.get("risk_level"),
            latency_ms=event.get("latency_ms", 0),
            token_usage=event.get("token_usage", {}),
            cost_estimate=event.get("cost_estimate", 0.0),
            status=event.get("status", "ok"),
            error_message=event.get("error_message"),
        )
        db.add(span)
        db.commit()
        if span.tool_name and span.event_type == "tool_call":
            metrics.tool_calls_total.labels(tool=span.tool_name, status=span.status).inc()
        if span.event_type == "policy_check" and span.policy_decision:
            metrics.policy_decisions_total.labels(decision=span.policy_decision).inc()
        logger.info(span.event_type, extra={"run_id": run.id, "trace_id": run.id, "span_id": span_id})
        _publish(run.id, {**event, "span_id": span_id, "run_id": run.id})

    def approval_writer(request: dict) -> str:
        existing = db.query(ApprovalRequest).filter(
            ApprovalRequest.run_id == run.id,
            ApprovalRequest.agent_id == request.get("agent_id"),
            ApprovalRequest.tool_name == request["tool_name"],
            ApprovalRequest.status == "pending",
        ).first()
        if existing:
            return existing.id
        approval = ApprovalRequest(
            id=str(uuid.uuid4()),
            run_id=run.id,
            agent_id=request.get("agent_id"),
            tool_name=request["tool_name"],
            requested_action=request.get("requested_action", "Tool execution requested"),
            reason=request.get("reason", "Policy requires human approval"),
            tool_input=request.get("tool_input", {}),
            risk_level=request.get("risk_level", "medium"),
            policy_rule=request.get("policy_rule", ""),
        )
        db.add(approval)
        db.commit()
        metrics.approvals_total.labels(status="requested").inc()
        _publish(run.id, {"event_type": "approval_required", "approval_id": approval.id, "tool_name": approval.tool_name})
        return approval.id

    start = time.perf_counter()
    try:
        approved, rejected = _approval_maps(db, run.id)
        context = RunContext(
            run_id=run.id,
            user_input=run.input_text,
            uploaded_files=files,
            storage_dir=Path("storage"),
            provider_settings={
                "openai_api_key": settings.openai_api_key,
                "openai_base_url": runtime_settings.get("base_url", settings.openai_base_url),
                "openai_model": runtime_settings.get("model_name", settings.openai_model),
                "ollama_base_url": settings.ollama_base_url,
                "web_search_endpoint": settings.web_search_endpoint,
                "app_mode": settings.app_mode,
                "llm_provider": runtime_settings.get("provider_type", settings.llm_provider),
                "llm_temperature": runtime_settings.get("temperature", settings.llm_temperature),
                "llm_max_tokens": runtime_settings.get("max_tokens", settings.llm_max_tokens),
            },
            trace_writer=trace_writer,
            approval_writer=approval_writer,
            memory_corpus=_memory_corpus(db),
            approved_tool_inputs=approved,
            rejected_tools=rejected,
            max_steps=runtime_settings.get("max_steps_per_run", settings.max_steps_per_run),
            max_cost=runtime_settings.get("max_cost_per_run_usd", settings.max_cost_per_run_usd),
            tool_permissions=_tool_permissions(db),
        )
        result = AgentGraphRunner().run(pack, context)
        run.final_output = result.output
        run.status = "waiting_approval" if result.waiting_for_approval else ("failed" if result.error else "completed")
        run.error_message = result.error
        run.output_hash = sha256_text(run.final_output or "")
        run.cost_estimate = result.cost_estimate
        run.latency_ms = int((time.perf_counter() - start) * 1000)
        if run.status != "waiting_approval":
            run.finished_at = datetime.utcnow()
        db.commit()
        metrics.runs_total.labels(status=run.status).inc()
        metrics.run_duration.labels(status=run.status).observe(max(run.latency_ms / 1000, 0))
        _publish(run.id, {"event_type": "run_finished", "status": run.status, "output_preview": (run.final_output or "")[:500]})
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.utcnow()
        db.commit()
        metrics.runs_total.labels(status="failed").inc()
        trace_writer({"event_type": "error", "status": "error", "error_message": str(exc)})
        logger.exception("run failed", extra={"run_id": run.id, "trace_id": run.id})
