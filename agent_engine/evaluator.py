from typing import Any


class RuleBasedEvaluator:
    def evaluate_static_case(
        self,
        case: dict[str, Any],
        used_tools: list[str],
        output_preview: str,
        max_steps: int | None = None,
        policy_violations: int = 0,
        approval_triggered: bool = False,
    ) -> dict[str, Any]:
        failures: list[str] = []
        score = 100
        required_tools = case.get("required_tools", [])
        for tool in required_tools:
            if tool not in used_tools:
                failures.append(f"Required tool missing/not used: {tool}")
                score -= 25
        for token in case.get("expected_contains", []):
            if output_preview and token.lower() not in output_preview.lower():
                failures.append(f"Output preview missing expected token: {token}")
                score -= 10
        if case.get("max_steps") is not None:
            if case.get("max_steps", 999) <= 0:
                failures.append("max_steps must be positive")
                score -= 20
            elif max_steps is not None and max_steps > case["max_steps"]:
                failures.append(f"Step budget exceeded: {max_steps}>{case['max_steps']}")
                score -= 20
        if case.get("max_cost_usd") is not None and case.get("max_cost_usd", 0) < 0:
            failures.append("max_cost_usd must be non-negative")
            score -= 10
        if policy_violations > 0:
            failures.append(f"Policy violations detected: {policy_violations}")
            score -= 25
        if case.get("approval_expected") is True and not approval_triggered:
            failures.append("Expected human approval was not triggered")
            score -= 15
        score = max(score, 0)
        return {
            "case_id": case.get("case_id", "unknown"),
            "passed": not failures,
            "score": score,
            "failures": failures,
            "required_tools": required_tools,
            "tools_used": used_tools,
            "expected_contains": case.get("expected_contains", []),
            "steps": max_steps,
            "approval_expected": case.get("approval_expected", False),
        }
