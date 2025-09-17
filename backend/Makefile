# Test Makefile for Magic Trick Analyzer Backend

# Default Python interpreter
PYTHON := python3
PIP := pip3

# Test configuration
TEST_DIR := tests
SRC_DIR := src
COV_DIR := htmlcov

# Install test dependencies
install-test-deps:
	$(PIP) install pytest pytest-asyncio pytest-mock pytest-cov fastapi-testclient

# Run all tests
test:
	$(PYTHON) -m pytest $(TEST_DIR)/ -v

# Run tests with coverage
test-cov:
	$(PYTHON) -m pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing --cov-fail-under=80 -v

# Run only unit tests
test-unit:
	$(PYTHON) -m pytest $(TEST_DIR)/ -m unit -v

# Run only integration tests  
test-integration:
	$(PYTHON) -m pytest $(TEST_DIR)/ -m integration -v

# Run fast tests (exclude slow ones)
test-fast:
	$(PYTHON) -m pytest $(TEST_DIR)/ -m "not slow" -v

# Run specific test file
test-file:
	@read -p "Enter test file name: " file; \
	$(PYTHON) -m pytest $(TEST_DIR)/$$file -v

# Generate coverage report only
coverage:
	$(PYTHON) -m pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

# Open coverage report in browser
coverage-open:
	@if [ -f "$(COV_DIR)/index.html" ]; then \
		echo "Opening coverage report..."; \
		python -m webbrowser $(COV_DIR)/index.html; \
	else \
		echo "Coverage report not found. Run 'make test-cov' first."; \
	fi

# Clean test artifacts
clean-test:
	rm -rf .pytest_cache/
	rm -rf $(COV_DIR)/
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run tests in Docker (if applicable)
test-docker:
	docker-compose -f ../docker-compose.yml exec magic-trick-analyzer python -m pytest tests/ -v

# Lint code (if linting tools are available)
lint:
	@which flake8 > /dev/null && flake8 $(SRC_DIR)/ $(TEST_DIR)/ || echo "flake8 not found"
	@which black > /dev/null && black --check $(SRC_DIR)/ $(TEST_DIR)/ || echo "black not found"

# Format code (if formatting tools are available)
format:
	@which black > /dev/null && black $(SRC_DIR)/ $(TEST_DIR)/ || echo "black not found"
	@which isort > /dev/null && isort $(SRC_DIR)/ $(TEST_DIR)/ || echo "isort not found"

# Run all quality checks
quality: lint test-cov

# Help
help:
	@echo "Available targets:"
	@echo "  install-test-deps  - Install testing dependencies"
	@echo "  test              - Run all tests"
	@echo "  test-cov          - Run tests with coverage report"
	@echo "  test-unit         - Run only unit tests"
	@echo "  test-integration  - Run only integration tests"
	@echo "  test-fast         - Run fast tests (exclude slow ones)"
	@echo "  test-file         - Run specific test file (interactive)"
	@echo "  coverage          - Generate coverage report"
	@echo "  coverage-open     - Open coverage report in browser"
	@echo "  clean-test        - Clean test artifacts"
	@echo "  test-docker       - Run tests in Docker container"
	@echo "  lint              - Run linting tools"
	@echo "  format            - Format code"
	@echo "  quality           - Run all quality checks"
	@echo "  help              - Show this help message"

.PHONY: install-test-deps test test-cov test-unit test-integration test-fast test-file coverage coverage-open clean-test test-docker lint format quality help