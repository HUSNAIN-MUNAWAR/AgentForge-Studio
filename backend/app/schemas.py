from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field


class PackCreate(BaseModel):
    yaml_text: str
    active: bool = True
    change_notes: str = "Initial import"


class PackUpdate(BaseModel):
    yaml_text: str | None = None
    active: bool | None = None
    change_notes: str = "Updated in AgentForge Studio"
    increment_version: bool = True


class PackOut(BaseModel):
    id: str
    name: str
    slug: str
    version: str
    description: str
    active: bool
    yaml_text: str | None = None

    model_config = {"from_attributes": True}


class RunCreate(BaseModel):
    pack_id: str
    input_text: str
    file_ids: list[str] = Field(default_factory=list)


class RunOut(BaseModel):
    id: str
    pack_id: str
    pack_version: str
    input_text: str
    status: str
    final_output: str | None = None
    error_message: str | None = None
    model_provider: str
    model_name: str
    latency_ms: int = 0
    cost_estimate: float = 0.0
    job_id: str | None = None
    queue_name: str | None = None
    retry_count: int = 0

    model_config = {"from_attributes": True}


class ToolPermissionUpdate(BaseModel):
    enabled: bool | None = None
    permission_status: str | None = Field(None, pattern="^(allow|block|approval)$")
    config: dict[str, Any] | None = None


class EvalRunCreate(BaseModel):
    pack_id: str
    cases: list[dict[str, Any]] | None = None


class EvalRunOut(BaseModel):
    id: str
    pack_id: str
    pack_version: str
    status: str
    summary: dict[str, Any]
    results: list[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    edited_tool_input: dict[str, Any] | None = None


class AppSettingUpdate(BaseModel):
    provider_type: str | None = None
    model_name: str | None = None
    base_url: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    max_steps_per_run: int | None = None
    max_cost_per_run_usd: float | None = None
