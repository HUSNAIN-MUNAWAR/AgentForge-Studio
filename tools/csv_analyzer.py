import csv
from pathlib import Path
from statistics import mean
from tools.base import BaseTool


class CSVAnalyzerTool(BaseTool):
    name = "csv_analyzer"
    description = "Summarizes CSV columns, row count, missing values, and basic numeric stats."
    risk_level = "low"

    def execute(self, tool_input):
        path = Path(tool_input["path"])
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        columns = reader.fieldnames or []
        missing = {col: sum(1 for row in rows if not (row.get(col) or "").strip()) for col in columns}
        numeric_stats = {}
        for col in columns:
            values = []
            for row in rows:
                try:
                    values.append(float(row.get(col, "")))
                except ValueError:
                    pass
            if values:
                numeric_stats[col] = {"min": min(values), "max": max(values), "mean": mean(values)}
        samples = rows[:5]
        return {"path": str(path), "row_count": len(rows), "columns": columns, "missing_values": missing, "numeric_stats": numeric_stats, "sample_rows": samples}
