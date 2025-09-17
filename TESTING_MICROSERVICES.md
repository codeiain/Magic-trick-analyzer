# Magic Trick Analyzer - Testing & CI/CD

This document provides comprehensive information about testing and CI/CD for the Magic Trick Analyzer microservices.

## 🧪 Testing Overview

The project includes comprehensive unit tests for all microservices:

- **OCR Service**: Text extraction, validation, and job processing tests
- **AI Service**: Trick detection, classification, and similarity calculation tests  
- **MCP Server**: Database operations and tool handler tests
- **Backend**: Complete integration and API tests (existing comprehensive suite)

## 📋 Test Structure

```
magic-trick-analyzer/
├── ocr-service/
│   ├── test_ocr_processor.py       # OCR service unit tests
│   ├── pytest.ini                 # Test configuration
│   ├── run_tests.py               # Test runner script
│   └── requirements.txt           # Includes pytest dependencies
├── ai-service/
│   ├── test_ai_processor.py        # AI service unit tests
│   ├── pytest.ini                 # Test configuration
│   ├── run_tests.py               # Test runner script
│   └── requirements.txt           # Includes pytest dependencies
├── mcp-server/
│   ├── test_magic_trick_mcp_server.py  # MCP server unit tests
│   ├── pytest.ini                 # Test configuration
│   ├── run_tests.py               # Test runner script
│   └── requirements.txt           # Includes pytest dependencies
├── backend/
│   ├── tests/                     # Comprehensive backend test suite
│   ├── pytest.ini                # Test configuration
│   ├── run_tests.py              # Test runner script
│   └── TESTING.md                # Detailed testing documentation
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI/CD pipeline
└── docker-compose.test.yml        # Test environment configuration
```

## 🚀 Running Tests

### Individual Service Tests

#### OCR Service
```bash
cd ocr-service
python run_tests.py --coverage    # Run with coverage
python run_tests.py --unit        # Unit tests only
python -m pytest test_ocr_processor.py -v
```

#### AI Service  
```bash
cd ai-service
python run_tests.py --coverage    # Run with coverage
python run_tests.py --unit        # Unit tests only
python -m pytest test_ai_processor.py -v
```

#### MCP Server
```bash
cd mcp-server
python run_tests.py --coverage    # Run with coverage
python run_tests.py --unit        # Unit tests only
python -m pytest test_magic_trick_mcp_server.py -v
```

#### Backend (Comprehensive Suite)
```bash
cd backend
python run_tests.py --coverage    # Run with coverage
.\test.ps1 test-cov               # PowerShell (Windows)
make test-cov                     # Make (Unix/Linux)
```

### Docker-based Testing

Run tests in isolated Docker containers:

```bash
# Run all service tests
docker-compose -f docker-compose.test.yml --profile test up --build --abort-on-container-exit

# Run specific service tests
docker-compose -f docker-compose.test.yml run test-ocr
docker-compose -f docker-compose.test.yml run test-ai
docker-compose -f docker-compose.test.yml run test-mcp
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci.yml` provides:

#### Test Jobs
- **test-ocr-service**: OCR service unit tests with coverage
- **test-ai-service**: AI service unit tests with coverage  
- **test-mcp-server**: MCP server unit tests with coverage
- **test-backend**: Comprehensive backend test suite

#### Build Jobs
- **build-images**: Build Docker images for all services
- **security-scan**: Vulnerability scanning with Trivy
- **integration-tests**: Full system integration tests

#### Deployment Jobs
- **deploy-staging**: Deploy to staging (develop branch)
- **deploy-production**: Deploy to production (main branch)

### Workflow Features

✅ **Multi-service testing** in parallel  
✅ **Code coverage reporting** with Codecov integration  
✅ **Docker image building** with multi-platform support  
✅ **Security vulnerability scanning**  
✅ **Integration testing** with Docker Compose  
✅ **Automated deployments** to staging/production  
✅ **Dependency caching** for faster builds  
✅ **Notification system** for build status  

### Triggers

- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop` branches  
- Manual workflow dispatch

## 📊 Test Coverage

### Coverage Targets

| Service | Target Coverage | Test Types |
|---------|----------------|------------|
| OCR Service | 85%+ | Unit, Integration |
| AI Service | 85%+ | Unit, Integration |
| MCP Server | 90%+ | Unit, Integration |
| Backend | 80%+ | Unit, Integration, API |

### Coverage Reports

Coverage reports are generated in multiple formats:
- **Terminal output** during test runs
- **HTML reports** in `htmlcov/` directories
- **XML reports** for CI/CD integration
- **Codecov.io** for online tracking and PR comments

## 🧪 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Use mocks for external dependencies
- Fast execution (< 1 second per test)
- High code coverage focus

### Integration Tests (`@pytest.mark.integration`)  
- Test component interactions
- Use real or test external services
- Medium execution time (1-10 seconds per test)
- End-to-end workflow validation

### Slow Tests (`@pytest.mark.slow`)
- Tests involving large file processing
- AI model loading and inference
- Complex database operations
- Can be excluded for quick feedback loops

## 🛠️ Test Infrastructure

### Testing Dependencies

Each service includes:
- **pytest 8.3.2**: Core testing framework
- **pytest-asyncio 0.23.7**: Async test support
- **pytest-mock 3.12.0**: Advanced mocking capabilities
- **pytest-cov 4.0.0**: Code coverage reporting

### Mocking Strategy

- **External APIs**: HTTP requests mocked
- **Databases**: In-memory or temporary databases
- **File systems**: Temporary directories and files
- **AI models**: Mock embeddings and predictions
- **Redis**: Mock Redis client for job queues

### Test Data Generation

Tests automatically generate:
- Sample PDF documents
- Mock job data and responses
- Temporary files and directories
- Database records and schemas
- AI model embeddings and similarities

## 🐛 Debugging Tests

### Local Debugging
```bash
# Run specific test with verbose output
python -m pytest test_file.py::test_function -v -s

# Drop into debugger on failure
python -m pytest test_file.py --pdb

# Show local variables on failure
python -m pytest test_file.py --tb=long

# Run only failed tests from last run
python -m pytest --lf
```

### CI Debugging
- Check GitHub Actions logs for detailed output
- Review coverage reports for missing test scenarios
- Use workflow artifacts for debugging information
- Enable debug logging in test configurations

## 📈 Performance Testing

### Test Execution Performance
- Unit tests: < 30 seconds per service
- Integration tests: < 2 minutes per service  
- Full test suite: < 10 minutes total
- Docker builds: < 15 minutes total

### Optimization Strategies
- Parallel test execution
- Dependency caching
- Smart test selection
- Mock external services
- Incremental Docker builds

## 🔒 Security Testing

### Vulnerability Scanning
- **Trivy** scans Docker images for vulnerabilities
- **SARIF** format results uploaded to GitHub Security
- **Automated alerts** for critical vulnerabilities
- **Dependency scanning** for Python packages

### Security Best Practices
- No secrets in test code
- Isolated test environments
- Minimal container images
- Regular dependency updates

## 📚 Adding New Tests

### Guidelines
1. **Follow naming convention**: `test_*.py` files, `test_*` functions
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
3. **Include docstrings**: Explain test purpose and expected behavior
4. **Test both success and failure cases**: Edge cases and error conditions
5. **Use proper fixtures**: Reuse setup code and test data
6. **Mock external dependencies**: Keep tests isolated and fast
7. **Assert meaningful outcomes**: Verify business logic, not implementation details

### Test Template
```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test cases for new feature functionality"""

    @pytest.fixture
    def mock_dependency(self):
        """Mock external dependency"""
        return Mock()

    @pytest.mark.unit
    def test_success_case(self, mock_dependency):
        """Test successful operation"""
        # Arrange
        mock_dependency.method.return_value = "expected"
        
        # Act
        result = function_under_test(mock_dependency)
        
        # Assert
        assert result == "expected"
        mock_dependency.method.assert_called_once()

    @pytest.mark.unit
    def test_error_case(self, mock_dependency):
        """Test error handling"""
        mock_dependency.method.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            function_under_test(mock_dependency)
```

## 🚀 Getting Started

1. **Install dependencies** for each service:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests locally**:
   ```bash
   python run_tests.py --coverage
   ```

3. **Check coverage reports**:
   ```bash
   # Open HTML coverage report
   open htmlcov/index.html  # macOS
   start htmlcov\index.html # Windows
   ```

4. **Submit changes** with confidence knowing CI will validate everything!

## 📞 Support

- **Issues**: Create GitHub issues for test failures or coverage gaps
- **Documentation**: Refer to individual service `TESTING.md` files
- **CI/CD**: Check GitHub Actions logs for detailed information
- **Coverage**: Monitor Codecov.io for coverage trends

The comprehensive test suite ensures code quality, reliability, and maintainability across all microservices in the Magic Trick Analyzer platform! 🎭✨