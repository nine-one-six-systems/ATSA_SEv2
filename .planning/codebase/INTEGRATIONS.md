# External Integrations

**Analysis Date:** 2026-02-04

## APIs & External Services

**Tax Reference Data:**
- IRS.gov URLs - Reference links embedded in tax strategies
  - No SDK integration; static URLs stored in database
  - Used in `database/init_db.py` for seeding IRS references
  - Examples: IRC Sections 179, 401(k), HSA, charitable deductions, etc.
  - Client: Direct URL references in `models/irs_reference.py`

## Data Storage

**Databases:**
- SQLite (local file-based)
  - Location: `database.db` at project root (via `config.py: SQLALCHEMY_DATABASE_URI`)
  - Client: Flask-SQLAlchemy ORM
  - Tables: clients, documents, extracted_data, analysis_results, analysis_summaries, irs_references, tax_brackets, standard_deductions

**File Storage:**
- Local filesystem only
  - Upload directory: `static/uploads/`
  - Supported formats: PDF, JPG, JPEG, PNG (configured in `config.py: ALLOWED_EXTENSIONS`)
  - Max file size: 16MB (enforced in Flask config and `config.py`)

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- Custom/None - No authentication system implemented
- No user login, session management, or role-based access control
- Application assumes single operator context

**Data Security:**
- SSN Encryption: Active
  - Implementation: Cryptography library (Fernet cipher) in `models/client.py`
  - Storage: Encrypted in database
  - Key management: Optional `SSN_ENCRYPTION_KEY` environment variable (defaults to development key)

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Console-based logging only (Flask debug mode)
- No persistent log storage or aggregation

## CI/CD & Deployment

**Hosting:**
- None configured (local development only)
- README mentions migration path to production with Gunicorn WSGI server

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars (optional but recommended):**
- `SECRET_KEY` - Flask session/security key (default: 'dev-secret-key-change-in-production')
- `SSN_ENCRYPTION_KEY` - Base64-encoded 32-byte key for client SSN encryption
- `TESSERACT_CMD` - Path to tesseract executable (if not in system PATH)

**Secrets location:**
- Environment variables only (no .env file template provided)
- Credentials not committed to repository

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Document Processing Pipeline

**PDF Processing:**
- Tool: pdfplumber 0.10.3
- Location: `services/ocr_service.py`
- Method: Text extraction via `pdfplumber.open()` and `page.extract_text()`
- No external PDF API calls

**Image OCR:**
- Tool: pytesseract 0.3.13+ (wrapper around Tesseract)
- Location: `services/ocr_service.py`
- Method: `pytesseract.image_to_string()` on PIL Image objects
- Requires: System-level Tesseract binary installation
- Supported formats: JPG, JPEG, PNG

## Tax Data Sources

**Federal Tax Brackets:**
- Hardcoded data in `services/tax_data_service.py`
- Years supported: 2026 (primary), 2024 (fallback)
- Includes all filing statuses: single, married_joint, married_separate, head_of_household, qualifying_surviving_spouse
- Not fetched from external API

**State Tax Data:**
- Custom markdown reference parser in `services/state_tax_parser.py`
- Source: Local markdown files (not detailed in inspection)
- Includes state-specific tax brackets and deductions

**IRS Code References:**
- Seeded into database on first initialization
- Source: Hardcoded in `database/init_db.py`
- Includes 14+ IRC sections with descriptions and applicable forms
- References point to IRS.gov documentation URLs

---

*Integration audit: 2026-02-04*
