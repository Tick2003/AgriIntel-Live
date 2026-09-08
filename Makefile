# AgriIntel.in — Developer Makefile
# ===================================
# Usage: make <target>
# Requires: Python 3.10+, pip, Docker

.DEFAULT_GOAL := help
PYTHON        := python
PIP           := pip
PYTEST        := $(PYTHON) -m pytest
RUFF          := $(PYTHON) -m ruff

.PHONY: help install install-dev lint format test test-all coverage \
        run run-api docker-build docker-up docker-down clean

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo "AgriIntel.in — Available Make targets:"
	@echo ""
	@echo "  Setup"
	@echo "    install       Install production dependencies"
	@echo "    install-dev   Install dev/test extras (includes production)"
	@echo ""
	@echo "  Code Quality"
	@echo "    lint          Run ruff linter (no auto-fix)"
	@echo "    format        Run ruff formatter + auto-fix"
	@echo ""
	@echo "  Testing"
	@echo "    test          Run offline unit tests (fast, no network)"
	@echo "    test-all      Run full test suite including integration tests"
	@echo "    coverage      Run offline tests + generate HTML coverage report"
	@echo ""
	@echo "  Running"
	@echo "    run           Start Streamlit UI (dev mode)"
	@echo "    run-api       Start FastAPI backend (dev mode, reload)"
	@echo ""
	@echo "  Docker"
	@echo "    docker-build  Build Docker image"
	@echo "    docker-up     Start all services with docker-compose"
	@echo "    docker-down   Stop all services"
	@echo ""
	@echo "  Utilities"
	@echo "    clean         Remove build artifacts and cache files"

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -e ".[dev]"
	$(PIP) install pre-commit
	pre-commit install

# ── Code Quality ──────────────────────────────────────────────────────────────
lint:
	$(RUFF) check .

format:
	$(RUFF) check --fix .
	$(RUFF) format .

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	$(PYTEST) -m "not integration" -v --tb=short

test-all:
	$(PYTEST) -v

coverage:
	$(PYTEST) -m "not integration" \
		--cov=app --cov=agents --cov=database --cov=etl --cov=cv --cov=utils \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=50 \
		-v
	@echo "HTML report: htmlcov/index.html"

# ── Running ───────────────────────────────────────────────────────────────────
run:
	streamlit run app/main.py

run-api:
	uvicorn api_server:app --reload --port 8000

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build:
	docker build -t agriintel:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# ── Utilities ─────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete."
