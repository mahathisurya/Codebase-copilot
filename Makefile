.PHONY: dev test lint format eval clean help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment
	docker compose up --build

dev-detached: ## Start development environment in background
	docker compose up --build -d

stop: ## Stop all services
	docker compose down

logs: ## View logs
	docker compose logs -f

logs-backend: ## View backend logs
	docker compose logs -f backend

logs-frontend: ## View frontend logs
	docker compose logs -f frontend

test: ## Run all tests
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

test-watch: ## Run tests in watch mode
	docker compose exec backend pytest-watch tests/

lint: ## Run linters
	@echo "Linting backend..."
	docker compose exec backend ruff check app/ tests/
	docker compose exec backend mypy app/ tests/
	@echo "Linting frontend..."
	docker compose exec frontend npm run lint

format: ## Format code
	@echo "Formatting backend..."
	docker compose exec backend ruff format app/ tests/
	@echo "Formatting frontend..."
	docker compose exec frontend npm run format

type-check: ## Run type checkers
	docker compose exec backend mypy app/ tests/
	docker compose exec frontend npm run type-check

eval: ## Run evaluation suite
	docker compose exec backend python -m eval.run --dataset eval/sample_eval.json

eval-report: ## Generate evaluation report
	docker compose exec backend python -m eval.report

shell-backend: ## Open backend shell
	docker compose exec backend /bin/bash

shell-frontend: ## Open frontend shell
	docker compose exec frontend /bin/sh

clean: ## Clean up generated files and volumes
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf backend/data/*
	rm -rf backend/repos/*

rebuild: ## Rebuild containers
	docker compose down
	docker compose build --no-cache
	docker compose up

install-backend: ## Install backend dependencies locally
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies locally
	cd frontend && npm install

db-reset: ## Reset database
	docker compose exec backend python -m app.storage.db reset

ci-test: ## Run CI tests
	cd backend && pytest tests/ -v --cov=app --cov-report=xml
	cd frontend && npm run lint && npm run build
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
.next/
out/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Environment
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# App specific
backend/data/*
!backend/data/.gitkeep
backend/repos/*
!backend/repos/.gitkeep
eval/runs/*
!eval/runs/.gitkeep

# Logs
*.log
logs/

# Docker
*.pid