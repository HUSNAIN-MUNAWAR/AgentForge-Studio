import uuid
import yaml
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from agent_engine.pack_schema import validate_pack_yaml
from backend.app.database import get_db
from backend.app.models import AgentPack, AgentPackRevision
from backend.app.schemas import PackCreate, PackOut, PackUpdate
from backend.app.services.seed import slugify

router = APIRouter(prefix="/packs", tags=["packs"])


def _bump_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    return f"{version}.1"


def _with_version(yaml_text: str, version: str) -> str:
    data = yaml.safe_load(yaml_text) or {}
    if isinstance(data, dict):
        data["version"] = version
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    return yaml_text


@router.get("", response_model=list[PackOut])
def list_packs(db: Session = Depends(get_db)):
    return db.query(AgentPack).order_by(AgentPack.name.asc()).all()


@router.post("", response_model=PackOut)
def create_pack(payload: PackCreate, db: Session = Depends(get_db)):
    pack_model = validate_pack_yaml(payload.yaml_text)
    slug = slugify(pack_model.name)
    if db.query(AgentPack).filter(AgentPack.slug == slug).first():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    item = AgentPack(
        id=str(uuid.uuid4()),
        name=pack_model.name,
        slug=slug,
        version=pack_model.version,
        description=pack_model.description,
        yaml_text=payload.yaml_text,
        active=payload.active,
    )
    db.add(item)
    db.flush()
    db.add(AgentPackRevision(id=str(uuid.uuid4()), pack_id=item.id, version=item.version, yaml_text=item.yaml_text, change_notes=payload.change_notes, changed_fields={"created": True}))
    db.commit()
    db.refresh(item)
    return item


@router.get("/{pack_id}", response_model=PackOut)
def get_pack(pack_id: str, db: Session = Depends(get_db)):
    item = db.get(AgentPack, pack_id)
    if not item:
        raise HTTPException(404, "Pack not found")
    return item


@router.put("/{pack_id}", response_model=PackOut)
def update_pack(pack_id: str, payload: PackUpdate, db: Session = Depends(get_db)):
    item = db.get(AgentPack, pack_id)
    if not item:
        raise HTTPException(404, "Pack not found")
    old_yaml = item.yaml_text
    old_version = item.version
    if payload.yaml_text is not None:
        yaml_text = payload.yaml_text
        parsed = validate_pack_yaml(yaml_text)
        new_version = _bump_patch(old_version) if payload.increment_version else parsed.version
        yaml_text = _with_version(yaml_text, new_version) if payload.increment_version else yaml_text
        pack_model = validate_pack_yaml(yaml_text)
        item.name = pack_model.name
        item.version = pack_model.version
        item.description = pack_model.description
        item.yaml_text = yaml_text
        db.add(AgentPackRevision(id=str(uuid.uuid4()), pack_id=item.id, version=item.version, yaml_text=item.yaml_text, change_notes=payload.change_notes, changed_fields={"yaml_changed": old_yaml != yaml_text, "previous_version": old_version}))
    if payload.active is not None:
        item.active = payload.active
    db.commit()
    db.refresh(item)
    return item


@router.get("/{pack_id}/revisions")
def list_revisions(pack_id: str, db: Session = Depends(get_db)):
    if not db.get(AgentPack, pack_id):
        raise HTTPException(404, "Pack not found")
    return db.query(AgentPackRevision).filter(AgentPackRevision.pack_id == pack_id).order_by(AgentPackRevision.created_at.desc()).all()


@router.delete("/{pack_id}")
def delete_pack(pack_id: str, db: Session = Depends(get_db)):
    item = db.get(AgentPack, pack_id)
    if not item:
        raise HTTPException(404, "Pack not found")
    db.delete(item)
    db.commit()
    return {"deleted": True}


@router.post("/import", response_model=PackOut)
def import_pack(payload: PackCreate, db: Session = Depends(get_db)):
    return create_pack(payload, db)


@router.get("/{pack_id}/export")
def export_pack(pack_id: str, db: Session = Depends(get_db)):
    item = db.get(AgentPack, pack_id)
    if not item:
        raise HTTPException(404, "Pack not found")
    return Response(content=item.yaml_text, media_type="application/x-yaml")


@router.post("/{pack_id}/validate")
def validate_pack(pack_id: str, db: Session = Depends(get_db)):
    item = db.get(AgentPack, pack_id)
    if not item:
        raise HTTPException(404, "Pack not found")
    pack = validate_pack_yaml(item.yaml_text)
    return {"valid": True, "name": pack.name, "version": pack.version, "agents": len(pack.agents), "tools": len(pack.tools), "workflow_type": pack.workflow.type}
