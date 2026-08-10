.PHONY: up down test lint seed
up:
	docker compose up --build
down:
	docker compose down
test:
	cd services/api && pytest -q
	cd apps/web && npm test
lint:
	cd services/api && ruff check .
	cd apps/web && npm run lint
seed:
	docker compose run --rm api python seed.py
