#!/usr/bin/env python3
"""
Test runner for webeater project.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py config       # Run only config tests
    python run_tests.py hints        # Run only hint tests
    python run_tests.py -v           # Run with verbose output
"""

import sys
import unittest
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_all_tests(verbosity=1):
    """Run all tests in the tests directory."""
    loader = unittest.TestLoader()
    start_dir = "tests"
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_specific_tests(test_module, verbosity=1):
    """Run tests from a specific module."""
    loader = unittest.TestLoader()

    try:
        module_name = f"tests.test_{test_module}"
        suite = loader.loadTestsFromName(module_name)

        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        return result.wasSuccessful()
    except ImportError:
        print(f"Test module '{test_module}' not found.")
        return False


def main():
    """Main test runner function."""
    args = sys.argv[1:]
    verbosity = 1
    test_module = None

    # Parse arguments
    if "-v" in args or "--verbose" in args:
        verbosity = 2
        args = [arg for arg in args if arg not in ["-v", "--verbose"]]

    if args:
        test_module = args[0]

    print("=" * 70)
    print("WEBEATER TEST SUITE")
    print("=" * 70)

    if test_module:
        print(f"Running {test_module} tests...")
        success = run_specific_tests(test_module, verbosity)
    else:
        print("Running all tests...")
        success = run_all_tests(verbosity)

    print("=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
