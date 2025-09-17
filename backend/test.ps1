# PowerShell Test Runner for Magic Trick Analyzer Backend
# Usage: .\test.ps1 [command] [args]

param(
    [string]$Command = "test",
    [string]$TestFile = "",
    [switch]$Coverage = $false,
    [switch]$Verbose = $false,
    [switch]$Help = $false
)

# Configuration
$PYTHON = "python"
$TEST_DIR = "tests"
$SRC_DIR = "src"
$COV_DIR = "htmlcov"

function Show-Help {
    Write-Host "Magic Trick Analyzer Backend Test Runner" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\test.ps1 [command] [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  test              - Run all tests"
    Write-Host "  test-cov          - Run tests with coverage report"
    Write-Host "  test-unit         - Run only unit tests"
    Write-Host "  test-integration  - Run only integration tests"
    Write-Host "  test-fast         - Run fast tests (exclude slow ones)"
    Write-Host "  coverage          - Generate coverage report only"
    Write-Host "  install-deps      - Install test dependencies"
    Write-Host "  clean             - Clean test artifacts"
    Write-Host "  help              - Show this help message"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -TestFile <file>  - Run specific test file"
    Write-Host "  -Coverage         - Include coverage report"
    Write-Host "  -Verbose          - Verbose output"
    Write-Host "  -Help             - Show this help"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\test.ps1 test-cov -Verbose"
    Write-Host "  .\test.ps1 test -TestFile test_job_queue.py"
    Write-Host "  .\test.ps1 coverage"
}

function Install-TestDeps {
    Write-Host "Installing test dependencies..." -ForegroundColor Cyan
    & $PYTHON -m pip install pytest pytest-asyncio pytest-mock pytest-cov fastapi-testclient
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Test dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install test dependencies" -ForegroundColor Red
        exit 1
    }
}

function Run-Tests {
    param([string[]]$Args)
    
    $cmd = @($PYTHON, "-m", "pytest")
    $cmd += $Args
    
    if ($Verbose) {
        $cmd += "-v"
    }
    
    Write-Host "Running: $($cmd -join ' ')" -ForegroundColor Cyan
    & $cmd[0] $cmd[1..($cmd.Length-1)]
}

function Clean-TestArtifacts {
    Write-Host "Cleaning test artifacts..." -ForegroundColor Cyan
    
    # Remove pytest cache
    if (Test-Path ".pytest_cache") {
        Remove-Item ".pytest_cache" -Recurse -Force
        Write-Host "Removed .pytest_cache" -ForegroundColor Yellow
    }
    
    # Remove coverage files
    if (Test-Path $COV_DIR) {
        Remove-Item $COV_DIR -Recurse -Force
        Write-Host "Removed $COV_DIR" -ForegroundColor Yellow
    }
    
    if (Test-Path ".coverage") {
        Remove-Item ".coverage" -Force
        Write-Host "Removed .coverage" -ForegroundColor Yellow
    }
    
    # Remove __pycache__ directories
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | ForEach-Object {
        $fullPath = Join-Path $PWD.Path $_
        if (Test-Path $fullPath) {
            Remove-Item $fullPath -Recurse -Force
            Write-Host "Removed $fullPath" -ForegroundColor Yellow
        }
    }
    
    # Remove .pyc files
    Get-ChildItem -Path . -Recurse -File -Name "*.pyc" | ForEach-Object {
        $fullPath = Join-Path $PWD.Path $_
        if (Test-Path $fullPath) {
            Remove-Item $fullPath -Force
        }
    }
    
    Write-Host "Test artifacts cleaned!" -ForegroundColor Green
}

function Open-CoverageReport {
    $reportPath = Join-Path $COV_DIR "index.html"
    if (Test-Path $reportPath) {
        Write-Host "Opening coverage report..." -ForegroundColor Cyan
        Start-Process $reportPath
    } else {
        Write-Host "Coverage report not found. Run tests with coverage first." -ForegroundColor Red
    }
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

# Check if Python is available
try {
    & $PYTHON --version | Out-Null
} catch {
    Write-Host "Python not found. Please ensure Python is installed and in PATH." -ForegroundColor Red
    exit 1
}

switch ($Command.ToLower()) {
    "test" {
        if ($TestFile) {
            $testPath = Join-Path $TEST_DIR $TestFile
            Run-Tests @($testPath)
        } elseif ($Coverage) {
            Run-Tests @($TEST_DIR, "--cov=$SRC_DIR", "--cov-report=html", "--cov-report=term-missing", "--cov-fail-under=80")
        } else {
            Run-Tests @($TEST_DIR)
        }
    }
    "test-cov" {
        Run-Tests @($TEST_DIR, "--cov=$SRC_DIR", "--cov-report=html", "--cov-report=term-missing", "--cov-fail-under=80")
        Write-Host ""
        Write-Host "Coverage report generated in $COV_DIR/" -ForegroundColor Green
    }
    "test-unit" {
        Run-Tests @($TEST_DIR, "-m", "unit")
    }
    "test-integration" {
        Run-Tests @($TEST_DIR, "-m", "integration")
    }
    "test-fast" {
        Run-Tests @($TEST_DIR, "-m", "not slow")
    }
    "coverage" {
        Run-Tests @($TEST_DIR, "--cov=$SRC_DIR", "--cov-report=html", "--cov-report=term-missing")
        Open-CoverageReport
    }
    "install-deps" {
        Install-TestDeps
    }
    "clean" {
        Clean-TestArtifacts
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Use '.\test.ps1 help' for available commands" -ForegroundColor Yellow
        exit 1
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Test execution completed successfully!" -ForegroundColor Green