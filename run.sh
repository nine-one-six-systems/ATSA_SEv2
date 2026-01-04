#!/bin/bash
# Simple startup script for ATSA

echo "Starting ATSA Application..."
echo "Make sure you have activated your virtual environment and installed dependencies:"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo ""
echo "Starting Flask server on http://localhost:5555"
python app.py

