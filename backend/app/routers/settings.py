from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.database import get_db
from backend.app.models import AppSetting
from backend.app.schemas import AppSettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _settings_payload(db: Session) -> dict:
    settings = get_settings()
    runtime = db.get(AppSetting, "runtime")
    overrides = runtime.value if runtime else {}
    provider_type = overrides.get("provider_type", settings.llm_provider)
    return {
        "app_mode": settings.app_mode,
        "provider_type": provider_type,
        "provider_configured": bool(settings.openai_api_key) or provider_type in {"ollama", "mock"},
        "mock_mode_active": not bool(settings.openai_api_key) and provider_type == "openai_compatible",
        "base_url": overrides.get("base_url", settings.openai_base_url if provider_type == "openai_compatible" else settings.ollama_base_url),
        "model_name": overrides.get("model_name", settings.openai_model),
        "temperature": overrides.get("temperature", settings.llm_temperature),
        "max_tokens": overrides.get("max_tokens", settings.llm_max_tokens),
        "max_steps_per_run": overrides.get("max_steps_per_run", settings.max_steps_per_run),
        "max_cost_per_run_usd": overrides.get("max_cost_per_run_usd", settings.max_cost_per_run_usd),
        "queue_execution_mode": settings.queue_execution_mode,
        "stored_settings": overrides,
        "security_note": "API keys are read from backend environment variables and are not returned to the frontend.",
    }


@router.get("")
def get_app_settings(db: Session = Depends(get_db)):
    return _settings_payload(db)


@router.put("")
def update_runtime_settings(payload: AppSettingUpdate, db: Session = Depends(get_db)):
    value = payload.model_dump(exclude_none=True)
    item = db.get(AppSetting, "runtime")
    if not item:
        item = AppSetting(key="runtime", value=value)
        db.add(item)
    else:
        item.value = {**(item.value or {}), **value}
    db.commit()
    return _settings_payload(db)
