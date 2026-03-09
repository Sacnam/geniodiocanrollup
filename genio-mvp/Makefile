# Genio Knowledge OS - Makefile

.PHONY: help install dev test lint build deploy clean

# Default target
help:
	@echo "Genio Knowledge OS - Available Commands:"
	@echo ""
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development environment"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make build        - Build production images"
	@echo "  make deploy       - Deploy to production"
	@echo "  make clean        - Clean up containers and volumes"
	@echo ""

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Development
dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres redis qdrant
	@echo "Run these commands in separate terminals:"
	@echo "  cd backend && uvicorn app.main:app --reload"
	@echo "  cd backend && celery -A app.tasks worker --loglevel=info"
	@echo "  cd backend && celery -A app.tasks beat --loglevel=info"
	@echo "  cd frontend && npm run dev"

# Testing
test:
	@echo "Running backend tests..."
	cd backend && pytest -v --tb=short
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

test-coverage:
	cd backend && pytest --cov=app --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

# Linting
lint:
	@echo "Linting backend..."
	cd backend && flake8 app tests --max-line-length=100 --ignore=E203,W503
	cd backend && black --check app tests
	@echo "Linting frontend..."
	cd frontend && npm run lint

lint-fix:
	cd backend && black app tests
	cd frontend && npm run lint -- --fix

# Database
db-migrate:
	cd backend && alembic upgrade head

db-rollback:
	cd backend && alembic downgrade -1

db-reset:
	cd backend && alembic downgrade base && alembic upgrade head

# Building
build:
	@echo "Building Docker images..."
	docker-compose build

build-prod:
	cd backend && docker build -t genio-api:latest .
	cd frontend && docker build -t genio-frontend:latest .

# Deployment
deploy-staging:
	cd deploy && terraform workspace select staging && terraform apply

deploy-prod:
	./deploy/production-deploy.sh

# Health checks
health:
	./scripts/health-check.sh http://localhost:8000

# Maintenance
db-analyze:
	psql $(DATABASE_URL) -f scripts/db-maintenance.sql

backup:
	./scripts/backup.sh

# Cleaning
clean:
	docker-compose down -v
	docker system prune -f

clean-all: clean
	rm -rf backend/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf frontend/node_modules
	rm -rf frontend/dist

# Documentation
docs:
	@echo "Generating API documentation..."
	cd backend && python -c "from app.main import app; import json; from fastapi.openapi.utils import get_openapi; print(json.dumps(get_openapi(title='Genio API', version='2.1.0', routes=app.routes)))" > ../docs/openapi.json

# Load testing
load-test:
	cd backend && locust -f tests/load_test.py --host=http://localhost:8000

# Full CI simulation
ci: lint test build
	@echo "CI checks complete!"
