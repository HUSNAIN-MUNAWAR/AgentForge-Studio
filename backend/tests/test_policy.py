from agent_engine.pack_schema import PoliciesConfig
from agent_engine.policy import PolicyEngine


def test_policy_block_and_approval():
    p = PoliciesConfig(require_approval=["email_draft"], blocked=["secret.read"])
    engine = PolicyEngine(p)
    assert engine.decide("secret.read", "high").decision == "block"
    assert engine.decide("email_draft", "medium").decision == "require_human_approval"
    assert engine.decide("file_reader", "low").decision == "allow"
