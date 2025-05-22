# wsgi.py
import os
import sys
import pathlib

# Add the project directory to the system path using relative path resolution
project_path = str(pathlib.Path(__file__).parent.absolute())
if project_path not in sys.path:
    sys.path.append(project_path)

# Configure virtual environment if it exists
venv_path = os.path.join(project_path, "venv")
if os.path.exists(venv_path):
    os.environ["VIRTUAL_ENV"] = venv_path
    os.environ["PATH"] = os.path.join(venv_path, "bin:") + os.environ["PATH"]

# Set environment variables (better to use PythonAnywhere's environment variables UI)
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "False"
# Do NOT include sensitive values like API_TOKEN or API keys here

# Import the application
from app import create_app

application = create_app()  # for WSGI servers
