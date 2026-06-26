import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_engine.evaluator import RuleBasedEvaluator
from agent_engine.pack_schema import validate_pack_yaml



def main():
    evaluator = RuleBasedEvaluator()
    total = passed = 0
    for pack_file in sorted((ROOT / "packs").glob("*/pack.yaml")):
        pack = validate_pack_yaml(pack_file.read_text(encoding="utf-8"))
        eval_file = pack_file.parent / (pack.evaluation.cases_file if pack.evaluation else "eval_cases.json")
        if not eval_file.exists():
            continue
        cases = json.loads(eval_file.read_text(encoding="utf-8"))
        for case in cases:
            result = evaluator.evaluate_static_case(case, used_tools=pack.tools, output_preview="")
            total += 1
            passed += 1 if result["passed"] else 0
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status} {pack.name}::{result['case_id']} {result['failures']}")
    print(json.dumps({"total": total, "passed": passed, "pass_rate": passed / total if total else 0}, indent=2))
    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
