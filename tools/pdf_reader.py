from pathlib import Path
from tools.base import BaseTool


class PDFReaderTool(BaseTool):
    name = "pdf_reader"
    description = "Extracts text from PDF files using pypdf when available."
    risk_level = "low"

    def execute(self, tool_input):
        path = Path(tool_input["path"])
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return {"path": str(path), "pages": len(reader.pages), "text_preview": text[:5000]}
        except Exception as exc:
            return {"path": str(path), "error": str(exc), "text_preview": ""}
