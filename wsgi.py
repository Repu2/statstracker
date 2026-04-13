"""WSGI entry point for production (gunicorn, PythonAnywhere, etc.)."""
import os
import sys

# Add project directory to path (required for PythonAnywhere)
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Ensure DB exists before first request
from db import init_db

init_db()

from app import app

# PythonAnywhere expects "application"
application = app
