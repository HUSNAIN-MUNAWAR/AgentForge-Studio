from tools.base import BaseTool


class GitHubIssueDraftTool(BaseTool):
    name = "github_issue_draft"
    description = "Creates a local GitHub issue draft. It does not call GitHub unless extended."
    risk_level = "medium"

    def execute(self, tool_input):
        return {"title": tool_input.get("title", "Issue draft"), "body": tool_input.get("body", ""), "created_remote": False}
