"""
Test suite for the webeater library.

This module provides comprehensive tests for:
- Configuration loading, saving, and validation
- Hint file loading and combination
- All config options and hint options

Run tests with:
    python -m unittest discover tests
    python run_tests.py
    python -m pytest tests/  (if pytest is installed)
"""

import unittest
from tests.test_config import TestWeatConfig, TestRemoveHints, TestMainContentHints
from tests.test_hints import TestHintsConfig


# Create a test suite that includes all test classes
def create_test_suite():
    """Create a comprehensive test suite for all webeater components."""
    suite = unittest.TestSuite()

    # Add config tests
    suite.addTest(unittest.makeSuite(TestWeatConfig))
    suite.addTest(unittest.makeSuite(TestRemoveHints))
    suite.addTest(unittest.makeSuite(TestMainContentHints))

    # Add hint tests
    suite.addTest(unittest.makeSuite(TestHintsConfig))

    return suite


def run_tests(verbosity=2):
    """Run all tests with specified verbosity."""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run all tests when this module is executed directly
    import sys

    print("Running webeater test suite...")
    print("=" * 50)

    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
