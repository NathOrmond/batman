.PHONY: help install install-dev clean test lint format type-check build docs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in production mode
	pip install -e .

install-dev: ## Install the package in development mode with all dev dependencies
	pip install -e .[dev]

clean: ## Clean up Python cache files and build artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=api_testing_framework --cov-report=html --cov-report=term

lint: ## Run linting checks
	flake8 api_testing_framework/
	black --check api_testing_framework/

format: ## Format code with black and isort
	black api_testing_framework/
	isort api_testing_framework/

type-check: ## Run type checking with mypy
	mypy api_testing_framework/

check: lint type-check test ## Run all checks (lint, type-check, test)

build: ## Build the package
	python -m build

docs: ## Generate documentation
	@echo "Documentation generation not implemented yet"

init-project: ## Initialize a new BATMAN project
	python -m api_testing_framework.cli init example-project

generate-tests: ## Generate tests from example config
	python -m api_testing_framework.cli generate -c example-config.yaml

run-tests: ## Run generated tests
	python -m api_testing_framework.cli run -c example-config.yaml

validate-config: ## Validate example configuration
	python -m api_testing_framework.cli validate -c example-config.yaml

all: clean install-dev check build ## Clean, install dev deps, run checks, and build
