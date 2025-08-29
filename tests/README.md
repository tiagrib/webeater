# Webeater Tests

This directory contains comprehensive unit tests for the webeater library using Python's `unittest` framework.

## Test Structure

- `test_config.py` - Tests for configuration loading, saving, validation, and all config options
- `test_hints.py` - Tests for hint file loading, combination, and all hint options  
- `test_suite.py` - Main test suite that combines all tests
- `__init__.py` - Makes tests directory a Python package

## Running Tests

### Option 1: Using the test runner script
```bash
# Run all tests
python run_tests.py

# Run specific test module
python run_tests.py config
python run_tests.py hints

# Run with verbose output
python run_tests.py -v
```

### Option 2: Using unittest discovery
```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_config
python -m unittest tests.test_hints

# Run with verbose output
python -m unittest discover tests -v
```

### Option 3: Using the test suite directly
```bash
python tests/test_suite.py
```

### Option 4: Using pytest (if installed)
```bash
pip install pytest
pytest tests/
```

## Test Coverage

### Configuration Tests (`test_config.py`)

**WeatConfig Tests:**
- ✅ Default config creation
- ✅ Loading from existing files
- ✅ Validation of positive window dimensions
- ✅ Extra hint files handling
- ✅ Duplicate hint file removal
- ✅ Config saving to file
- ✅ Excluding default values from saved config
- ✅ Invalid JSON handling
- ✅ Invalid data validation
- ✅ String representation
- ✅ Combined hints loading
- ✅ Combined hints retrieval

**RemoveHints Tests:**
- ✅ Default creation
- ✅ Creation with data

**MainContentHints Tests:**
- ✅ Default creation  
- ✅ Creation with data

### Hint Tests (`test_hints.py`)

**HintsConfig Tests:**
- ✅ Default creation
- ✅ Creation with data
- ✅ Loading from file successfully
- ✅ Legacy main format support (list → object conversion)
- ✅ File not found handling
- ✅ Invalid JSON handling
- ✅ Empty combined hints
- ✅ Single file combination
- ✅ Multiple file combination
- ✅ Direct hints combination
- ✅ Duplicate removal while preserving order
- ✅ Partial data handling
- ✅ Nonexistent files in combination
- ✅ String representation
- ✅ Actual project hint files loading
- ✅ Combined actual hints testing

## Test Configuration

All tests use temporary directories and files to avoid interfering with the actual project configuration. The tests include:

- **Mocking**: Uses `unittest.mock` to mock logging and file operations where needed
- **Temporary files**: Creates temporary directories and files for testing file operations
- **Cleanup**: Properly cleans up test fixtures in `tearDown()` methods
- **Real file testing**: Includes tests that verify the actual hint files in the project work correctly

## Adding New Tests

When adding new tests:

1. Create test methods starting with `test_`
2. Use descriptive test method names
3. Include docstrings explaining what is being tested
4. Use `setUp()` for test fixtures and `tearDown()` for cleanup
5. Add the test class to `test_suite.py` if creating a new test file
6. Follow the existing patterns for mocking and temporary file creation

## Test Data

The tests create their own test data and temporary files. They also verify that the actual hint files in the `hints/` directory work correctly:

- `hints/default.json` - Default removal and main content hints
- `hints/news.json` - News-specific hints  
- `hints/sports.json` - Sports-specific hints

## Dependencies

The tests require:
- Python 3.6+ (for unittest framework)
- `pydantic` (for validation testing)
- No additional test dependencies required