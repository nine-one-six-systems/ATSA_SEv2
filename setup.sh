#!/bin/bash
# Setup script for ATSA Application

set -e

echo "=========================================="
echo "ATSA Application Setup"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version
echo ""

# Create virtual environment
echo "2. Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "4. Upgrading pip..."
pip install --upgrade pip
echo "   ✓ pip upgraded"
echo ""

# Install Python dependencies
echo "5. Installing Python dependencies..."
pip install -r requirements.txt
echo "   ✓ Dependencies installed"
echo ""

# Check for Tesseract
echo "6. Checking Tesseract OCR installation..."
if command -v tesseract &> /dev/null; then
    echo "   ✓ Tesseract is installed: $(tesseract --version | head -n 1)"
else
    echo "   ⚠ Tesseract OCR not found!"
    echo ""
    echo "   Please install Tesseract OCR:"
    echo "   - macOS: brew install tesseract"
    echo "   - Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
fi
echo ""

# Create uploads directory if it doesn't exist
echo "7. Setting up directories..."
mkdir -p static/uploads
echo "   ✓ Directories ready"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the app: python app.py"
echo "  3. Open browser: http://localhost:5000"
echo ""
echo "Or use the run script: ./run.sh"
echo ""

