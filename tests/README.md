# Testing Guide

This document provides comprehensive information about testing the rsync-tailscale-docker project.

## Test Suite Overview

The project includes a complete testing framework with multiple test types:

- **Unit Tests**: Test individual functions and components in isolation
- **Integration Tests**: Test component interactions and system integration
- **End-to-End Tests**: Test complete workflows from start to finish
- **Performance Tests**: Verify system performance under various conditions

## Test Structure

```
tests/
├── conftest.py                          # Pytest configuration and fixtures
├── unit/                                # Unit tests
│   ├── test_log_parsing.py             # Log parsing functionality
│   ├── test_path_validation.py         # Path validation and security
│   └── test_web_handlers.py            # Web interface handlers
├── integration/                         # Integration tests
│   ├── test_ssh_connection.py          # SSH connectivity testing
│   ├── test_sync_process.py            # Sync process workflow
│   └── test_e2e_workflow.py            # End-to-end system tests
├── pytest.ini                          # Pytest configuration
├── requirements-test.txt               # Test dependencies
└── run_tests.sh                        # Test runner script
```

## Running Tests

### Quick Start

```bash
# Make test runner executable (first time only)
chmod +x run_tests.sh

# Install test dependencies
./run_tests.sh install

# Run all tests
./run_tests.sh all

# Run with coverage report
./run_tests.sh coverage
```

### Test Runner Commands

The `run_tests.sh` script provides convenient commands:

```bash
# Run specific test types
./run_tests.sh unit           # Unit tests only
./run_tests.sh integration   # Integration tests only
./run_tests.sh e2e           # End-to-end tests only

# Run tests by speed
./run_tests.sh quick         # Fast tests only (exclude slow tests)
./run_tests.sh slow          # Slow tests only

# Run specific tests
./run_tests.sh specific tests/unit/test_log_parsing.py
./run_tests.sh marker ssh    # Tests marked with 'ssh'

# Quality and reporting
./run_tests.sh lint          # Code quality checks
./run_tests.sh report        # Generate comprehensive reports
./run_tests.sh clean         # Clean test artifacts
```

### Direct Pytest Commands

You can also run pytest directly:

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_log_parsing.py

# Run by markers
pytest -m "unit and not slow"
pytest -m "integration"

# Run with specific options
pytest -x --tb=short  # Stop on first failure, short traceback
pytest -s            # Don't capture output (useful for debugging)
```

## Test Markers

Tests are organized using markers:

- `unit`: Unit tests
- `integration`: Integration tests  
- `e2e`: End-to-end tests
- `slow`: Long-running tests
- `ssh`: Tests requiring SSH connectivity
- `docker`: Tests requiring Docker
- `network`: Tests requiring network access

## Test Coverage

The test suite aims for comprehensive coverage:

- **Unit Test Coverage**: Individual functions and methods
- **Integration Coverage**: Component interactions
- **Error Scenario Coverage**: Error handling and edge cases
- **Security Testing**: Input validation and injection prevention
- **Performance Testing**: Resource usage and scalability

### Coverage Reports

Coverage reports are generated in multiple formats:

- **Terminal**: Quick overview displayed after test runs
- **HTML**: Detailed interactive report in `htmlcov/index.html`
- **XML**: Machine-readable format in `reports/coverage.xml`

## Test Categories

### Unit Tests

#### `test_log_parsing.py`
Tests log parsing functionality:
- Log file reading and parsing
- Error detection and line number extraction
- Log formatting and display
- Performance with large log files

#### `test_path_validation.py`  
Tests path validation and security:
- Path injection prevention
- Input sanitization
- Directory traversal protection
- File permission validation

#### `test_web_handlers.py`
Tests web interface handlers:
- HTTP request/response handling
- Status endpoint functionality
- Log retrieval and formatting
- Security headers validation

### Integration Tests

#### `test_ssh_connection.py`
Tests SSH connectivity:
- Connection establishment
- Authentication validation
- Timeout handling
- Error scenario testing

#### `test_sync_process.py`
Tests complete sync workflow:
- Route configuration processing
- Rsync command execution
- Error handling and recovery
- Performance monitoring

#### `test_e2e_workflow.py`
Tests end-to-end system functionality:
- Complete workflow execution
- Docker container integration
- File system operations
- Resource usage monitoring

## Mock Strategy

The test suite uses comprehensive mocking:

- **Subprocess Commands**: Mock rsync, ssh, and docker commands
- **File System Operations**: Mock file I/O for isolated testing
- **Network Operations**: Mock HTTP requests and SSH connections
- **Time-Dependent Operations**: Mock time functions for consistent testing

## Test Data Management

Test fixtures provide:

- **Temporary Workspaces**: Isolated file system environments
- **Sample Configuration Files**: Valid and invalid configuration examples
- **Mock Log Content**: Various log scenarios and edge cases
- **Test File Structures**: Realistic directory structures with test files

## Performance Testing

Performance tests verify:

- **Log File Processing**: Handling large log files efficiently
- **Memory Usage**: Resource consumption during operations
- **Concurrent Operations**: Thread safety and concurrent access
- **Response Times**: Web interface performance

## Security Testing

Security-focused tests include:

- **Input Validation**: Testing against malicious inputs
- **Path Traversal**: Directory traversal attack prevention
- **Command Injection**: Shell command injection prevention
- **File Permission**: Proper file access controls

## Debugging Tests

For debugging failing tests:

```bash
# Run with detailed output
pytest -s -vv tests/specific_test.py

# Drop into debugger on failure
pytest --pdb tests/specific_test.py

# Run single test method
pytest tests/unit/test_log_parsing.py::TestLogParsing::test_parse_log_entries

# Show local variables on failure
pytest --tb=long tests/specific_test.py
```

## Continuous Integration

The test suite is designed for CI/CD integration:

- **Fast Feedback**: Quick tests run first
- **Parallel Execution**: Tests can run in parallel
- **Multiple Reports**: JUnit XML for CI systems
- **Environment Isolation**: Tests don't depend on external services

## Test Best Practices

### Writing Tests

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one specific behavior
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Isolate units under test
5. **Test Edge Cases**: Include boundary conditions and error scenarios

### Test Organization

1. **Logical Grouping**: Group related tests in classes
2. **Consistent Fixtures**: Use fixtures for common setup
3. **Appropriate Markers**: Mark tests with relevant markers
4. **Documentation**: Include docstrings for complex tests

### Performance Considerations

1. **Fast Unit Tests**: Keep unit tests fast for quick feedback
2. **Selective Integration**: Run integration tests when needed
3. **Resource Cleanup**: Ensure proper cleanup of test resources
4. **Parallel Safe**: Write tests that can run in parallel

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure test runner has proper file permissions
2. **Missing Dependencies**: Install test requirements with `./run_tests.sh install`
3. **SSH Connection Failures**: Integration tests mock SSH by default
4. **Docker Not Available**: Docker tests are marked and can be skipped

### Environment Setup

```bash
# Ensure Python 3.8+ is available
python3 --version

# Install test dependencies
pip install -r requirements-test.txt

# Verify pytest installation
pytest --version

# Check project structure
ls -la tests/
```

### Test Isolation

Tests are designed to be isolated:

- **No External Dependencies**: Tests mock external services
- **Temporary Files**: Use temporary directories for file operations
- **Clean State**: Each test starts with a clean environment
- **Resource Cleanup**: Fixtures handle proper cleanup

## Contributing Tests

When adding new features:

1. **Write Tests First**: Consider TDD approach
2. **Cover Edge Cases**: Think about failure scenarios
3. **Update Documentation**: Update this guide for new test patterns
4. **Run Full Suite**: Ensure new tests don't break existing ones

### Test Review Checklist

- [ ] Tests are properly isolated
- [ ] External dependencies are mocked
- [ ] Edge cases are covered
- [ ] Tests have descriptive names
- [ ] Appropriate markers are used
- [ ] Documentation is updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Support

For testing issues or questions:

1. Check this documentation first
2. Review existing test patterns in the codebase  
3. Examine test output and error messages carefully
4. Use debugging techniques outlined above