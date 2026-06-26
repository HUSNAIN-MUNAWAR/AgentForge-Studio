from tools.base import BaseTool


class EmailDraftTool(BaseTool):
    name = "email_draft"
    description = "Creates a local email draft text. It never sends email."
    risk_level = "medium"

    def execute(self, tool_input):
        recipient = tool_input.get("recipient", "recipient@example.com")
        context = tool_input.get("context", "")
        tone = tool_input.get("tone", "professional")
        draft = f"To: {recipient}\nSubject: Quick follow-up\n\nHi,\n\nI reviewed the context below and prepared this {tone} outreach draft.\n\n{context[:1200]}\n\nBest regards,\nAgentForge Studio"
        return {"draft": draft, "sent": False}
