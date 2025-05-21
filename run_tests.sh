#!/bin/bash
# run_tests.sh

# Activate virtual environment
source venv/bin/activate

# Set test environment variables
export API_TOKEN=test_token
export OPENAI_API_KEY=test_key
export ENVIRONMENT=testing
export DEBUG=True
export RATE_LIMIT_ENABLED=False

# Run tests with coverage
pytest --cov=flaskllm --cov-report=term-missing

# Return to the root directory
cd ..
