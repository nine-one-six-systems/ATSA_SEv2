# Technology Stack

**Analysis Date:** 2026-02-04

## Languages

**Primary:**
- Python 3.12.6 - Backend application and business logic

## Runtime

**Environment:**
- Python 3.8+ (Python 3.12.6 deployed)

**Package Manager:**
- pip - Python package management
- Lockfile: requirements.txt (pinned versions)

## Frameworks

**Core:**
- Flask 3.0.0 - Web framework for HTTP routing and request handling
- Flask-SQLAlchemy 3.1.1 - SQLAlchemy integration with Flask for ORM

**Frontend:**
- Vanilla HTML/CSS/JavaScript - Client-side UI (no frontend framework)

**Database:**
- SQLAlchemy 2.0.35+ - Python ORM for database abstraction and model definition

## Key Dependencies

**Critical:**
- Flask-SQLAlchemy 3.1.1 - Database ORM integration
- pdfplumber 0.10.3 - PDF text extraction and parsing
- pytesseract 0.3.13+ - OCR engine wrapper for image text extraction
- Pillow 10.2.0+ - Image processing (required for pytesseract)

**Security:**
- cryptography 41.0.7 - Encryption for SSN storage in database
- werkzeug 3.0.1 - WSGI utility library and password hashing (Flask dependency)

**Environment:**
- python-dotenv 1.0.0 - Environment variable management for configuration

## Configuration

**Environment:**
- Configuration via `config.py` at application root
- Database URI: SQLite local file (`database.db`)
- Upload folder: `static/uploads/` (16MB max file size)
- Optional environment variables:
  - `SECRET_KEY` - Flask secret key (default: development-only key)
  - `SSN_ENCRYPTION_KEY` - Base64-encoded 32-byte key for SSN encryption
  - `TESSERACT_CMD` - Path to tesseract executable (if not in system PATH)

**Build:**
- `setup.sh` - Initialization script (creates venv, installs dependencies, validates Tesseract)
- `run.sh` - Application startup script

## Platform Requirements

**Development:**
- Python 3.8 or higher
- Tesseract OCR binary (system-level installation required)
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `apt-get install tesseract-ocr`
  - Windows: Manual installer from https://github.com/UB-Mannheim/tesseract/wiki

**Production:**
- Python 3.8+ runtime
- SQLite3 (or migration to PostgreSQL as documented in README)
- Tesseract OCR for document processing
- WSGI server (Gunicorn or equivalent, not included in dependencies)
- HTTPS/SSL termination (recommended)

---

*Stack analysis: 2026-02-04*
