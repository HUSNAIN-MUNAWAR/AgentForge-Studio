from pathlib import Path
from agent_engine.pack_schema import validate_pack_yaml


def test_builtin_packs_validate():
    root = Path(__file__).resolve().parents[2]
    packs = list((root / "packs").glob("*/pack.yaml"))
    assert len(packs) >= 5
    for pack_file in packs:
        pack = validate_pack_yaml(pack_file.read_text(encoding="utf-8"))
        assert pack.name
        assert pack.workflow.start in pack.workflow.nodes
