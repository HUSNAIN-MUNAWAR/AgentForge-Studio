import httpx
from tools.base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Optional web search interface. Disabled unless WEB_SEARCH_ENDPOINT is configured."
    risk_level = "medium"

    def __init__(self, endpoint: str = "") -> None:
        self.endpoint = endpoint

    def execute(self, tool_input):
        if not self.endpoint:
            return {"disabled": True, "reason": "WEB_SEARCH_ENDPOINT is not configured", "query": tool_input.get("query")}
        with httpx.Client(timeout=15) as client:
            resp = client.post(self.endpoint, json={"query": tool_input.get("query", "")})
            resp.raise_for_status()
            return resp.json()
