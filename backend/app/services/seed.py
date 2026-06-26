import uuid
from pathlib import Path
import yaml
from sqlalchemy.orm import Session
from agent_engine.pack_schema import validate_pack_yaml
from tools.registry import get_tool_registry
from backend.app.models import AgentPack, ToolDefinition

ROOT = Path(__file__).resolve().parents[3]


def slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-").replace("--", "-")


def seed_tool_definitions(db: Session) -> None:
    registry = get_tool_registry()
    for tool in registry.list_tools():
        existing = db.get(ToolDefinition, tool.name)
        if existing:
            continue
        db.add(ToolDefinition(
            name=tool.name,
            description=tool.description,
            enabled=True,
            risk_level=tool.risk_level,
            permission_status="approval" if tool.risk_level in {"medium", "high"} else "allow",
            config={},
        ))
    db.commit()


def seed_builtin_packs(db: Session) -> None:
    packs_dir = ROOT / "packs"
    if not packs_dir.exists():
        return
    for pack_file in packs_dir.glob("*/pack.yaml"):
        yaml_text = pack_file.read_text(encoding="utf-8")
        pack = validate_pack_yaml(yaml_text)
        slug = slugify(pack.name)
        existing = db.query(AgentPack).filter(AgentPack.slug == slug).first()
        if existing:
            continue
        db.add(AgentPack(
            id=str(uuid.uuid4()),
            name=pack.name,
            slug=slug,
            version=pack.version,
            description=pack.description,
            yaml_text=yaml_text,
            active=True,
            source_path=str(pack_file.relative_to(ROOT)),
        ))
    db.commit()
