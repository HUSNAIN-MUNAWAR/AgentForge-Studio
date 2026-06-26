import json
import subprocess
import sys
import tempfile
from pathlib import Path
from tools.base import BaseTool


class CodeSandboxTool(BaseTool):
    name = "code_sandbox"
    description = "Runs a small Python snippet in a subprocess with timeout. Local demo only."
    risk_level = "medium"

    def execute(self, tool_input):
        code = tool_input.get("code", "")
        timeout = int(tool_input.get("timeout_seconds", 2))
        wrapper = """
import json
result = None
{code}
print(json.dumps({{"result": result}}))
""".format(code=code)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snippet.py"
            path.write_text(wrapper, encoding="utf-8")
            proc = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=timeout)
        return {"returncode": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
