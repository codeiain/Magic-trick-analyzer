#!/usr/bin/env python3
"""
Test runner for AI Service
"""

import sys
import subprocess
import argparse


def run_tests(coverage=False, verbose=False, markers=None):
    """Run tests with optional coverage"""
    cmd = ["python", "-m", "pytest"]
    
    if coverage:
        cmd.extend(["--cov=ai_processor", "--cov-report=html", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    if markers:
        cmd.extend(["-m", markers])
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run AI service tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    
    args = parser.parse_args()
    
    markers = None
    if args.unit:
        markers = "unit"
    elif args.integration:
        markers = "integration"
    
    exit_code = run_tests(
        coverage=args.coverage,
        verbose=args.verbose,
        markers=markers
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()