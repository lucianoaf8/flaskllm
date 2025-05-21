# Flask LLM API - Project Guidelines & Best Practices

## Introduction

This document serves as the definitive guide for developing, maintaining, and extending the Flask LLM API project. These guidelines represent battle-tested approaches to ensure security, performance, maintainability, and resilience in production environments. All development should adhere to these principles.

## Table of Contents

1. [Project Structure & Architecture](#project-structure--architecture)
2. [Code Quality Standards](#code-quality-standards)
3. [API Design Principles](#api-design-principles)
4. [Security Requirements](#security-requirements)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Testing Methodology](#testing-methodology)
7. [Logging & Monitoring](#logging--monitoring)
8. [Performance Optimization](#performance-optimization)
9. [LLM Integration Guidelines](#llm-integration-guidelines)
10. [PythonAnywhere Deployment](#pythonanywhere-deployment)
11. [Development Workflow](#development-workflow)
12. [Troubleshooting Guide](#troubleshooting-guide)

## Project Structure & Architecture

### Package Structure

**DO:**
- Maintain the modular structure with clear separation of concerns
- Keep related functionality in the same module
- Use `__init__.py` files to expose only necessary imports

```
flaskllm/
├── api/                     # API-specific code
├── core/                    # Core application components
├── llm/                     # LLM integration logic
├── utils/                   # Utility functions
├── tests/                   # Test suite
├── app.py                   # Application entry point
└── wsgi.py                  # WSGI entry point
```

**DON'T:**
- Mix concerns across modules (e.g., don't put LLM logic in API routes)
- Create circular dependencies between modules
- Duplicate functionality across multiple modules

### Architecture Patterns

**DO:**
- Use the application factory pattern for Flask
- Implement dependency injection for testability
- Follow the repository pattern for any data access
- Use the strategy pattern for different LLM providers

**DON'T:**
- Create global state (use app context or dependency injection)
- Mix business logic with presentation logic
- Implement complex inheritance hierarchies

## Code Quality Standards

### Style Guidelines

- Follow PEP 8 for Python code style
- Use 4 spaces for indentation (not tabs)
- Maximum line length of 88 characters (Black default)
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Documentation Requirements

**Every file must include:**
- Module-level docstring explaining purpose
- Function/class docstrings with:
  - Description of functionality
  - Parameters with types and descriptions
  - Return values with types and descriptions
  - Exceptions that might be raised

**Example:**
```python
def process_prompt(
    self,
    prompt: str,
    source: Optional[PromptSource] = None,
    language: Optional[str] = None,
    type: Optional[PromptType] = None
) -> str:
    """
    Process a prompt using the LLM API.

    Args:
        prompt: The prompt to process
        source: Source of the prompt (email, meeting, etc.)
        language: Target language code (ISO 639-1)
        type: Type of processing to perform

    Returns:
        Processed result as a string

    Raises:
        LLMAPIError: If the LLM API returns an error
    """
```

### Type Hints

**DO:**
- Use type hints for all function parameters and return values
- Use `Optional[Type]` for optional parameters
- Use `Union[Type1, Type2]` for parameters that can be multiple types
- Use `typing.Dict`, `typing.List`, etc. for container types
- Use `Any` only when absolutely necessary

**DON'T:**
- Mix typed and untyped code
- Use `# type: ignore` comments unless absolutely necessary
- Ignore mypy errors without good reason

### Code Organization

**DO:**
- Limit function length to maximum 50 lines
- Limit class length to maximum 300 lines
- Extract complex logic into helper functions
- Group related functions/methods together
- Use consistent naming patterns

**DON'T:**
- Create "god" objects that do too many things
- Use deeply nested conditionals (extract to functions)
- Duplicate code (follow DRY principle)

## API Design Principles

### Endpoint Design

**DO:**
- Follow RESTful conventions
- Use versioned endpoints (e.g., `/api/v1/webhook`)
- Use HTTP methods appropriately:
  - GET for retrieving data
  - POST for creating/processing data
  - PUT for replacing data
  - PATCH for updating data
  - DELETE for removing data
- Use appropriate status codes consistently

**DON'T:**
- Create inconsistent URL patterns
- Use GET for operations with side effects
- Return incorrect status codes
- Create unnecessarily deep URL hierarchies

### Request/Response Format

**DO:**
- Validate all request input using schemas
- Return consistent JSON response structure:
```json
{
  "data": {...},        # Main response data
  "meta": {             # Optional metadata
    "processing_time": 1.23
  }
}
```
- For errors:
```json
{
  "error": "Error message",
  "details": "Detailed explanation",
  "code": "ERROR_CODE"
}
```
- Include appropriate HTTP headers (Content-Type, etc.)

**DON'T:**
- Return inconsistent response formats
- Return raw error messages from exceptions
- Expose sensitive information in error messages
- Return HTML or plain text instead of JSON

### Input Validation

**DO:**
- Validate all input using Pydantic models
- Check data types, ranges, patterns, and constraints
- Perform application-specific validation
- Return clear validation error messages

**DON'T:**
- Trust client input without validation
- Manually validate input without a schema
- Allow invalid values to propagate through the system

## Security Requirements

### Authentication & Authorization

**DO:**
- Use strong API tokens with sufficient entropy
- Store tokens securely in environment variables
- Validate tokens on every request
- Log authentication failures with client IPs
- Implement rate limiting for authentication attempts

**DON'T:**
- Hardcode tokens in the source code
- Use simple or predictable tokens
- Store tokens in plain text files
- Expose token values in logs or error messages

### Data Handling

**DO:**
- Sanitize and validate all input
- Escape content that may contain malicious code
- Apply the principle of least privilege
- Use secure headers in responses
- Implement request size limits

**DON'T:**
- Store sensitive data without encryption
- Return sensitive data in responses
- Trust user-provided filenames or paths
- Log sensitive information

### API Protection

**DO:**
- Implement rate limiting for all endpoints
- Set appropriate timeouts for all operations
- Validate content types and reject unexpected ones
- Implement audit logging for sensitive operations
- Use HTTPS for all communication

**DON'T:**
- Allow unlimited requests from a single source
- Accept arbitrary content types
- Allow open CORS access without restrictions
- Expose detailed error information in production

## Error Handling Strategy

### Approach

**DO:**
- Use custom exception classes for different error types
- Catch specific exceptions rather than broad ones
- Convert exceptions to appropriate HTTP responses
- Include appropriate error codes and messages
- Log exceptions with context for debugging

**DON'T:**
- Use generic try/except blocks without specific exception types
- Swallow exceptions without logging
- Return inconsistent error formats
- Expose stack traces or implementation details in errors

### Exception Hierarchy

Maintain a consistent exception hierarchy:

```
APIError (base class)
├── InvalidInputError
├── AuthenticationError
├── RateLimitExceeded
├── LLMAPIError
└── InternalError
```

### Error Response Format

```json
{
  "error": "Brief error message",
  "details": "More detailed explanation",
  "code": "ERROR_CODE"
}
```

## Testing Methodology

### Test Types

1. **Unit Tests**
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on specific functionality

2. **Integration Tests**
   - Test interaction between components
   - Use test doubles for external services
   - Verify correct component integration

3. **End-to-End Tests**
   - Test complete API endpoints
   - Verify correct HTTP responses
   - Test authentication and error handling

### Test Coverage Requirements

- Minimum 80% code coverage
- 100% coverage for critical paths:
  - Authentication logic
  - Input validation
  - Error handling
  - LLM integration

### Testing Best Practices

**DO:**
- Write tests before implementing features (TDD)
- Use fixtures for test setup
- Use parametrized tests for multiple test cases
- Test edge cases and error conditions
- Test performance and resource usage

**DON'T:**
- Skip testing of error conditions
- Write tests that depend on external services
- Create brittle tests that break with minor changes
- Duplicate test setup code

## Logging & Monitoring

### Logging Strategy

**DO:**
- Use structured logging (JSON format in production)
- Log at appropriate levels:
  - DEBUG: Detailed debugging information
  - INFO: General operational information
  - WARNING: Warning events that might need attention
  - ERROR: Error events that might still allow the application to continue
  - CRITICAL: Critical events that require immediate attention
- Include context in log messages (request ID, user info, etc.)
- Rotate log files to prevent disk space issues

**DON'T:**
- Log sensitive information (API keys, tokens, etc.)
- Use print statements for debugging
- Log too much information in production
- Mix log levels inappropriately

### Log Message Format

```
[TIMESTAMP] [LEVEL] [MODULE] [REQUEST_ID] - Message
```

Example:
```
[2025-05-20 12:34:56] [INFO] [api.routes] [req-123] - Processing prompt (length: 250 chars)
```

### Monitoring Strategy

**DO:**
- Monitor application health (response times, error rates)
- Set up alerts for critical errors
- Track LLM API usage and costs
- Monitor system resources (CPU, memory, disk)
- Set up uptime monitoring

**DON'T:**
- Rely solely on log files for monitoring
- Ignore increasing error rates
- Overlook performance degradation

## Performance Optimization

### Response Time

**DO:**
- Set appropriate timeouts for LLM API calls
- Use caching for repeated or similar requests
- Implement asynchronous processing for long-running tasks
- Optimize database queries (if using a database)
- Use connection pooling for external services

**DON'T:**
- Block the main thread with long-running operations
- Make sequential API calls when parallel is possible
- Load unnecessary data

### Resource Usage

**DO:**
- Limit request and response payload sizes
- Close connections and resources properly
- Use streaming responses for large payloads
- Profile memory usage regularly
- Optimize database connections

**DON'T:**
- Store large data in memory unnecessarily
- Leave connections open after use
- Ignore memory leaks

### Caching Strategy

**DO:**
- Cache repeated LLM API calls
- Implement cache invalidation strategies
- Use cache expiration times
- Consider distributed caching for scaling

**DON'T:**
- Cache sensitive data
- Cache everything without consideration
- Ignore cache hit ratio metrics

## LLM Integration Guidelines

### Provider Management

**DO:**
- Use the factory pattern for multiple LLM providers
- Abstract provider-specific details
- Implement retries with exponential backoff
- Set appropriate timeouts
- Track API usage and costs

**DON'T:**
- Hardcode provider-specific logic in business code
- Send sensitive data in prompts
- Ignore rate limits imposed by providers

### Prompt Engineering

**DO:**
- Use consistent system prompts for similar tasks
- Implement prompt templates for different use cases
- Validate and sanitize user input before including in prompts
- Test prompt effectiveness with different inputs
- Document prompt templates and their purposes

**DON'T:**
- Include sensitive information in prompts
- Use excessively long prompts
- Ignore context limitations of models
- Change prompt formats without testing

### Response Processing

**DO:**
- Validate LLM responses before returning to clients
- Implement fallbacks for unexpected responses
- Process responses according to requested formats
- Handle streaming responses appropriately
- Cache responses when appropriate

**DON'T:**
- Return raw LLM responses without validation
- Ignore malformed or inappropriate responses
- Assume response formats will always be consistent

## PythonAnywhere Deployment

### Configuration

**DO:**
- Use the correct WSGI configuration
- Set up proper virtual environment paths
- Configure static file serving appropriately
- Use environment variables for secrets
- Set appropriate file permissions

**DON'T:**
- Store secrets in code or unprotected files
- Use different Python versions in development and production
- Ignore PythonAnywhere resource limits

### Resource Management

**DO:**
- Monitor CPU and memory usage
- Optimize database connections
- Use efficient logging (limit file sizes)
- Plan for scaling if needed
- Use scheduled tasks for maintenance

**DON'T:**
- Create long-running processes without consideration
- Ignore file size and disk space limitations
- Overlook database connection limits

### Deployment Process

**DO:**
- Use version control for all code
- Test thoroughly before deployment
- Use a consistent deployment checklist
- Update dependencies carefully
- Monitor application after deployment

**DON'T:**
- Deploy untested code
- Make direct changes on the server
- Ignore deprecation warnings
- Skip database migrations

## Development Workflow

### Version Control

**DO:**
- Use feature branches for development
- Write meaningful commit messages
- Review code before merging
- Tag releases with version numbers
- Keep the main branch stable

**DON'T:**
- Commit directly to main branch
- Commit large binary files
- Skip code reviews
- Commit temporary or generated files

### Environment Management

**DO:**
- Use virtual environments for isolation
- Keep development and production environments similar
- Document environment setup process
- Use requirements.txt or pyproject.toml for dependencies
- Pin dependency versions

**DON'T:**
- Use global Python installations
- Mix different Python versions
- Install unnecessary dependencies
- Use different packages in development and production

### Code Review Process

**DO:**
- Review all code changes before merging
- Use a consistent review checklist
- Focus on security, performance, and maintainability
- Automate code style and linting checks
- Ensure tests are included and passing

**DON'T:**
- Skip reviews for "small" changes
- Approve code that doesn't meet standards
- Focus only on implementation details
- Ignore non-functional requirements

## Troubleshooting Guide

### Common Issues and Solutions

#### LLM API Failures

**Symptoms:**
- 502 errors from the API
- Timeout errors
- Empty or malformed responses

**Solutions:**
1. Check API key validity and permissions
2. Verify LLM provider status (service outages)
3. Check network connectivity
4. Review rate limits and quotas
5. Examine request payload for issues
6. Increase timeout values for large prompts

#### Authentication Problems

**Symptoms:**
- 401 errors from the API
- "Unauthorized" error messages
- Authentication failures in logs

**Solutions:**
1. Verify API token is correct
2. Check token is being sent in the correct header
3. Ensure environment variables are set correctly
4. Check for token expiration (if using JWTs)
5. Review authentication middleware for issues

#### Performance Issues

**Symptoms:**
- Slow response times
- High CPU or memory usage
- Request timeouts

**Solutions:**
1. Profile application to identify bottlenecks
2. Check LLM provider response times
3. Review database queries (if applicable)
4. Implement caching for frequent requests
5. Optimize request processing pipeline
6. Consider asynchronous processing for heavy tasks

### Debugging Strategy

**DO:**
- Use logging strategically to identify issues
- Check logs for error messages and context
- Reproduce issues in development environment
- Isolate components to find the source of issues
- Use debugging tools (debugger, profiler, etc.)

**DON'T:**
- Add temporary debugging code to production
- Ignore log messages or warnings
- Make multiple changes at once when debugging
- Assume the cause of an issue without evidence

### Incident Response

**When a production issue occurs:**

1. **Assess Impact**
   - Determine severity and scope
   - Identify affected users or functionality
   - Estimate business impact

2. **Contain the Issue**
   - Consider temporary mitigations
   - Decide if a rollback is necessary
   - Communicate with stakeholders

3. **Investigate and Resolve**
   - Identify root cause through logs and monitoring
   - Develop and test a fix
   - Deploy the solution

4. **Post-Incident Review**
   - Document what happened
   - Identify preventive measures
   - Update monitoring and alerting
   - Share learnings with the team

## Final Thoughts

This guide is a living document. As the project evolves and new challenges are encountered, these guidelines should be updated to reflect the latest best practices and lessons learned.

Remember the core principles:
- Security first, always
- Reliability and resilience in all components
- Clear, maintainable code
- Comprehensive testing
- Thoughtful error handling
- Performance optimization where it matters

Following these guidelines will ensure a robust, secure, and maintainable Flask LLM API that can evolve with changing requirements and scale to meet future needs.
