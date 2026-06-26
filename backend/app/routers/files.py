import re
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.database import get_db
from backend.app.models import UploadedFile

router = APIRouter(prefix="/files", tags=["files"])
STORAGE = Path("storage/uploads")
STORAGE.mkdir(parents=True, exist_ok=True)


def safe_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    return clean or "upload.txt"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
    fid = str(uuid.uuid4())
    stored = STORAGE / f"{fid}_{safe_name(file.filename or 'upload')}"
    stored.write_bytes(raw)
    item = UploadedFile(id=fid, original_name=file.filename or "upload", stored_path=str(stored), content_type=file.content_type or "application/octet-stream", size_bytes=len(raw))
    db.add(item)
    db.commit()
    return item


@router.get("")
def list_files(db: Session = Depends(get_db)):
    return db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).all()


@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    item = db.get(UploadedFile, file_id)
    if not item:
        raise HTTPException(404, "File not found")
    try:
        Path(item.stored_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(item)
    db.commit()
    return {"deleted": True}
