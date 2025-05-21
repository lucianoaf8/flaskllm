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
fi

# Set test environment variables
export API_TOKEN=test_token
export OPENAI_API_KEY=test_key
export ENVIRONMENT=testing
export DEBUG=True
export RATE_LIMIT_ENABLED=False

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Return to the root directory
cd ..
