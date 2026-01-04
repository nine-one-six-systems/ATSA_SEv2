# Advanced Tax Strategy Assessment (ATSA)

A web application that analyzes a person's taxable income to determine the most advanced strategy possible to limit taxable exposure. It also provides functional strategies to reduce taxable income and maximize income.

## Features

- **Document Upload & OCR**: Upload PDF or JPG/PNG files with prior year tax returns for OCR and input into the database
- **Tax Analysis**: Analyzes a client's income and tax information to provide alternative options for decreasing tax liability
- **IRS Code References**: Each strategy includes reference data to the actual IRS code that supports the option
- **Client Profiles**: Create and manage client profiles with support for multiple people (married couples) with different income sources

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Backend**: Python/Flask
- **Database**: SQLite
- **OCR**: PDFplumber (PDFs) + pytesseract (Images)

## Installation

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR (for image OCR)

#### Installing Tesseract OCR

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

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ATSA
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (optional):
```bash
export SECRET_KEY="your-secret-key-here"
export SSN_ENCRYPTION_KEY="your-encryption-key-here"  # Base64 encoded 32-byte key
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### 1. Create a Client Profile

- Navigate to the "Clients" page
- Click "Add New Client"
- Fill in the client information (name, filing status, contact info, etc.)
- Save the client

### 2. Upload Tax Documents

- Navigate to the "Upload Documents" page
- Select a client from the dropdown
- Drag and drop or browse for tax documents (PDF, JPG, PNG)
- Click "Upload Files"
- After upload, click "Process" to run OCR and extract tax data

### 3. Run Tax Analysis

- Navigate to the "Analysis" page (or click "View Analysis" from a client card)
- Select a client
- Click "Run Analysis"
- Review the generated tax strategies with IRS code references

## Project Structure

```
ATSA/
├── app.py                 # Flask application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── database/
│   └── init_db.py         # Database initialization script
├── models/                # SQLAlchemy models
├── services/              # Business logic services
├── routes/                # API route handlers
├── static/                # Static files (CSS, JS, uploads)
└── templates/             # HTML templates
```

## API Endpoints

### Clients
- `GET /api/clients` - List all clients
- `POST /api/clients` - Create new client
- `GET /api/clients/<id>` - Get client details
- `PUT /api/clients/<id>` - Update client
- `DELETE /api/clients/<id>` - Delete client
- `POST /api/clients/<id>/link-spouse` - Link two client profiles

### Documents
- `POST /api/documents/upload` - Upload tax document
- `GET /api/documents/<id>` - Get document details
- `POST /api/documents/<id>/process` - Trigger OCR processing
- `GET /api/documents/client/<client_id>` - Get all documents for client

### Analysis
- `POST /api/analysis/analyze/<client_id>` - Run analysis for client
- `GET /api/analysis/<id>` - Get analysis results
- `GET /api/analysis/client/<client_id>` - Get all analyses for client

## Security Considerations

- SSNs are encrypted before storage in the database
- File uploads are validated for type and size (max 16MB)
- User inputs are sanitized
- In production, change the default SECRET_KEY and use proper SSN_ENCRYPTION_KEY

## Development

The application runs in debug mode by default. For production deployment:

1. Set `debug=False` in `app.py`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure proper environment variables
4. Set up HTTPS/SSL
5. Use a production database (PostgreSQL recommended)

## License

[Add your license here]
