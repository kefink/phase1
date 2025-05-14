"""
Test script for the new application structure.
This script creates and runs a Flask application using the new structure.
"""
from new_structure import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Use a different port to avoid conflicts