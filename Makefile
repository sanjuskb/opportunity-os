.PHONY: help install dev lint test type-check format docker-up docker-down clean verify

PYTHON ?= python
UV ?= uv

help:
	@echo "Opportunity OS Development Commands:"
	@echo "  make install     - Install root, frontend, packages and backend dependencies"
	@echo "  make dev         - Run development services"
	@echo "  make lint        - Run linting for frontend and backend"
	@echo "  make type-check  - Run TypeScript and Python type checkers"
	@echo "  make test        - Run automated tests across the workspace"
	@echo "  make format      - Format TypeScript and Python files"
	@echo "  make docker-up   - Start local Redis, PostgreSQL, and auxiliary containers"
	@echo "  make docker-down - Stop local Docker containers"
	@echo "  make clean       - Remove caches, temporary files, and build outputs"
	@echo "  make verify      - Run full verification suite (lint, type-check, tests)"

install:
	pnpm install
	cd apps/api && $(UV) sync

dev-web:
	pnpm --filter @opportunity-os/web dev

dev-api:
	cd apps/api && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint-web:
	pnpm --filter @opportunity-os/web lint

lint-api:
	cd apps/api && $(UV) run ruff check .

lint: lint-web lint-api

type-check-web:
	pnpm --filter @opportunity-os/web type-check

type-check-api:
	cd apps/api && $(UV) run mypy app

type-check: type-check-web type-check-api

test-web:
	pnpm --filter @opportunity-os/web test

test-api:
	cd apps/api && $(UV) run pytest

test: test-web test-api

format:
	pnpm run format
	cd apps/api && $(UV) run ruff format .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

verify: lint type-check test
