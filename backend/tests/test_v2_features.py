from pathlib import Path

from agent_engine.policy import PolicyEngine
from agent_engine.pack_schema import PoliciesConfig
from agent_engine.runner import AgentGraphRunner, RunContext
from agent_engine.pack_schema import validate_pack_yaml
from tools.memory_search import MemorySearchTool


def test_policy_regex_block():
    policy = PolicyEngine(PoliciesConfig(rules=[{
        "name": "Block private key text",
        "match": {"tool": "file_reader", "input_regex": "private[_ -]?key"},
        "decision": "block"
    }]))
    decision = policy.decide("file_reader", "low", {"query": "read private key"})
    assert decision.decision == "block"


def test_tool_permissions_force_approval():
    policy = PolicyEngine(PoliciesConfig(), tool_permissions={"email_draft": "require_human_approval"})
    decision = policy.decide("email_draft", "medium", {"recipient": "a@example.com"})
    assert decision.decision == "require_human_approval"


def test_memory_search_tool_returns_ranked_chunks():
    tool = MemorySearchTool()
    result = tool.execute({
        "query": "battery complaint",
        "limit": 2,
        "memory_corpus": [
            {"chunk_id": "1", "title": "a", "text": "shipping delay", "metadata": {}},
            {"chunk_id": "2", "title": "b", "text": "battery complaint severity high", "metadata": {}},
        ],
    })
    assert result["results"][0]["chunk_id"] == "2"


def test_runner_pauses_for_approval():
    research_pack = validate_pack_yaml(Path("packs/research_team/pack.yaml").read_text())
    traces = []
    approvals = []
    context = RunContext(
        run_id="test-run",
        user_input="draft outreach",
        uploaded_files=[],
        storage_dir=Path("storage"),
        provider_settings={"app_mode": "test", "llm_provider": "mock"},
        trace_writer=traces.append,
        approval_writer=lambda req: approvals.append(req) or "approval-1",
        tool_permissions={"web_search": "require_human_approval"},
    )
    result = AgentGraphRunner().run(research_pack, context)
    assert result.waiting_for_approval is True
    assert approvals
    assert any(t.get("event_type") == "approval_created" for t in traces)
