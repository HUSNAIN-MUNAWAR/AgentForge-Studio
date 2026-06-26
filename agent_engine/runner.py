from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
import time
import uuid

from agent_engine.pack_schema import AgentPack, AgentConfig
from agent_engine.policy import PolicyEngine
from agent_engine.providers import provider_from_settings
from tools.registry import get_tool_registry


@dataclass
class RunContext:
    run_id: str
    user_input: str
    uploaded_files: list[dict[str, Any]]
    storage_dir: Path
    provider_settings: dict[str, Any]
    trace_writer: Callable[[dict[str, Any]], None]
    approval_writer: Callable[[dict[str, Any]], str]
    memory_corpus: list[dict[str, Any]] = field(default_factory=list)
    approved_tool_inputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    rejected_tools: set[str] = field(default_factory=set)
    max_steps: int = 32
    max_cost: float = 1.0
    tool_permissions: dict[str, str] = field(default_factory=dict)


@dataclass
class RunResult:
    output: str
    waiting_for_approval: bool = False
    error: str | None = None
    cost_estimate: float = 0.0
    used_tools: list[str] = field(default_factory=list)
    steps: int = 0


class AgentGraphRunner:
    def run(self, pack: AgentPack, context: RunContext) -> RunResult:
        registry = get_tool_registry(context.provider_settings)
        provider = provider_from_settings(pack.models.default_provider, context.provider_settings)
        policy = PolicyEngine(pack.policies, tool_permissions=context.tool_permissions, max_steps=context.max_steps, max_cost=context.max_cost)
        outputs: dict[str, str] = {}
        tool_outputs: dict[str, Any] = {}
        used_tools: list[str] = []
        cost = 0.0
        step = 0

        self._trace(context, event_type="workflow_started", input_summary=context.user_input[:500], output_summary=f"Workflow type: {pack.workflow.type}")

        for node_id in self._ordered_nodes(pack):
            step += 1
            if step > context.max_steps:
                self._trace(context, event_type="policy_check", policy_decision="block", status="blocked", output_summary="Max step limit reached")
                return RunResult(output=self._compose_output(outputs, tool_outputs), error="Max step limit reached", cost_estimate=cost, used_tools=used_tools, steps=step)

            agent = next(a for a in pack.agents if a.id == node_id)
            tool_context = self._maybe_run_tools(pack, agent, context, registry, policy, used_tools, step, cost)
            tool_outputs.update(tool_context.get("outputs", {}))
            if tool_context.get("waiting_for_approval"):
                return RunResult(output=self._compose_output(outputs, tool_outputs, pending_approval=True), waiting_for_approval=True, used_tools=used_tools, steps=step)

            user_prompt = self._build_agent_prompt(pack, agent, context.user_input, outputs, tool_outputs)
            start = time.perf_counter()
            llm_result = provider.generate(agent.system_prompt, user_prompt, model=pack.models.default_model)
            latency = int((time.perf_counter() - start) * 1000)
            outputs[agent.id] = llm_result.text
            cost += llm_result.cost_estimate
            self._trace(
                context,
                event_type="agent_step",
                agent_id=agent.id,
                node_id=agent.id,
                input_summary=user_prompt[:600],
                output_summary=llm_result.text[:1200],
                latency_ms=latency,
                token_usage=llm_result.token_usage,
                cost_estimate=llm_result.cost_estimate,
            )

        final = self._compose_output(outputs, tool_outputs)
        if "markdown_report" in pack.tools:
            report = registry.get("markdown_report").execute({"title": pack.name, "body": final, "run_id": context.run_id, "storage_dir": str(context.storage_dir)})
            used_tools.append("markdown_report")
            self._trace(context, event_type="tool_call", tool_name="markdown_report", tool_input={"title": pack.name}, tool_output=report, policy_decision="allow", risk_level="low", output_summary=str(report)[:800])
            final += f"\n\nReport saved: `{report.get('path')}`"
        self._trace(context, event_type="workflow_completed", output_summary=final[:1200])
        return RunResult(output=final, cost_estimate=cost, used_tools=used_tools, steps=step)

    def _ordered_nodes(self, pack: AgentPack) -> list[str]:
        if pack.workflow.type in {"parallel_research"}:
            return pack.workflow.nodes
        ordered = [pack.workflow.start]
        current = pack.workflow.start
        seen = {current}
        edge_map = {edge.from_: edge.to for edge in pack.workflow.edges}
        while current in edge_map and edge_map[current] not in seen:
            current = edge_map[current]
            ordered.append(current)
            seen.add(current)
        for node in pack.workflow.nodes:
            if node not in seen:
                ordered.append(node)
        return ordered

    def _maybe_run_tools(self, pack: AgentPack, agent: AgentConfig, context: RunContext, registry, policy: PolicyEngine, used_tools: list[str], step: int, cost: float) -> dict[str, Any]:
        outputs: dict[str, Any] = {}
        requested = [tool for tool in agent.tools if tool in pack.tools]
        for tool_name in requested:
            tool = registry.get(tool_name)
            if not tool:
                self._trace(context, event_type="tool_missing", agent_id=agent.id, tool_name=tool_name, status="error", error_message="Tool not registered")
                continue
            tool_input = self._input_for_tool(tool_name, context)
            approval_key = f"{agent.id}:{tool_name}"
            if approval_key in context.rejected_tools:
                self._trace(context, event_type="tool_blocked", agent_id=agent.id, tool_name=tool_name, tool_input=tool_input, policy_decision="rejected", risk_level=tool.risk_level, status="blocked", output_summary="Human rejected approval request")
                continue
            if approval_key in context.approved_tool_inputs:
                tool_input = context.approved_tool_inputs[approval_key] or tool_input
                decision_text = "allow_after_approval"
            else:
                decision = policy.decide(tool_name, tool.risk_level, tool_input, agent_id=agent.id, action_type="tool_call", current_step=step, current_cost=cost)
                decision_text = decision.decision
                self._trace(context, event_type="policy_check", agent_id=agent.id, tool_name=tool_name, tool_input=tool_input, policy_decision=decision.decision, risk_level=tool.risk_level, output_summary=decision.reason)
                if decision.decision == "block":
                    self._trace(context, event_type="tool_blocked", agent_id=agent.id, tool_name=tool_name, tool_input=tool_input, policy_decision="block", risk_level=tool.risk_level, status="blocked", output_summary=decision.reason)
                    continue
                if decision.decision == "require_human_approval":
                    approval_id = context.approval_writer({
                        "agent_id": agent.id,
                        "tool_name": tool_name,
                        "requested_action": f"Execute {tool_name}",
                        "reason": decision.reason,
                        "tool_input": tool_input,
                        "risk_level": tool.risk_level,
                        "policy_rule": decision.rule_name or "",
                    })
                    self._trace(context, event_type="approval_created", agent_id=agent.id, tool_name=tool_name, tool_input=tool_input, policy_decision="require_human_approval", risk_level=tool.risk_level, output_summary=f"Approval request {approval_id} created")
                    return {"outputs": outputs, "waiting_for_approval": True}
            start = time.perf_counter()
            result = tool.execute(tool_input)
            latency = int((time.perf_counter() - start) * 1000)
            used_tools.append(tool_name)
            outputs[tool_name] = result
            self._trace(context, event_type="tool_call", agent_id=agent.id, tool_name=tool_name, tool_input=tool_input, tool_output=result, policy_decision=decision_text, risk_level=tool.risk_level, latency_ms=latency, output_summary=str(result)[:1200])
        return {"outputs": outputs, "waiting_for_approval": False}

    def _input_for_tool(self, tool_name: str, context: RunContext) -> dict[str, Any]:
        first_file = context.uploaded_files[0] if context.uploaded_files else None
        if tool_name in {"file_reader", "pdf_reader", "csv_analyzer"}:
            path = first_file["path"] if first_file else "sample_data/customer_feedback.csv"
            return {"path": path, "size_bytes": first_file.get("size_bytes", 0) if first_file else 0}
        if tool_name == "memory.search":
            return {"query": context.user_input[:250], "memory_corpus": context.memory_corpus, "limit": 5}
        if tool_name == "code_sandbox":
            return {"code": "result = {'message': 'sandbox executed', 'rows': 0}", "timeout_seconds": 2}
        if tool_name == "email_draft":
            return {"recipient": "lead@example.com", "context": context.user_input, "tone": "professional"}
        if tool_name == "github_issue_draft":
            return {"title": "Agent-generated issue draft", "body": context.user_input}
        if tool_name == "web_search":
            return {"query": context.user_input[:200]}
        if tool_name == "json_export":
            return {"payload": {"input": context.user_input}, "run_id": context.run_id, "storage_dir": str(context.storage_dir)}
        if tool_name == "sql_query":
            return {"query": "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"}
        return {"input": context.user_input}

    def _build_agent_prompt(self, pack: AgentPack, agent: AgentConfig, user_input: str, outputs: dict[str, str], tool_outputs: dict[str, Any]) -> str:
        prior = "\n\n".join(f"## {k}\n{v}" for k, v in outputs.items())[-5000:]
        tools = "\n".join(f"- {k}: {str(v)[:1200]}" for k, v in tool_outputs.items())
        return f"""
Pack: {pack.name} v{pack.version}
Agent: {agent.name}
Role: {agent.role}
Goal: {agent.goal}

User task:
{user_input}

Tool results:
{tools or 'No tool results yet.'}

Previous agent outputs:
{prior or 'No previous agent outputs yet.'}

Return an actionable, structured answer for your part of the workflow.
""".strip()

    def _compose_output(self, outputs: dict[str, str], tool_outputs: dict[str, Any], pending_approval: bool = False) -> str:
        lines = ["# AgentForge Run Output"]
        if pending_approval:
            lines.append("\n**Status:** Waiting for human approval before continuing a risky action.")
        if tool_outputs:
            lines.append("\n## Tool Results")
            for name, result in tool_outputs.items():
                lines.append(f"\n### {name}\n```json\n{result}\n```")
        for agent_id, text in outputs.items():
            lines.append(f"\n## {agent_id}\n{text}")
        return "\n".join(lines)

    def _trace(self, context: RunContext, **event: Any) -> None:
        event.setdefault("span_id", str(uuid.uuid4()))
        context.trace_writer(event)
