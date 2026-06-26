import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import AgentPack, EvaluationRun
from backend.app.schemas import EvalRunCreate, EvalRunOut
from backend.app import metrics
from agent_engine.evaluator import RuleBasedEvaluator
from agent_engine.pack_schema import validate_pack_yaml

router = APIRouter(prefix="/evals", tags=["evaluations"])


@router.post("/run", response_model=EvalRunOut)
def run_eval(payload: EvalRunCreate, db: Session = Depends(get_db)):
    pack_row = db.get(AgentPack, payload.pack_id)
    if not pack_row:
        raise HTTPException(404, "Pack not found")
    pack = validate_pack_yaml(pack_row.yaml_text)
    cases = payload.cases or []
    if not cases and pack_row.source_path:
        eval_path = Path(pack_row.source_path).parent / (pack.evaluation.cases_file if pack.evaluation else "eval_cases.json")
        eval_file = Path.cwd() / eval_path
        if eval_file.exists():
            cases = json.loads(eval_file.read_text(encoding="utf-8"))
    evaluator = RuleBasedEvaluator()
    results = []
    for case in cases:
        result = evaluator.evaluate_static_case(
            case,
            used_tools=pack.tools,
            output_preview="",
            max_steps=None,
            policy_violations=0,
            approval_triggered=bool(pack.policies.require_approval),
        )
        results.append(result)
        metrics.evals_total.labels(status="passed" if result["passed"] else "failed").inc()
    passed = sum(1 for r in results if r["passed"])
    summary = {"total": len(results), "passed": passed, "failed": len(results) - passed, "pass_rate": (passed / len(results)) if results else 0, "pack_version": pack_row.version}
    item = EvaluationRun(id=str(uuid.uuid4()), pack_id=pack_row.id, pack_version=pack_row.version, status="completed", summary=summary, results=results)
    db.add(item)
    db.commit()
    return item


@router.get("", response_model=list[EvalRunOut])
def list_evals(db: Session = Depends(get_db)):
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(50).all()


@router.get("/{eval_id}", response_model=EvalRunOut)
def get_eval(eval_id: str, db: Session = Depends(get_db)):
    item = db.get(EvaluationRun, eval_id)
    if not item:
        raise HTTPException(404, "Evaluation not found")
    return item


@router.get("/{eval_id}/report.md")
def export_eval_markdown(eval_id: str, db: Session = Depends(get_db)):
    item = db.get(EvaluationRun, eval_id)
    if not item:
        raise HTTPException(404, "Evaluation not found")
    lines = [
        "# AgentForge Evaluation Report", "", f"Eval ID: `{item.id}`", f"Pack ID: `{item.pack_id}`",
        f"Pack version: `{item.pack_version}`", "", "| Case | Status | Score | Failure Reason | Steps | Tools Used |",
        "|---|---:|---:|---|---:|---|"
    ]
    for r in item.results:
        failures = "; ".join(r.get("failures", [])) or "—"
        tools = ", ".join(r.get("tools_used", []))
        lines.append(f"| {r.get('case_id')} | {'PASS' if r.get('passed') else 'FAIL'} | {r.get('score', 0)} | {failures} | {r.get('steps', '—')} | {tools} |")
    return Response("\n".join(lines), media_type="text/markdown")
