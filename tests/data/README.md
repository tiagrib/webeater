# Test Data Files

This directory contains test data files used by the webeater test suite.

## Configuration Test Files

### Valid Configuration Files
- `valid_sample.json` - A complete valid configuration file for testing
- `valid_hint.json` - A valid hint configuration file

### Invalid Configuration Files
- `invalid_json.json` - Malformed JSON syntax for testing JSON parsing errors
- `invalid_data_types.json` - Valid JSON but invalid data types (string instead of number)
- `invalid_zero_width.json` - Valid JSON but violates validation (zero width)
- `invalid_negative_height.json` - Valid JSON but violates validation (negative height)
- `invalid_hint.json` - Malformed JSON in hint file for testing hint loading errors

## Usage

These files are used by the test suite to verify:

1. **JSON Parsing**: That malformed JSON is handled gracefully
2. **Data Validation**: That invalid data types are caught by Pydantic validation
3. **Business Logic Validation**: That domain-specific rules (positive dimensions) are enforced
4. **Error Handling**: That appropriate errors are raised with helpful messages

The test files simulate real-world scenarios where configuration files might be corrupted, manually edited incorrectly, or contain invalid values.