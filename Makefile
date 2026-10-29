.PHONY: lint format test db-up db-down

lint:            ## Check code style and common bugs
	uv run ruff check .
	uv run ruff format --check .

format:          ## Auto-fix formatting and import order
	uv run ruff check --fix .
	uv run ruff format .

test:            ## Run the test suite
	uv run pytest

db-up:           ## Start Postgres with pgvector
	docker compose up -d db

db-down:
	docker compose down