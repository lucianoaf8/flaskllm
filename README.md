# FlaskLLM API

A secure, scalable, and maintainable Python Flask-based API for processing prompts using Large Language Models (LLMs). This API provides a robust middleware layer between client applications (like Excel with Office Scripts) and LLM providers (like OpenAI, Anthropic, etc.).

## Features

- **Multi-Provider Support**: Integrate with OpenAI, Anthropic Claude, and more
- **Secure API Authentication**: Token-based authentication for all endpoints
- **Input Validation**: Robust request validation using Pydantic schemas
- **Rate Limiting**: Prevent API abuse with configurable rate limits
- **Comprehensive Error Handling**: Clear, consistent error responses
- **Extensive Testing**: Unit and integration tests for all components
- **Easy Deployment**: Deployment guide for PythonAnywhere

## Use Cases

- Process email contents via Office Scripts and Excel
- Generate summaries of meeting transcripts
- Extract keywords or entities from documents
- Translate content to different languages
- Perform sentiment analysis on text
- Extract named entities from content

## Quick Start

### Prerequisites

- Python 3.10+
- API key for at least one LLM provider (OpenAI, Anthropic)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lucianoaf8/flaskllm.git
   cd flaskllm
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file:
   ```bash
   cp .env.example .env
   # Edit .env with your LLM API keys and configuration
   ```

5. Run the development server:
   ```bash
   python app.py
   ```

The server will be available at http://localhost:5000.

## API Reference

### Health Check

```
GET /api/v1/health
```

Returns the health status of the API.

### Process Prompt

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

**Response:**
```json
{
  "summary": "The company plans to reduce hiring to cut costs.",
  "processing_time": 1.25
}
```

## Authentication

All API requests require authentication using an API token. The token should be provided in the `X-API-Token` header.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development, testing, production) | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `API_TOKEN` | Authentication token for API access | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `LLM_PROVIDER` | LLM provider to use (openai, anthropic) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | Required if using OpenAI |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required if using Anthropic |
| `ANTHROPIC_MODEL` | Anthropic model to use | `claude-2` |

## Development

### Running Tests

Use the provided script to run tests:

```bash
./run_tests.sh
```

This will execute both unit and integration tests with coverage reporting.

## Documentation

For complete documentation, see the `/docs` directory:

- [Project Documentation](docs/project-documentation.md)
- [Flask LLM Guidelines](docs/flask-llm-guidelines.md)
- [Task List](docs/task-list-v3.md)
- [PythonAnywhere Deployment Guide](docs/deploy_to_pythonanywhere.md)

## License

[Your License Here]

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
