from pathlib import Path
from tools.base import BaseTool


class MarkdownReportTool(BaseTool):
    name = "markdown_report"
    description = "Writes a Markdown report to local storage."
    risk_level = "low"

    def execute(self, tool_input):
        storage = Path(tool_input.get("storage_dir", "storage")) / "reports"
        storage.mkdir(parents=True, exist_ok=True)
        safe_run = str(tool_input.get("run_id", "manual"))[:80]
        path = storage / f"{safe_run}.md"
        title = tool_input.get("title", "AgentForge Report")
        body = tool_input.get("body", "")
        path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
        return {"path": str(path), "bytes": path.stat().st_size}
