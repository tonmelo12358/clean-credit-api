# CleanCredit API - Developer Workflow Automation

# Variables
PYTHON = python3
PIP = pip
UVICORN = $(PYTHON) -m uvicorn
PYTEST = $(PYTHON) -m pytest
RUFF = $(PYTHON) -m ruff
MYPY = $(PYTHON) -m mypy

# Default target
.DEFAULT_GOAL := help

.PHONY: install run test lint clean help

help:
	@echo "CleanCredit API - Developer Workflow"
	@echo "------------------------------------"
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  install  Install project dependencies"
	@echo "  run      Run the FastAPI server on port 8001 (hot-reload)"
	@echo "  test     Execute the full pytest suite"
	@echo "  lint     Run static analysis (Ruff & Mypy)"
	@echo "  clean    Remove Python artifacts and cache directories"

install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

run:
	@echo "Starting API server on port 8001..."
	$(UVICORN) app.main:app --port 8001 --reload

test:
	@echo "Running tests..."
	$(PYTEST)

lint:
	@echo "Running linter (Ruff)..."
	$(RUFF) check .
	@echo "Running type checker (Mypy)..."
	$(MYPY) app

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -f .coverage
	rm -rf htmlcov