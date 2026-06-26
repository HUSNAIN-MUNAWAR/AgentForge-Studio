# Screenshot Catalog

These screenshots were captured from the running AgentForge Studio UI and are embedded in the root README.

## Regenerate

Start the backend and frontend first:

```bash
# backend
PYTHONPATH=. DATABASE_URL=sqlite:///./agentforge.db QUEUE_EXECUTION_MODE=sync LLM_PROVIDER=mock \
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# frontend
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run build
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run start -- -H 127.0.0.1 -p 3000
```

Then capture:

```bash
cd frontend
APP_URL=http://127.0.0.1:3000 API_URL=http://127.0.0.1:8000 npm run screenshots
```

## Files

- `dashboard.png`
- `templates.png`
- `packs.png`
- `pack-builder.png`
- `workflow.png`
- `runs.png`
- `trace-viewer.png`
- `evaluation-lab.png`
- `approval-queue.png`
- `tools.png`
- `memory.png`
- `settings.png`
