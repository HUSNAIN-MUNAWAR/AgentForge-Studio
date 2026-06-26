from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import ToolDefinition
from backend.app.schemas import ToolPermissionUpdate

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
def list_tools(db: Session = Depends(get_db)):
    return db.query(ToolDefinition).order_by(ToolDefinition.name.asc()).all()


@router.put("/{name}/permissions")
def update_permissions(name: str, payload: ToolPermissionUpdate, db: Session = Depends(get_db)):
    item = db.get(ToolDefinition, name)
    if not item:
        raise HTTPException(404, "Tool not found")
    if payload.enabled is not None:
        item.enabled = payload.enabled
    if payload.permission_status is not None:
        item.permission_status = payload.permission_status
    if payload.config is not None:
        item.config = payload.config
    db.commit()
    return item
