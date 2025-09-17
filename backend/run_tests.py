"""
Test runner script for the Magic Trick Analyzer backend

This script provides different ways to run the test suite.
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_type="all", coverage=True, verbose=True):
    """Run the test suite"""
    
    # Base pytest command - use current Python interpreter
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Test type selection
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "redis":
        cmd.extend(["-m", "redis"])
    elif test_type == "database":
        cmd.extend(["-m", "database"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type != "all":
        # Specific test file
        cmd.append(f"tests/{test_type}")
    
    # Add test directory if running all tests
    if test_type == "all":
        cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the tests
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run Magic Trick Analyzer tests")
    
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "redis", "database", "slow", "fast"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true", 
        help="Reduce verbosity"
    )
    
    parser.add_argument(
        "--file",
        help="Run a specific test file (e.g., test_job_queue.py)"
    )
    
    args = parser.parse_args()
    
    test_type = args.file if args.file else args.type
    coverage = not args.no_coverage
    verbose = not args.quiet
    
    return run_tests(test_type, coverage, verbose)


if __name__ == "__main__":
    sys.exit(main())