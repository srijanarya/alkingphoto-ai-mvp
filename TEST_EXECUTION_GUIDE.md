# TalkingPhoto AI MVP - Test Execution Guide

## Overview

This guide provides comprehensive instructions for running tests in the TalkingPhoto AI MVP project. The test suite includes unit tests, integration tests, end-to-end tests, and performance benchmarks.

## Quick Start

### Install Test Dependencies

```bash
# Install test requirements
pip install -r requirements-test.txt

# Verify pytest installation
pytest --version
```

### Run All Tests

```bash
# Run complete test suite
pytest

# Run with coverage
pytest --cov

# Run with detailed output
pytest -v --tb=short
```

## Test Categories

### Unit Tests (Fast)

Unit tests focus on individual components and functions in isolation.

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test modules
pytest tests/unit/test_ai_service.py -v
pytest tests/unit/test_credits.py -v
pytest tests/unit/test_file_service.py -v
pytest tests/unit/test_user_management.py -v

# Run unit tests with markers
pytest -m "unit" -v
pytest -m "unit and not slow" -v
```

**Expected Results:**

- 50+ unit tests
- Execution time: < 30 seconds
- Coverage: 85%+ for core modules

### Integration Tests (Medium)

Integration tests verify component interactions and external service integrations.

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run video generation pipeline tests
pytest tests/integration/test_video_generation_pipeline.py -v

# Run integration tests with specific markers
pytest -m "integration" -v
pytest -m "integration and ai_provider" -v
```

**Expected Results:**

- 20+ integration tests
- Execution time: 2-5 minutes
- Tests AI provider interactions (mocked)

### End-to-End Tests (Slow)

E2E tests validate complete user workflows from start to finish.

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific E2E scenarios
pytest tests/e2e/test_complete_video_workflow.py::TestCompleteVideoWorkflow::test_new_user_complete_journey -v

# Run E2E tests with markers
pytest -m "e2e" -v
pytest -m "e2e and not slow" -v
```

**Expected Results:**

- 10+ E2E scenarios
- Execution time: 5-10 minutes
- Full workflow validation

### Performance Tests (Very Slow)

Performance tests benchmark system capabilities and identify bottlenecks.

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific performance benchmarks
pytest tests/performance/test_video_generation_performance.py::TestVideoGenerationPerformance::test_single_video_generation_speed -v

# Run performance tests with markers
pytest -m "performance" -v
pytest -m "benchmark" -v
```

**Expected Results:**

- 8+ performance tests
- Execution time: 10-20 minutes
- Performance metrics and benchmarks

## Test Filtering and Selection

### By Test Markers

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run database-related tests
pytest -m "db" -v

# Run AI provider tests
pytest -m "ai_provider" -v

# Run authentication tests
pytest -m "auth" -v

# Run credit system tests
pytest -m "credits" -v

# Run file handling tests
pytest -m "files" -v

# Run video generation tests
pytest -m "video" -v
```

### By Test Names

```bash
# Run tests matching pattern
pytest -k "test_ai_service" -v
pytest -k "test_credits and not integration" -v
pytest -k "video_generation" -v

# Run specific test classes
pytest tests/unit/test_ai_service.py::TestAIService -v
pytest tests/unit/test_credits.py::TestCreditManager -v
```

### By Test Files

```bash
# Run specific test files
pytest tests/unit/test_ai_service.py tests/unit/test_credits.py -v

# Run all tests in a directory
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Coverage Analysis

### Generate Coverage Reports

```bash
# HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov --cov-report=term-missing

# XML coverage report (for CI)
pytest --cov --cov-report=xml

# Coverage with specific threshold
pytest --cov --cov-fail-under=85
```

### Coverage by Module

```bash
# Coverage for specific modules
pytest --cov=services --cov-report=term-missing
pytest --cov=models --cov-report=term-missing
pytest --cov=core --cov-report=term-missing
```

## Test Environment Configuration

### Environment Variables

```bash
# Set test environment
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
export REDIS_URL=redis://localhost:6379/15

# API keys for integration tests (optional)
export NANO_BANANA_API_KEY=test_key
export VEO3_API_KEY=test_key
export RUNWAY_API_KEY=test_key
```

### Test Database Setup

```bash
# Use in-memory SQLite for speed (default)
pytest tests/unit/

# Use PostgreSQL for integration tests
export TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
pytest tests/integration/
```

## Parallel Test Execution

### Install pytest-xdist

```bash
pip install pytest-xdist
```

### Run Tests in Parallel

```bash
# Auto-detect CPU cores
pytest -n auto

# Specify number of workers
pytest -n 4

# Parallel execution with coverage
pytest -n auto --cov --cov-report=html
```

**Note:** Some integration tests may not be suitable for parallel execution due to shared resources.

## Continuous Integration

### GitHub Actions Configuration

The test suite is configured to run in GitHub Actions:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", 3.11]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Local CI Simulation

```bash
# Simulate CI environment locally
export CI=true
export GITHUB_ACTIONS=true
pytest --cov --cov-report=xml -v
```

## Test Data Management

### Test Fixtures

The test suite uses comprehensive fixtures for consistent test data:

```python
# Available fixtures
@pytest.fixture
def test_user()          # Standard test user
def premium_user()       # Premium subscription user
def test_file()          # Sample uploaded file
def test_video_generation()  # Video generation record
def sample_image_data()  # Image file content
def temp_upload_dir()    # Temporary directory
def auth_headers()       # Authentication headers
```

### Database Fixtures

```python
@pytest.fixture
def db_session()         # Database session with rollback
def clean_db()          # Fresh database state
```

### Mock Services

```python
# AI service mocks
@pytest.fixture
def ai_mocks()          # All AI service mocks
def mock_veo3_api()     # VEO3 API mock
def mock_runway_api()   # Runway API mock
def mock_elevenlabs()   # ElevenLabs TTS mock
```

## Debugging Tests

### Run Tests with Debugging

```bash
# Run with Python debugger
pytest --pdb tests/unit/test_ai_service.py

# Run with detailed tracebacks
pytest --tb=long -v

# Run with print statements visible
pytest -s -v

# Run single test with maximum verbosity
pytest tests/unit/test_ai_service.py::TestAIService::test_enhance_image_success -v -s
```

### Test Logging

```bash
# Enable test logging
pytest --log-cli-level=INFO -v

# Capture logs in test output
pytest --capture=no --log-cli-level=DEBUG -v
```

## Performance Testing

### Benchmark Tests

```bash
# Run benchmark tests
pytest -m "benchmark" --benchmark-only

# Save benchmark results
pytest -m "benchmark" --benchmark-json=benchmark_results.json

# Compare benchmark results
pytest -m "benchmark" --benchmark-compare=baseline.json
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
pytest -m "performance" --profile-memory
```

### Load Testing

```bash
# Run concurrent load tests
pytest tests/performance/test_video_generation_performance.py::test_concurrent_video_generation -v

# Run database performance tests
pytest tests/performance/test_video_generation_performance.py::test_database_performance_under_load -v
```

## Test Maintenance

### Update Test Dependencies

```bash
# Update test requirements
pip-compile requirements-test.in

# Install updated dependencies
pip-sync requirements-test.txt
```

### Clean Test Environment

```bash
# Remove test artifacts
rm -rf htmlcov/
rm -rf .pytest_cache/
rm -f coverage.xml
rm -f .coverage

# Clean temporary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## Common Test Commands

### Development Workflow

```bash
# Quick smoke test
pytest -m "smoke" -v

# Test changes only
pytest --lf -v  # Last failed
pytest --ff -v  # Failed first

# Test modified files
pytest --testmon -v
```

### Release Testing

```bash
# Full test suite for release
pytest --cov --cov-fail-under=85 -v

# Critical path tests
pytest -m "not slow" --cov-fail-under=90 -v

# Performance regression tests
pytest -m "benchmark" --benchmark-compare=baseline.json
```

## Troubleshooting

### Common Issues

**1. ImportError: No module named 'X'**

```bash
# Install missing dependencies
pip install -r requirements-test.txt
```

**2. Database connection errors**

```bash
# Check database configuration
export DATABASE_URL=sqlite:///:memory:
```

**3. Permission errors with temp files**

```bash
# Clean up temp directories
rm -rf /tmp/pytest-*
```

**4. Slow test execution**

```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

**5. Memory issues with large tests**

```bash
# Run tests in smaller batches
pytest tests/unit/
pytest tests/integration/
```

### Test Debugging Checklist

1. ✅ All dependencies installed (`pip install -r requirements-test.txt`)
2. ✅ Database configured correctly
3. ✅ Environment variables set
4. ✅ Test data fixtures available
5. ✅ Mock services configured
6. ✅ Sufficient disk space for temp files
7. ✅ Correct Python version (3.8+)

## Test Quality Metrics

### Success Criteria

- **Unit Tests**: 90%+ pass rate, < 30 seconds execution
- **Integration Tests**: 95%+ pass rate, < 5 minutes execution
- **E2E Tests**: 95%+ pass rate, < 10 minutes execution
- **Code Coverage**: 85%+ overall, 95%+ for critical paths
- **Performance**: Meet all benchmark targets

### Monitoring

```bash
# Generate test report
pytest --html=report.html --self-contained-html

# Monitor test trends
pytest --collect-only --quiet | wc -l  # Count total tests
```

---

**Last Updated**: 2025-09-13  
**Test Suite Version**: 1.0  
**Python Version**: 3.8+  
**Total Tests**: 80+ tests across all categories
