.PHONY: dev test eval validate-packs docker-config frontend-build worker

dev:
	docker compose up --build

worker:
	python worker.py

test:
	python -m py_compile backend/app/main.py
	pytest backend/tests -q

validate-packs:
	python scripts/validate_packs.py

eval:
	python evals/run_local_eval.py

docker-config:
	docker compose config

frontend-build:
	cd frontend && npm install && npm run build
