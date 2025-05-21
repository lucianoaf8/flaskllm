# wsgi.py
import sys
import os

# Add the project directory to the system path
project_path = "/home/yourusername/flaskllm"
if project_path not in sys.path:
    sys.path.append(project_path)

# Configure virtual environment
os.environ["VIRTUAL_ENV"] = "/home/yourusername/flaskllm/venv"
os.environ["PATH"] = "/home/yourusername/flaskllm/venv/bin:" + os.environ["PATH"]

# Set environment variables (better to use PythonAnywhere's environment variables UI)
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "False"
# Do NOT include sensitive values like API_TOKEN or API keys here

# Import the application
from app import create_app
application = create_app()  # for WSGI servers
