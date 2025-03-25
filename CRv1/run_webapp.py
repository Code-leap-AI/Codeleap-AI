#!/usr/bin/env python3
"""
Run Web Application
-----------------
Helper script to set up and run the course confidence web application.
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import flask
        import pandas
        import numpy
        import requests
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages using
