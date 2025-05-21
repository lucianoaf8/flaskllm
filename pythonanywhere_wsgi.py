# pythonanywhere_wsgi.py
import sys
import os

# Add the project directory to the system path
project_path = "/home/yourusername/flaskllm"
if project_path not in sys.path:
    sys.path.append(project_path)

# Configure virtual environment
os.environ["VIRTUAL_ENV"] = "/home/yourusername/flaskllm/venv"
os.environ["PATH"] = "/home/yourusername/flaskllm/venv/bin:" + os.environ["PATH"]

# Import the application
