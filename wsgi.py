# wsgi.py
import os
import sys

# Add the project directory to the system path
project_home = os.path.expanduser("~")
project_path = os.path.join(project_home, "Projects/flaskllm")
if project_path not in sys.path:
    sys.path.append(project_path)

# Configure virtual environment
os.environ["VIRTUAL_ENV"] = os.path.join(project_path, "venv")
os.environ["PATH"] = os.path.join(project_path, "venv/bin:") + os.environ["PATH"]

# Set environment variables (better to use PythonAnywhere's environment variables UI)
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "False"
# Do NOT include sensitive values like API_TOKEN or API keys here

# Import the application
from app import create_app

application = create_app()  # for WSGI servers
