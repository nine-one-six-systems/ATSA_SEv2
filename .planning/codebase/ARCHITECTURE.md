# Architecture

**Analysis Date:** 2026-02-04

## Pattern Overview

**Overall:** MVC (Model-View-Controller) layered architecture with Flask microservices pattern

**Key Characteristics:**
- Clear separation between data models, business logic services, and HTTP endpoints
- SQLAlchemy ORM for database abstraction
- Service layer pattern for domain-specific operations (tax parsing, analysis, OCR)
- Blueprint-based modular routing for scalability
- Synchronous request-response model with optional analysis triggering

## Layers

**Database Layer:**
- Purpose: Persist client data, documents, extracted tax data, analysis results, and tax reference tables
- Location: `database/init_db.py`, SQLite database at `database.db`
- Contains: Schema initialization, IRS reference seeding, tax table population
- Depends on: SQLAlchemy ORM
- Used by: All models and services

**Model Layer (ORM):**
- Purpose: Define database entities and relationships
- Location: `models/` directory
- Contains: `Client`, `Document`, `ExtractedData`, `AnalysisResult`, `AnalysisSummary`, `IRSReference`, `TaxBracket`, `StandardDeduction`
- Depends on: Flask-SQLAlchemy, cryptography (for SSN encryption)
- Used by: Services and route handlers

**Service Layer (Domain Logic):**
- Purpose: Encapsulate tax processing, analysis, and calculation logic
- Location: `services/` directory
- Contains:
  - `ocr_service.py`: Text extraction from PDFs and images
  - `tax_parser.py`: Form detection and field extraction from OCR text
  - `analysis_engine.py`: Client tax analysis, strategy generation, summary calculation
  - `tax_calculator.py`: Tax computation based on brackets and income
  - `irs_reference.py`: IRS code lookup and reference retrieval
  - `tax_strategies.py`: Comprehensive tax strategy analysis
  - `state_tax_parser.py`: State-specific tax parsing
  - `tax_data_service.py`: Population and management of tax reference data
- Depends on: Models, pdfplumber, pytesseract, Pillow
- Used by: Route handlers

**Route Layer (HTTP Endpoints):**
- Purpose: Handle HTTP requests and orchestrate service calls
- Location: `routes/` directory, registered via Blueprint pattern in `routes/api.py`
- Contains:
  - `clients.py`: Client CRUD operations, spouse linking
  - `documents.py`: Document upload, OCR processing, document retrieval
  - `analysis.py`: Tax analysis triggering and result retrieval
  - `calculator.py`: Tax bracket and deduction lookups
- Depends on: Services, models, Flask
- Used by: Frontend JavaScript calls

**Presentation Layer:**
- Purpose: Render HTML templates and serve static assets
- Location: `templates/` (HTML), `static/` (CSS, JS)
- Contains: `index.html`, `clients.html`, `upload.html`, `analysis.html`, `calculator.html`
- Entry point: `app.py:create_app()` routes `GET /`, `/clients.html`, `/upload.html`, etc.

## Data Flow

**Document Upload and Processing Pipeline:**

1. User uploads tax document via `POST /api/documents/upload`
   - File validation (PDF, JPG, PNG only)
   - File secured and stored to `static/uploads/`
   - Document record created in database with `ocr_status='pending'`

2. Client triggers processing via `POST /api/documents/{id}/process`
   - `OCRService.extract_text()` → extracts text from file using pdfplumber (PDF) or pytesseract (images)
   - Document status updated to `ocr_status='processing'`

3. `TaxParser.parse_text()` analyzes extracted text
   - Detects tax forms using regex patterns (1040, W-2, 1099-*, Schedules, etc.)
   - Extracts specific fields from each detected form type
   - Stores extracted data records in `ExtractedData` table

4. Automatic `AnalysisEngine.analyze_client()` trigger
   - Calculates data version hash from ExtractedData timestamps
   - Checks for cached results (returns if data unchanged)
   - Organizes extracted data by form type
   - Generates tax summary: total income, AGI, taxable income, tax calculations
   - Calls `TaxStrategiesService.analyze_all_strategies()` for recommendations
   - Stores strategies in `AnalysisResult` table
   - Creates/updates `AnalysisSummary` with hash and timestamp

5. Document status updated to `ocr_status='completed'` or `'failed'`

**Analysis Retrieval:**

1. User requests analysis via `GET /api/analysis/client/{client_id}`
   - Retrieves stored `AnalysisResult` records (ordered by priority)
   - Retrieves `AnalysisSummary` for tax calculations
   - Returns strategies with recommendations and potential savings

**Tax Calculation:**

1. Frontend requests tax brackets via `GET /api/calculator/tax-brackets?tax_type=federal&filing_status=single&tax_year=2026`
   - Queries `TaxBracket` table
   - Returns income ranges and corresponding rates

2. Tax calculator uses brackets to compute liability based on income

## State Management

**Analysis Caching:**
- `AnalysisSummary.data_version_hash`: SHA-256 of sorted ExtractedData timestamps detects when client data changes
- If hash unchanged, cached strategies are returned without reanalysis (unless `force_refresh=True`)
- Improves performance when viewing analysis multiple times

**Client Relationships:**
- Clients can be linked as spouses via `Client.spouse_id` field
- Bidirectional linking: both clients point to each other
- Enables joint tax filing scenarios

## Key Abstractions

**OCRService:**
- Purpose: Abstract OCR implementation details (pdfplumber for PDFs, pytesseract for images)
- Examples: `ocr_service.py`
- Pattern: Static methods with form-type dispatch

**TaxParser:**
- Purpose: Separate form detection logic from field extraction
- Examples: `tax_parser.py`
- Pattern: Form-specific extraction methods (`_extract_1040_data()`, `_extract_w2_data()`, etc.)
- Detects forms via regex, extracts field patterns, stores to database

**AnalysisEngine:**
- Purpose: Orchestrate tax analysis workflow and caching
- Examples: `analysis_engine.py`
- Pattern: Calculation helpers (`_get_numeric_value()`, `_estimate_marginal_rate()`), strategy analyzers (`_analyze_retirement_strategies()`)

**TaxStrategiesService:**
- Purpose: Generate context-aware tax recommendations
- Examples: `tax_strategies.py`
- Pattern: Comprehensive analysis of all strategy categories (retirement, business, deductions, investments, education)

## Entry Points

**Application Boot:**
- Location: `app.py:create_app()`
- Triggers: Script execution or WSGI server startup
- Responsibilities: Flask app configuration, database initialization, blueprint registration, route setup

**Frontend Routes:**
- Location: `app.py` lines 24-42
- Triggers: Browser navigation to `/`, `/clients.html`, `/upload.html`, `/analysis.html`, `/calculator.html`
- Responsibilities: Render HTML templates

**API Health Check:**
- Location: `routes/api.py:health_check()`
- Triggers: `GET /api/health`
- Responsibilities: Return service status

## Error Handling

**Strategy:** Try-catch at service layer with graceful fallbacks; error propagation to route layer

**Patterns:**
- OCR failures: Document marked as `ocr_status='failed'`, error returned to client
- Missing data: Analysis engine returns empty summary when no extracted data exists
- Analysis trigger failure: Caught and logged, document processing continues (non-blocking)
- Encryption/decryption: Falls back to SHA-256 hashing if Fernet encryption fails

## Cross-Cutting Concerns

**Logging:** Flask default logger via `current_app.logger.error()` for exceptions

**Validation:**
- File upload validation: Extension checks, size limits (16MB max in `app.py`)
- Client creation: Required fields validated in route handler (`first_name`, `last_name`, `filing_status`)

**Authentication:** Not implemented; no auth layer (assumed single-user or trusted environment)

**Data Security:**
- SSN encryption: Client model uses Fernet encryption for sensitive data
- Falls back to SHA-256 if encryption unavailable
- Secret key from environment variable `SECRET_KEY` or default development key

**Relationships and Cascading:**
- Document deletions cascade to `ExtractedData` (via `cascade='all, delete-orphan'`)
- Client deletions cascade to documents, extracted data, and analyses

---

*Architecture analysis: 2026-02-04*
