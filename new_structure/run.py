#!/usr/bin/env python3
"""
Run script for the Hillview School Management System.
This script creates and runs the Flask application.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_structure import create_app

if __name__ == '__main__':
    # Create the Flask application
    app = create_app('development')
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
