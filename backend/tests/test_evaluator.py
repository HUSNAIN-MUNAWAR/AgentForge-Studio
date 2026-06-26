from agent_engine.evaluator import RuleBasedEvaluator


def test_evaluator_required_tools():
    case = {"case_id": "c1", "required_tools": ["csv_analyzer"], "expected_contains": []}
    result = RuleBasedEvaluator().evaluate_static_case(case, used_tools=["csv_analyzer"], output_preview="")
    assert result["passed"]
