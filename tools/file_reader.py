from pathlib import Path
from tools.base import BaseTool


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Reads uploaded text, markdown, CSV, or log files as text."
    risk_level = "low"
    input_schema = {"path": "string"}
    output_schema = {"text_preview": "string", "bytes": "integer"}

    def execute(self, tool_input):
        path = Path(tool_input["path"])
        text = path.read_text(encoding="utf-8", errors="ignore")
        return {"path": str(path), "bytes": path.stat().st_size, "text_preview": text[:5000]}
