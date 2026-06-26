from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import ToolDefinition
from backend.app.routers import approvals, evals, files, health, memory, packs, runs, settings as settings_router, tools as tools_router, traces, websocket
from backend.app.services.seed import seed_builtin_packs, seed_tool_definitions

configure_logging()
app_settings = get_settings()

app = FastAPI(title="AgentForge Studio API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_tool_definitions(db)
        seed_builtin_packs(db)
    finally:
        db.close()


app.include_router(health.router)
app.include_router(packs.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(traces.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(tools_router.router, prefix="/api")
app.include_router(evals.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(websocket.router)
