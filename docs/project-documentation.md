# FlaskLLM API

## Project Documentation

### Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Usage Examples](#usage-examples)
6. [Deployment Guide](#deployment-guide)
7. [Development Guide](#development-guide)
8. [Testing Guide](#testing-guide)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)
11. [Contributing Guidelines](#contributing-guidelines)

---

## Project Overview

FlaskLLM API is a secure, scalable, and maintainable Python Flask-based API for processing prompts using Large Language Models (LLMs). It provides a robust middleware layer between client applications (like Excel with Office Scripts) and LLM providers (like OpenAI, Anthropic, etc.).

### Purpose

The API accepts prompts from various sources, sends them to an LLM service, processes the responses, and returns the results in a structured JSON format. This enables integration of LLM capabilities into business workflows without direct API access from client applications.

### Key Features

- Secure API token authentication
- Configurable LLM provider integration (OpenAI, Anthropic, etc.)
- Robust error handling and logging
- Input validation using Pydantic schemas
- Rate limiting and request throttling
- Comprehensive test coverage
- Easy deployment to PythonAnywhere

### Use Cases

- Process email contents via Office Scripts and Excel
- Generate summaries of meeting transcripts
- Extract keywords or entities from documents
- Translate content to different languages
- Custom text processing based on configured prompt templates

---

## Architecture

FlaskLLM follows a modular architecture with clear separation of concerns, making it extensible and maintainable.

### Component Overview

```
flaskllm/
├── api/                     # API-specific code
│   ├── __init__.py
│   ├── v1/                  # API versioning
│   │   ├── __init__.py
│   │   ├── routes.py        # API route definitions
│   │   ├── schemas.py       # Request/response schemas
│   │   └── validators.py    # Input validation
├── core/                    # Core application components
│   ├── __init__.py
│   ├── auth.py              # Authentication logic
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   ├── logging.py           # Logging configuration
│   └── middleware.py        # Custom middleware
├── llm/                     # LLM integration logic
│   ├── __init__.py
│   ├── openai_handler.py    # OpenAI integration
│   ├── anthropic_handler.py # Claude integration (if implemented)
│   └── factory.py           # LLM factory pattern
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── rate_limiter.py      # Rate limiting
│   ├── security.py          # Security helpers
│   └── validation.py        # General validators
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures
├── app.py                   # Application entry point
├── wsgi.py                  # WSGI entry point for production
├── .env.example             # Example environment variables
├── requirements.txt         # Dependencies
└── README.md                # Project documentation
```

### Design Patterns

- **Application Factory Pattern**: The Flask application is created using a factory function to enable configuration and testing
- **Strategy Pattern**: Different LLM providers are implemented using the strategy pattern with a common interface
- **Repository Pattern**: Any data access follows the repository pattern for abstraction
- **Dependency Injection**: Dependencies are injected for better testability

### Request Flow

1. Client sends a request to the API endpoint
2. Authentication middleware verifies API token
3. Request validation ensures correct input format
4. Rate limiting checks prevent abuse
5. LLM handler processes the request
6. Response is formatted and returned as JSON

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- An API key for at least one LLM provider (OpenAI, Anthropic, etc.)
- Virtual environment tool (venv, conda, etc.)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/flaskllm.git
   cd flaskllm
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a .env file**:
   ```bash
   cp .env.example .env
   ```

5. **Edit the .env file with your configuration**:
   ```
   # Environment
   ENVIRONMENT=development
   DEBUG=True

   # API Security
   API_TOKEN=your_secure_random_token
   ALLOWED_ORIGINS=*

   # LLM Configuration
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4

   # Request Configuration
   REQUEST_TIMEOUT=30
   MAX_PROMPT_LENGTH=4000

   # Rate Limiting
   RATE_LIMIT_ENABLED=True
   RATE_LIMIT=60
   ```

6. **Run the development server**:
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development, testing, production) | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `API_TOKEN` | Authentication token for API access | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `LLM_PROVIDER` | LLM provider to use (openai, anthropic) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | Required if using OpenAI |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `REQUEST_TIMEOUT` | Timeout for LLM API requests in seconds | `30` |
| `MAX_PROMPT_LENGTH` | Maximum allowed prompt length | `4000` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `True` |
| `RATE_LIMIT` | Number of requests allowed per minute | `60` |

---

## API Reference

### Authentication

All API requests require authentication using an API token. The token should be provided in the `X-API-Token` header or as an `api_token` query parameter.

Example:
```
X-API-Token: your_api_token
```

### Endpoints

#### Health Check

```
GET /api/v1/health
```

Returns the health status of the API.

**Response:** HTTP 200
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production"
}
```

#### Process Prompt

```
POST /api/v1/webhook
```

Process a prompt with the configured LLM provider.

**Request Body:**
```json
{
  "prompt": "Summarize this meeting: we need to reduce hiring.",
  "source": "meeting",
  "language": "en",
  "type": "summary"
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | The text to process (max 4000 chars) |
| `source` | string | No | Source of the prompt (email, meeting, document, chat, other) |
| `language` | string | No | Target language code (ISO 639-1) |
| `type` | string | No | Type of processing (summary, keywords, sentiment, entities, translation, custom) |

**Response:** HTTP 200
```json
{
  "summary": "The company plans to reduce hiring to cut costs.",
  "processing_time": 1.25
}
```

**Error Responses:**

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid input data |
| 401 | Authentication failed |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | LLM API error |

---

## Usage Examples

### Process a Prompt with cURL

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your_api_token" \
  -d '{"prompt":"Summarize this meeting: we need to reduce hiring."}' \
  http://localhost:5000/api/v1/webhook
```

### Process a Prompt with Python Requests

```python
import requests

url = "http://localhost:5000/api/v1/webhook"
headers = {
    "Content-Type": "application/json",
    "X-API-Token": "your_api_token"
}
data = {
    "prompt": "Summarize this meeting: we need to reduce hiring.",
    "source": "meeting",
    "language": "en",
    "type": "summary"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(result["summary"])
```

### Process a Prompt with JavaScript Fetch

```javascript
async function processPrompt(prompt) {
  const response = await fetch('http://localhost:5000/api/v1/webhook', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Token': 'your_api_token'
    },
    body: JSON.stringify({
      prompt: prompt,
      source: 'email',
      language: 'en',
      type: 'summary'
    })
  });

  const data = await response.json();
  return data.summary;
}

// Usage
processPrompt("Summarize this email: We will meet on Tuesday.")
  .then(summary => console.log(summary))
  .catch(error => console.error('Error:', error));
```

### Office Script (Excel) Integration

```typescript
/**
 * Process email content using the LLM API.
 * @param emailContent The email content to process
 * @customfunction
 */
async function ProcessEmail(emailContent: string): Promise {
  // API configuration
  const apiUrl = "https://yourusername.pythonanywhere.com/api/v1/webhook";
  const apiToken = "your_api_token";

  // Request configuration
  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Token": apiToken
    },
    body: JSON.stringify({
      prompt: emailContent,
      source: "email",
      type: "summary"
    })
  });

  // Check for errors
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  // Process response
  const result = await response.json();
  return result.summary;
}
```

---

## Deployment Guide

### Deploying to PythonAnywhere

1. **Create a PythonAnywhere Account:**
   - Sign up at [PythonAnywhere](https://www.pythonanywhere.com/)
   - Log in to your account

2. **Set Up a Web App:**
   - Go to the Web tab in your dashboard
   - Click "Add a new web app"
   - Choose "Manual configuration" (not "Flask")
   - Select Python 3.10

3. **Clone the Repository:**
   - Open a Bash console from the dashboard
   - Clone your repository:
     ```bash
     git clone https://github.com/yourusername/flaskllm.git
     ```
   - Set up the virtual environment:
     ```bash
     cd flaskllm
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```

4. **Configure Environment Variables:**
   - Create a `.env` file in your project directory:
     ```
     ENVIRONMENT=production
     DEBUG=False
     API_TOKEN=your_secure_random_token
     LLM_PROVIDER=openai
     OPENAI_API_KEY=your_openai_api_key
     OPENAI_MODEL=gpt-4
     REQUEST_TIMEOUT=30
     MAX_PROMPT_LENGTH=4000
     RATE_LIMIT_ENABLED=True
     RATE_LIMIT=60
     ```

5. **Configure the WSGI File:**
   - Open the WSGI configuration file from the Web tab
   - Replace its contents with:
     ```python
     import sys
     import os

     # Add your project directory to the path
     path = '/home/yourusername/flaskllm'
     if path not in sys.path:
         sys.path.append(path)

     # Set virtual environment path
     os.environ['VIRTUAL_ENV'] = '/home/yourusername/flaskllm/venv'
     os.environ['PATH'] = '/home/yourusername/flaskllm/venv/bin:' + os.environ['PATH']

     # Import the application
     from wsgi import application
     ```

6. **Set Up Static Files (if needed):**
   - In the Web tab, add a static files mapping:
     - URL: `/static/`
     - Directory: `/home/yourusername/flaskllm/static/`

7. **Reload Your Web App:**
   - Click the "Reload" button in the Web tab

8. **Verify Deployment:**
   - Test the health check endpoint:
     ```bash
     curl https://yourusername.pythonanywhere.com/api/v1/health
     ```

### PythonAnywhere Limitations and Considerations

- **Free Plan Limitations:**
  - CPU seconds quota (limited processing time)
  - Memory limitations
  - Web application is put to sleep after inactivity

- **File Size and Storage:**
  - Limited disk space
  - Manage log file sizes

- **Security:**
  - Use HTTPS by default
  - Set proper file permissions for sensitive files:
    ```bash
    chmod 600 .env
    ```

- **Database Connections:**
  - Close connections properly to avoid leaks
  - Use connection pooling if needed

- **Scheduled Tasks:**
  - Use PythonAnywhere's scheduled tasks for maintenance
  - For example, log rotation or cache clearing

---

## Development Guide

### Adding a New LLM Provider

1. **Create a new handler class:**
   - Create a file in the `llm/` directory (e.g., `llm/anthropic_handler.py`)
   - Implement the required interface with at least a `process_prompt` method

2. **Update the LLM factory:**
   - Add the new provider to the `LLMProvider` enum in `core/config.py`
   - Update the `LLMFactory.create()` method to handle the new provider

3. **Update configuration:**
   - Add the relevant environment variables in `.env.example`
   - Update the `Settings` class in `core/config.py`

### Adding a New Endpoint

1. **Define the route:**
   - Add a new route function in `api/v1/routes.py`
   - Use the appropriate decorators for authentication, validation, etc.

2. **Create request/response schemas:**
   - Add schemas to `api/v1/schemas.py`
   - Define all required fields and validation rules

3. **Implement the business logic:**
   - Either within the route function or in a dedicated module
   - Follow the existing patterns for error handling and logging

### Code Style and Quality

- **Linting and Formatting:**
  - Use `black` for consistent code formatting:
    ```bash
    black .
    ```
  - Use `flake8` for linting:
    ```bash
    flake8 .
    ```

- **Type Checking:**
  - Use `mypy` for static type checking:
    ```bash
    mypy .
    ```

- **Documentation:**
  - Document all modules, classes, and functions with docstrings
  - Keep the API documentation updated when making changes

---

## Testing Guide

### Running Tests

Use pytest to run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=flaskllm

# Run specific test files
pytest tests/unit/test_openai_handler.py

# Run specific test functions
pytest tests/unit/test_openai_handler.py::TestOpenAIHandler::test_process_prompt_success
```

### Writing Tests

#### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Focus on specific functionality

Example:
```python
# tests/unit/test_openai_handler.py
import pytest
from unittest.mock import patch, MagicMock

from llm.openai_handler import OpenAIHandler

class TestOpenAIHandler:
    @pytest.fixture
    def handler(self):
        return OpenAIHandler(api_key="test_key", model="gpt-3.5-turbo")

    @patch("openai.OpenAI")
    def test_process_prompt_success(self, mock_openai, handler):
        # Setup mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call the method
        result = handler.process_prompt("Test prompt")

        # Verify result
        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()
```

#### Integration Tests

- Test interaction between components
- Verify correct API behavior
- Test authentication and error handling

Example:
```python
# tests/integration/test_api.py
import pytest
import json
from unittest.mock import patch

from app import create_app
from core.config import Settings, EnvironmentType

@pytest.fixture
def client():
    # Create test settings
    test_settings = Settings(
        environment=EnvironmentType.TESTING,
        api_token="test_token",
        openai_api_key="test_key"
    )

    # Create app with test settings
    app = create_app(test_settings)

    with app.test_client() as client:
        yield client

def test_webhook_success(client):
    # Mock the LLM handler
    with patch("llm.factory.get_llm_handler") as mock_get_handler:
        mock_handler = mock_get_handler.return_value
        mock_handler.process_prompt.return_value = "Test response"

        # Make request
        response = client.post(
            "/api/v1/webhook",
            json={"prompt": "Test prompt"},
            headers={"X-API-Token": "test_token"}
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["summary"] == "Test response"
```

---

## Troubleshooting

### Common Issues and Solutions

#### API Authentication Issues

**Symptoms:**
- 401 Unauthorized responses
- "Authentication failed" error messages

**Solutions:**
1. Verify the API token is correct in both the server configuration and client requests
2. Check that the token is being sent in the correct header (`X-API-Token`)
3. Ensure environment variables are correctly set
4. Check logs for authentication failure details

#### LLM API Connection Issues

**Symptoms:**
- 502 Bad Gateway responses
- Timeout errors
- Empty or malformed responses

**Solutions:**
1. Verify the LLM provider API key is valid
2. Check the LLM provider's service status
3. Increase request timeout values for large prompts
4. Check network connectivity from the server to the LLM provider
5. Review request payload for formatting issues

#### Rate Limiting Issues

**Symptoms:**
- 429 Too Many Requests responses
- "Rate limit exceeded" error messages

**Solutions:**
1. Reduce the frequency of requests from clients
2. Increase the rate limit in configuration if appropriate
3. Implement client-side retry logic with exponential backoff
4. Consider implementing request queueing for high-volume scenarios

#### PythonAnywhere Specific Issues

**Symptoms:**
- Application not starting
- "Worker failed to start" errors
- Unexpected 500 errors

**Solutions:**
1. Check the error log in the PythonAnywhere Web tab
2. Verify the WSGI file configuration is correct
3. Check the virtual environment path is correct
4. Ensure all dependencies are installed in the virtual environment
5. Check for PythonAnywhere resource limits (CPU/memory)

### Debugging Tools

- **Log Analysis:**
  - Check application logs for error messages
  - Look for patterns in failed requests

- **API Testing:**
  - Use Postman or curl to test endpoints directly
  - Verify request/response formats

- **Performance Profiling:**
  - Monitor response times for different request types
  - Check for memory leaks or resource bottlenecks

---

## Security Considerations

### API Token Security

- Generate strong, random API tokens with sufficient entropy
- Rotate tokens periodically
- Never share tokens in code repositories or public channels
- Store tokens securely in environment variables or secret management systems

### Input Validation

- Validate all input using Pydantic schemas
- Sanitize potentially dangerous content
- Implement size limits for requests
- Verify content types and formats

### Data Privacy

- Do not log sensitive information
- Do not include sensitive data in prompts to LLM services
- Follow applicable data protection regulations
- Consider data residency requirements when choosing LLM providers

### Rate Limiting and Throttling

- Implement rate limiting to prevent abuse
- Set different limits for different endpoints
- Consider IP-based and token-based limiting
- Use exponential backoff for retries

### HTTPS and Transport Security

- Use HTTPS for all API communication
- Configure secure headers (Content-Security-Policy, etc.)
- Implement proper CORS configuration
- Use TLS 1.2 or higher

---

## Contributing Guidelines

### Pull Request Process

1. **Fork the Repository:**
   - Create a fork of the main repository
   - Clone your fork locally

2. **Create a Feature Branch:**
   - Create a branch for your feature or fix
   - Use descriptive branch names (e.g., `feature/add-new-provider`)

3. **Implement Changes:**
   - Follow the code style and quality guidelines
   - Add appropriate tests
   - Update documentation as needed

4. **Submit a Pull Request:**
   - Create a pull request against the main branch
   - Provide a clear description of the changes
   - Reference any related issues

### Code Review Checklist

- Code follows the style guidelines
- All tests pass
- New functionality has tests
- Documentation is updated
- No security vulnerabilities introduced
- No unnecessary dependencies added
- Performance impact considered

### Development Best Practices

- Write clean, readable code
- Follow the Single Responsibility Principle
- Use meaningful variable and function names
- Keep functions and classes small and focused
- Comment complex logic, but prefer self-documenting code
- Handle errors gracefully
- Write tests before implementing features (TDD)

---

## License

[Specify your project license here]

---

## Acknowledgments

[Add any acknowledgments, credits, or inspirations]
