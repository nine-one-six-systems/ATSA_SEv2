# Quick Start Guide

## ✅ Setup Complete!

All Python dependencies have been installed successfully in the virtual environment.

## Remaining Steps

### 1. Install Tesseract OCR (Required for Image OCR)

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

**Note:** PDF processing will work without Tesseract, but image (JPG/PNG) OCR requires Tesseract.

### 2. Run the Application

```bash
cd /Users/stephenhollifield/ATSA/ATSA
source venv/bin/activate
python app.py
```

Or use the run script:
```bash
./run.sh
```

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## What's Ready

✅ Python virtual environment created  
✅ All Python dependencies installed:
   - Flask 3.0.0
   - Flask-SQLAlchemy 3.1.1
   - SQLAlchemy 2.0.23
   - pdfplumber 0.10.3
   - pytesseract 0.3.10
   - Pillow 12.1.0
   - cryptography 41.0.7
   - And all dependencies

✅ Database will be auto-created on first run  
✅ Upload directory ready  
✅ All application files in place  

## First Time Usage

1. **Create a Client:**
   - Go to "Clients" page
   - Click "Add New Client"
   - Fill in client information
   - Save

2. **Upload Tax Documents:**
   - Go to "Upload Documents" page
   - Select a client
   - Upload PDF or image files
   - Click "Process" to extract data

3. **Run Analysis:**
   - Go to "Analysis" page (or click "View Analysis" from client card)
   - Select a client
   - Click "Run Analysis"
   - Review tax strategies with IRS code references

## Troubleshooting

### If Tesseract is not found:
- Make sure it's installed: `brew install tesseract` (macOS)
- Check if it's in PATH: `which tesseract`
- The app will still work for PDF files without Tesseract

### If you get import errors:
- Make sure virtual environment is activated: `source venv/bin/activate`
- Verify packages: `pip list`

### Database issues:
- Database is created automatically on first run
- Located at: `database.db` in the project root
- To reset: delete `database.db` and restart the app

## Next Steps

The application is ready to use! Just install Tesseract (if you need image OCR) and start the server.

For detailed setup instructions, see `SETUP_INSTRUCTIONS.md`

