.PHONY: help install test test-unit test-integration lint format type-check clean pre-commit install-hooks

help: ## Show this help message
	@echo "Market7 Development Commands"
	@echo "============================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .
	pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-xdist
	pip install black isort flake8 mypy pre-commit safety bandit

test: ## Run all tests
	python run_tests.py --all

test-unit: ## Run unit tests only
	python run_tests.py --unit

test-integration: ## Run integration tests only
	python run_tests.py --integration

test-coverage: ## Run tests with coverage report
	python run_tests.py --all --coverage

lint: ## Run linting checks
	python run_tests.py --lint

format: ## Check code formatting
	python run_tests.py --format

format-fix: ## Fix code formatting
	black core dca fork lev utils
	isort core dca fork lev utils

type-check: ## Run type checking
	python run_tests.py --type-check

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

install-hooks: ## Install pre-commit hooks
	pre-commit install

security: ## Run security checks
	safety check --file requirements.txt
	bandit -r core dca fork lev utils

quick-check: ## Quick development check (format + lint + type)
	black --check core dca fork lev utils
	isort --check-only core dca fork lev utils
	flake8 core dca fork lev utils
	mypy core dca fork lev utils --ignore-missing-imports

ci: ## Run full CI pipeline locally
	python run_tests.py --all --coverage
	safety check --file requirements.txt
	bandit -r core dca fork lev utils

setup: install-dev install-hooks ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."