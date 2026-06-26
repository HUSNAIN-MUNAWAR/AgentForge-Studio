from dataclasses import dataclass
from typing import Any
import re


@dataclass
class PolicyDecision:
    decision: str
    reason: str
    rule_name: str | None = None


DEFAULT_RULES = [
    {"name": "Block destructive file delete", "match": {"tool": "file.delete"}, "decision": "block", "reason": "Destructive file deletion is disabled."},
    {"name": "Block email sending", "match": {"tool": "email.send"}, "decision": "block", "reason": "AgentForge only creates email drafts; it never sends email."},
    {"name": "Approval for GitHub issue creation", "match": {"tool": "github.issue_create"}, "decision": "require_human_approval", "reason": "External GitHub write actions require approval."},
    {"name": "Block secret reads", "match": {"tool": "secret.read"}, "decision": "block", "reason": "Secret access is not exposed to agent tools."},
    {"name": "Approval for external APIs", "match": {"tool": "external_api.call"}, "decision": "require_human_approval", "reason": "External calls require human approval."},
]


class PolicyEngine:
    def __init__(self, policies: Any, tool_permissions: dict[str, str] | None = None, max_steps: int | None = None, max_cost: float | None = None) -> None:
        self.policies = policies
        self.tool_permissions = tool_permissions or {}
        self.max_steps = max_steps
        self.max_cost = max_cost

    def decide(
        self,
        tool_name: str,
        risk_level: str,
        tool_input: dict | None = None,
        agent_id: str | None = None,
        action_type: str | None = None,
        current_step: int | None = None,
        current_cost: float | None = None,
    ) -> PolicyDecision:
        tool_input = tool_input or {}
        if self.max_steps is not None and current_step is not None and current_step > self.max_steps:
            return PolicyDecision("block", f"Max steps exceeded: {current_step}>{self.max_steps}", "limits.max_steps")
        if self.max_cost is not None and current_cost is not None and current_cost > self.max_cost:
            return PolicyDecision("block", f"Max cost exceeded: {current_cost:.4f}>{self.max_cost:.4f}", "limits.max_cost")
        if tool_name in set(getattr(self.policies, "blocked", []) or []):
            return PolicyDecision("block", f"Tool `{tool_name}` is blocked by pack policy", "pack.blocked")
        if self.tool_permissions.get(tool_name) == "block":
            return PolicyDecision("block", f"Tool `{tool_name}` is blocked in Tool Permissions", "tool.permission")

        for rule in [*DEFAULT_RULES, *(getattr(self.policies, "rules", []) or [])]:
            if self._matches(rule.get("match", {}), tool_name, risk_level, tool_input, agent_id, action_type):
                return PolicyDecision(rule.get("decision", "allow"), rule.get("reason", f"Matched rule {rule.get('name', 'unnamed')}"), rule.get("name"))

        if tool_name in set(getattr(self.policies, "require_approval", []) or []):
            return PolicyDecision("require_human_approval", f"Tool `{tool_name}` requires approval by pack policy", "pack.require_approval")
        if self.tool_permissions.get(tool_name) in {"approval", "require_human_approval"}:
            return PolicyDecision("require_human_approval", f"Tool `{tool_name}` requires approval in Tool Permissions", "tool.permission")
        if risk_level in {"high"}:
            return PolicyDecision("require_human_approval", f"High-risk tool `{tool_name}` requires approval", "default.high_risk")
        return PolicyDecision("allow", "Allowed by policy", "default.allow")

    def _matches(self, match: dict[str, Any], tool_name: str, risk_level: str, tool_input: dict, agent_id: str | None, action_type: str | None) -> bool:
        if match.get("tool") and match.get("tool") != tool_name:
            return False
        if match.get("risk_level") and match.get("risk_level") != risk_level:
            return False
        if match.get("agent_id") and match.get("agent_id") != agent_id:
            return False
        if match.get("action_type") and match.get("action_type") != action_type:
            return False
        if match.get("input_regex"):
            try:
                if not re.search(str(match["input_regex"]), str(tool_input), re.IGNORECASE):
                    return False
            except re.error:
                return False
        if match.get("max_file_size") is not None:
            size = tool_input.get("size_bytes") or tool_input.get("file_size") or 0
            try:
                return int(size) > int(match["max_file_size"])
            except Exception:
                return False
        return True
