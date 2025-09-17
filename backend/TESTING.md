# Testing Guide - Magic Trick Analyzer Backend

This document provides comprehensive information about the test suite for the Magic Trick Analyzer backend.

## Overview

The test suite provides comprehensive coverage of the backend microservices architecture, including:
- Job queue system (Redis-based)
- OCR processing (PyMuPDF + Tesseract)
- AI processing (Sentence Transformers + custom algorithms)
- Job orchestration workflows
- FastAPI endpoints and routers
- Application initialization and configuration

## Test Structure

```
backend/
├── tests/
│   ├── conftest.py              # Global fixtures and configuration
│   ├── test_job_queue.py        # Job queue system tests
│   ├── test_ocr_processor.py    # OCR processing tests
│   ├── test_ai_processor.py     # AI processing tests
│   ├── test_job_orchestrator.py # Workflow orchestration tests
│   ├── test_jobs_api.py         # Jobs API endpoint tests
│   ├── test_books_api.py        # Books API endpoint tests
│   └── test_main_app.py         # Application initialization tests
├── pytest.ini                  # Pytest configuration
├── run_tests.py                # Python test runner
├── test.ps1                    # PowerShell test runner (Windows)
└── Makefile                    # Unix/Linux test commands
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Use mocks for external dependencies
- Fast execution time
- High test coverage of business logic

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May use real external services in test mode
- Longer execution time
- Test realistic workflows

### Slow Tests (`@pytest.mark.slow`)
- Tests that take significant time to execute
- Large file processing tests
- Complex AI model operations
- Can be excluded for quick feedback

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov fastapi-testclient

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
```

### Using Test Runners

#### Python Test Runner (Cross-platform)
```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run only unit tests
python run_tests.py --unit

# Run specific test file
python run_tests.py --file test_job_queue.py

# Clean artifacts
python run_tests.py --clean
```

#### PowerShell Test Runner (Windows)
```powershell
# Run all tests
.\test.ps1 test

# Run with coverage
.\test.ps1 test-cov

# Run only unit tests
.\test.ps1 test-unit

# Run specific test file
.\test.ps1 test -TestFile test_job_queue.py

# Clean artifacts
.\test.ps1 clean
```

#### Makefile (Unix/Linux/macOS)
```bash
# Install dependencies
make install-test-deps

# Run all tests
make test

# Run with coverage
make test-cov

# Run only unit tests
make test-unit

# Clean artifacts
make clean-test
```

## Test Coverage

The test suite targets **80%+ code coverage** across all backend components:

### Coverage by Component

| Component | Test File | Coverage Target |
|-----------|-----------|----------------|
| Job Queue | `test_job_queue.py` | 90%+ |
| OCR Processor | `test_ocr_processor.py` | 85%+ |
| AI Processor | `test_ai_processor.py` | 85%+ |
| Job Orchestrator | `test_job_orchestrator.py` | 90%+ |
| Jobs API | `test_jobs_api.py` | 95%+ |
| Books API | `test_books_api.py` | 95%+ |
| Main App | `test_main_app.py` | 90%+ |

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Open coverage report (automatically opens browser)
# Windows: start htmlcov/index.html
# macOS: open htmlcov/index.html  
# Linux: xdg-open htmlcov/index.html
```

## Test Fixtures and Utilities

### Global Fixtures (conftest.py)

- **`event_loop`**: Async event loop for testing
- **`mock_redis`**: Mocked Redis client
- **`mock_job_queue`**: Mocked job queue instance
- **`temp_dir`**: Temporary directory for test files
- **`sample_pdf`**: Generated test PDF document
- **`db_session`**: Mocked database session

### Test Data Generation

Tests automatically generate:
- Sample PDF documents with text content
- Mock job data and responses
- Temporary files and directories
- Database records for testing

## Key Testing Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Mocking External Services
```python
def test_with_mock_redis(mock_redis):
    mock_redis.get.return_value = b"test_value"
    result = function_using_redis()
    assert result == "test_value"
```

### API Testing
```python
def test_api_endpoint(client):
    response = client.get("/api/jobs/123")
    assert response.status_code == 200
    assert response.json()["id"] == "123"
```

### File Upload Testing
```python
def test_file_upload(client, sample_pdf):
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    response = client.post("/api/books/upload", files=files)
    assert response.status_code == 200
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests that take significant time
    api: API endpoint tests
    async: Async tests
addopts = 
    --strict-markers
    --tb=short
    --cov-fail-under=80
```

### Environment Variables

Tests use the following environment variables:

```bash
# Test database
TEST_DATABASE_URL=sqlite:///test.db

# Redis configuration
TEST_REDIS_URL=redis://localhost:6379/1

# AI model settings
TEST_MODEL_PATH=./test_models/

# OCR settings
TEST_TESSERACT_PATH=/usr/bin/tesseract
```

## Debugging Tests

### Running Specific Tests
```bash
# Run single test
python -m pytest tests/test_job_queue.py::test_enqueue_job -v

# Run test class
python -m pytest tests/test_ai_processor.py::TestTrickDetection -v

# Run tests matching pattern
python -m pytest -k "test_upload" -v
```

### Debug Output
```bash
# Show print statements
python -m pytest tests/ -s

# Show local variables on failure
python -m pytest tests/ --tb=long

# Stop on first failure
python -m pytest tests/ -x
```

### Using pytest-pdb
```bash
# Install pytest-pdb
pip install pytest-pdb

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Drop into debugger on first failure
python -m pytest tests/ --pdb -x
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock pytest-cov
      - name: Run tests
        run: python -m pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Docker Testing
```bash
# Run tests in Docker container
docker-compose -f docker-compose.yml exec magic-trick-analyzer python -m pytest tests/ -v

# Run tests with coverage in Docker
docker-compose -f docker-compose.yml exec magic-trick-analyzer python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Performance Testing

### Benchmarking
```python
import pytest
from time import time

def test_performance_benchmark():
    start_time = time()
    result = expensive_operation()
    execution_time = time() - start_time
    
    assert execution_time < 5.0  # Should complete in under 5 seconds
    assert result is not None
```

### Memory Usage
```bash
# Install memory profiler
pip install pytest-memray

# Run with memory profiling
python -m pytest tests/ --memray
```

## Test Maintenance

### Adding New Tests

1. **Identify the component** to test
2. **Choose appropriate test file** or create new one
3. **Use existing fixtures** from conftest.py
4. **Add appropriate markers** (unit/integration/slow)
5. **Follow naming conventions** (test_*)
6. **Include docstrings** explaining test purpose
7. **Test both success and failure cases**

### Updating Tests

- Update tests when modifying business logic
- Maintain backward compatibility in test fixtures
- Update test documentation when adding new features
- Review coverage reports regularly

### Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what they test
3. **Good Coverage**: Aim for 80%+ coverage but focus on critical paths
4. **Fast Tests**: Keep unit tests fast, mark slow tests appropriately
5. **Realistic Data**: Use representative test data
6. **Error Testing**: Test error conditions and edge cases
7. **Documentation**: Keep test documentation up to date

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes src directory
2. **Async Errors**: Use `@pytest.mark.asyncio` for async tests
3. **Database Errors**: Ensure test database is properly isolated
4. **Redis Errors**: Use mock_redis fixture for Redis-dependent tests
5. **File Errors**: Use temp_dir fixture for file operations

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review test logs for detailed error information
- Use `--tb=long` for full traceback information
- Enable debug logging in test configuration
- Run tests with `-s` flag to see print output

## Metrics and Reporting

### Coverage Metrics
- **Line Coverage**: Percentage of code lines executed
- **Branch Coverage**: Percentage of code branches taken
- **Function Coverage**: Percentage of functions called

### Performance Metrics
- **Test Execution Time**: Total time for test suite
- **Individual Test Performance**: Time per test
- **Memory Usage**: Memory consumption during tests

### Quality Metrics
- **Test Success Rate**: Percentage of passing tests
- **Code Coverage Trend**: Coverage over time
- **Test Maintenance**: Tests updated per code change