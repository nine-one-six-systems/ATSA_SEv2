# Setup Instructions for ATSA

Due to system permission restrictions, please run these commands manually in your terminal.

## Step 1: Create and Activate Virtual Environment

```bash
cd /Users/stephenhollifield/ATSA/ATSA
python3 -m venv venv
source venv/bin/activate
```

## Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Step 4: Verify Installation

```bash
# Check Python packages
python3 -c "import flask; print('Flask installed')"

# Check Tesseract
tesseract --version
```

## Step 5: Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
python app.py
```

Or use the provided script:
```bash
./setup.sh  # Run setup (first time only)
./run.sh     # Run the application
```

## Step 6: Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## Troubleshooting

### If you get permission errors:
- Make sure you're not using sudo for pip installs in the venv
- Check that the venv directory has proper permissions

### If Tesseract is not found:
- Make sure Tesseract is installed and in your PATH
- On macOS, you may need to add: `export PATH="/opt/homebrew/bin:$PATH"` to your ~/.zshrc

### If imports fail:
- Make sure the virtual environment is activated
- Verify all packages installed: `pip list`

### Database issues:
- The database will be created automatically on first run
- If you need to reset: delete `database.db` and restart the app

