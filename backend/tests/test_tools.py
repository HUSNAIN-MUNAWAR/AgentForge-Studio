from pathlib import Path
from tools.csv_analyzer import CSVAnalyzerTool


def test_csv_analyzer_sample_data():
    root = Path(__file__).resolve().parents[2]
    result = CSVAnalyzerTool().execute({"path": str(root / "sample_data" / "customer_feedback.csv")})
    assert result["row_count"] >= 3
    assert "columns" in result
