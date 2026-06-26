import sqlite3
from pathlib import Path
from tools.base import BaseTool


class SQLQueryTool(BaseTool):
    name = "sql_query"
    description = "Read-only SQL query tool for SQLite sample databases."
    risk_level = "medium"

    def execute(self, tool_input):
        query = tool_input.get("query", "")
        if not query.strip().lower().startswith("select"):
            return {"error": "Only SELECT queries are allowed"}
        db_path = tool_input.get("db_path")
        if not db_path:
            return {"error": "No SQLite db_path configured"}
        conn = sqlite3.connect(str(Path(db_path)))
        try:
            rows = conn.execute(query).fetchmany(50)
            return {"rows": rows, "row_count": len(rows)}
        finally:
            conn.close()
