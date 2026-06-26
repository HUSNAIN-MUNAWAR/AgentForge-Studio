from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_engine.pack_schema import validate_pack_yaml



def main() -> int:
    errors = []
    for pack_file in sorted((ROOT / "packs").glob("*/pack.yaml")):
        try:
            pack = validate_pack_yaml(pack_file.read_text(encoding="utf-8"))
            print(f"OK {pack_file.relative_to(ROOT)} :: {pack.name} ({len(pack.agents)} agents, {len(pack.tools)} tools)")
        except Exception as exc:
            errors.append(f"{pack_file}: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
