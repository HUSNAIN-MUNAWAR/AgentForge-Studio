from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    data: dict[str, Any]


class BaseTool:
    name: str = "base"
    description: str = "Base tool"
    risk_level: str = "low"
    permissions: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}

    def execute(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
