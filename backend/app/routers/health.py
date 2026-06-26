from fastapi import APIRouter, Response
from backend.app.queue.rq_queue import get_queue_length
from backend.app.core.config import get_settings
from backend.app import metrics

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "agentforge-api"}


@router.get("/ready")
def ready():
    settings = get_settings()
    qlen = get_queue_length()
    if qlen is not None:
        metrics.queue_length.labels(queue=settings.queue_name).set(qlen)
    return {"status": "ready", "queue": settings.queue_name, "queue_length": qlen, "queue_mode": settings.queue_execution_mode}


@router.get("/metrics")
def prometheus_metrics():
    payload, content_type = metrics.render_metrics()
    return Response(content=payload, media_type=content_type)
