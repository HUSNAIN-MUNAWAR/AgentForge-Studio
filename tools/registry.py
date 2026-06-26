from tools.base import BaseTool
from tools.file_reader import FileReaderTool
from tools.pdf_reader import PDFReaderTool
from tools.csv_analyzer import CSVAnalyzerTool
from tools.markdown_report import MarkdownReportTool
from tools.json_export import JSONExportTool
from tools.web_search import WebSearchTool
from tools.code_sandbox import CodeSandboxTool
from tools.email_draft import EmailDraftTool
from tools.github_issue_draft import GitHubIssueDraftTool
from tools.sql_query import SQLQueryTool
from tools.memory_search import MemorySearchTool


class ToolRegistry:
    def __init__(self, provider_settings: dict | None = None) -> None:
        provider_settings = provider_settings or {}
        self.tools: dict[str, BaseTool] = {}
        for tool in [
            FileReaderTool(),
            PDFReaderTool(),
            CSVAnalyzerTool(),
            MarkdownReportTool(),
            JSONExportTool(),
            WebSearchTool(provider_settings.get("web_search_endpoint", "")),
            CodeSandboxTool(),
            EmailDraftTool(),
            GitHubIssueDraftTool(),
            SQLQueryTool(),
            MemorySearchTool(),
        ]:
            self.tools[tool.name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.values())


def get_tool_registry(provider_settings: dict | None = None) -> ToolRegistry:
    return ToolRegistry(provider_settings)
