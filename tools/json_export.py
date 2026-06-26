import json
from pathlib import Path
from tools.base import BaseTool


class JSONExportTool(BaseTool):
    name = "json_export"
    description = "Exports structured data as JSON to local storage."
    risk_level = "low"

    def execute(self, tool_input):
        storage = Path(tool_input.get("storage_dir", "storage")) / "exports"
        storage.mkdir(parents=True, exist_ok=True)
        safe_run = str(tool_input.get("run_id", "manual"))[:80]
        path = storage / f"{safe_run}.json"
        payload = tool_input.get("payload", {})
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"path": str(path), "keys": list(payload.keys()) if isinstance(payload, dict) else []}
