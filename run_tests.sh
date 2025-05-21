#!/bin/bash
# run_tests.sh

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt
else
    # Activate virtual environment
    source venv/bin/activate
    
    # Ensure all dependencies are up-to-date
    echo "Updating dependencies..."
    pip install -r requirements-dev.txt
fi

# Set test environment variables
export API_TOKEN=test_token
export OPENAI_API_KEY=test_key
export ANTHROPIC_API_KEY=test_key
export ENVIRONMENT=testing
export DEBUG=True
export RATE_LIMIT_ENABLED=False
export LLM_PROVIDER=openai

# Run tests with coverage
echo "Running tests..."
python -m pytest --cov=. --cov-report=term-missing

# Get the exit code from pytest
TEST_EXIT_CODE=$?

# Stay in the current directory (removing the incorrect cd command)

# Return the pytest exit code
exit $TEST_EXIT_CODE
