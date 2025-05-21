import sys
import os

# Add your project directory to the path
path = "/home/yourusername/flaskllm"
if path not in sys.path:
    sys.path.append(path)

# Set virtual environment path
os.environ["VIRTUAL_ENV"] = "/home/yourusername/flaskllm/venv"
os.environ["PATH"] = "/home/yourusername/flaskllm/venv/bin:" + os.environ["PATH"]

# Set environment variables (better to use PythonAnywhere's environment variables UI)
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "False"
# Do NOT include sensitive values like API_TOKEN or API keys here

# Import the application
