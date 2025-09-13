# TalkingPhoto AI MVP - Test Automation Makefile
# Convenient commands for running tests and managing the test environment

.PHONY: help install test test-unit test-integration test-e2e test-performance test-fast test-slow test-all clean coverage lint format check

# Default target
help:
	@echo "TalkingPhoto AI MVP - Test Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install all dependencies including test requirements"
	@echo "  install-test     Install only test dependencies"
	@echo ""
	@echo "Test Commands:"
	@echo "  test             Run all tests with coverage"
	@echo "  test-unit        Run unit tests only (fast)"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e         Run end-to-end tests only"
	@echo "  test-performance Run performance tests and benchmarks"
	@echo "  test-fast        Run fast tests only (unit + quick integration)"
	@echo "  test-slow        Run slow tests only (e2e + performance)"
	@echo "  test-parallel    Run tests in parallel"
	@echo ""
	@echo "Coverage Commands:"
	@echo "  coverage         Generate HTML coverage report"
	@echo "  coverage-xml     Generate XML coverage report"
	@echo "  coverage-term    Show coverage in terminal"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint             Run code linting (flake8)"
	@echo "  format           Format code with black"
	@echo "  format-check     Check code formatting"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security-check   Run security scanning with bandit"
	@echo "  check            Run all quality checks"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean            Clean test artifacts and cache"
	@echo "  clean-all        Clean everything including dependencies"
	@echo "  test-debug       Run tests with debugging enabled"
	@echo "  test-collect     Show all available tests without running"

# Installation commands
install:
	pip install -r requirements/base.txt
	pip install -r requirements-test.txt

install-test:
	pip install -r requirements-test.txt

# Test execution commands
test:
	pytest --cov --cov-report=html --cov-report=term-missing -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v --tb=short

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v --tb=short

test-e2e:
	@echo "Running end-to-end tests..."
	pytest tests/e2e/ -v --tb=short

test-performance:
	@echo "Running performance tests..."
	pytest tests/performance/ -v --tb=short

test-fast:
	@echo "Running fast tests..."
	pytest -m "not slow" -v --tb=short

test-slow:
	@echo "Running slow tests..."
	pytest -m "slow" -v --tb=short

test-parallel:
	@echo "Running tests in parallel..."
	pytest -n auto --cov --cov-report=html -v

test-all:
	@echo "Running complete test suite..."
	pytest tests/ --cov --cov-report=html --cov-report=term-missing --cov-fail-under=85 -v

# Coverage commands
coverage:
	pytest --cov --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml:
	pytest --cov --cov-report=xml
	@echo "Coverage report generated in coverage.xml"

coverage-term:
	pytest --cov --cov-report=term-missing

# Code quality commands
lint:
	@echo "Running flake8 linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

format-check:
	@echo "Checking code formatting..."
	black --check .
	isort --check-only .

type-check:
	@echo "Running type checking..."
	mypy . --ignore-missing-imports

security-check:
	@echo "Running security checks..."
	bandit -r . -f json -o security-report.json || true
	@echo "Security report generated in security-report.json"

check: lint format-check type-check security-check
	@echo "All quality checks completed"

# Debugging and development commands
test-debug:
	@echo "Running tests with debugging enabled..."
	pytest --pdb --tb=long -v -s

test-collect:
	@echo "Collecting all available tests..."
	pytest --collect-only -q

test-failed:
	@echo "Re-running only failed tests..."
	pytest --lf -v

test-modified:
	@echo "Running tests for modified files..."
	pytest --testmon -v

# Specific test categories
test-auth:
	@echo "Running authentication tests..."
	pytest -m "auth" -v

test-credits:
	@echo "Running credit system tests..."
	pytest -m "credits" -v

test-files:
	@echo "Running file handling tests..."
	pytest -m "files" -v

test-video:
	@echo "Running video generation tests..."
	pytest -m "video" -v

test-ai:
	@echo "Running AI provider tests..."
	pytest -m "ai_provider" -v

test-db:
	@echo "Running database tests..."
	pytest -m "db" -v

# Benchmark and performance specific
test-benchmark:
	@echo "Running benchmark tests..."
	pytest -m "benchmark" --benchmark-only

test-memory:
	@echo "Running memory profiling tests..."
	pytest -m "performance" --profile-memory

test-load:
	@echo "Running load tests..."
	pytest tests/performance/test_video_generation_performance.py::TestVideoGenerationPerformance::test_load_testing_video_generation -v

# CI/CD commands
test-ci:
	@echo "Running CI test suite..."
	pytest --cov --cov-report=xml --cov-fail-under=85 --tb=short

test-smoke:
	@echo "Running smoke tests..."
	pytest -m "smoke" -v --tb=short

# Cleanup commands
clean:
	@echo "Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -f coverage.xml
	rm -f .coverage
	rm -f security-report.json
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyo" -delete
	rm -rf .mypy_cache/

clean-all: clean
	@echo "Cleaning all generated files..."
	rm -rf venv/
	rm -rf env/
	rm -rf .venv/
	pip freeze | grep -v "^-e" | xargs pip uninstall -y 2>/dev/null || true

# Documentation generation
test-docs:
	@echo "Generating test documentation..."
	pytest --collect-only --quiet > test-inventory.txt
	@echo "Test inventory saved to test-inventory.txt"

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "Development environment ready"

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

# Database specific
test-db-setup:
	@echo "Setting up test database..."
	export DATABASE_URL=sqlite:///:memory:
	python -c "from app import create_app, db; app = create_app('testing'); app.app_context().push(); db.create_all()"

test-db-teardown:
	@echo "Tearing down test database..."
	python -c "from app import create_app, db; app = create_app('testing'); app.app_context().push(); db.drop_all()"

# Performance monitoring
performance-baseline:
	@echo "Creating performance baseline..."
	pytest -m "benchmark" --benchmark-save=baseline

performance-compare:
	@echo "Comparing performance against baseline..."
	pytest -m "benchmark" --benchmark-compare=baseline

# Test environment validation
test-env-check:
	@echo "Checking test environment..."
	python -c "import pytest; print(f'pytest version: {pytest.__version__}')"
	python -c "import coverage; print(f'coverage version: {coverage.__version__}')"
	python -c "import flask; print(f'flask version: {flask.__version__}')"
	@echo "Test environment check completed"

# Continuous testing
test-watch:
	@echo "Starting continuous testing..."
	pytest-watch --runner "pytest -x -v"

# Test data management
test-data-reset:
	@echo "Resetting test data..."
	rm -rf /tmp/test_uploads/
	rm -rf /tmp/pytest-*/
	mkdir -p /tmp/test_uploads/

# Report generation
test-report:
	@echo "Generating comprehensive test report..."
	pytest --html=test-report.html --self-contained-html --cov --cov-report=html
	@echo "Test report generated: test-report.html"

# Quick commands for common workflows
quick-test: test-fast
	@echo "Quick test completed"

full-test: test-all
	@echo "Full test suite completed"

release-test: test-all check
	@echo "Release testing completed"