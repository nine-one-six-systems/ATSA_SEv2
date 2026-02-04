# Codebase Structure

**Analysis Date:** 2026-02-04

## Directory Layout

```
ATSA_SEv2/
├── app.py                  # Flask application factory and main routes
├── config.py               # Configuration (database URI, upload paths, OCR settings)
├── requirements.txt        # Python dependencies
├── database/
│   └── init_db.py          # Database schema initialization, IRS reference seeding, tax table population
├── models/
│   ├── __init__.py         # SQLAlchemy instance and model exports
│   ├── client.py           # Client model with SSN encryption
│   ├── document.py         # Document model (uploaded tax forms)
│   ├── extracted_data.py   # ExtractedData model (parsed form fields)
│   ├── analysis.py         # AnalysisResult and AnalysisSummary models
│   ├── irs_reference.py    # IRSReference model (tax codes and URLs)
│   └── tax_tables.py       # TaxBracket and StandardDeduction models
├── routes/
│   ├── __init__.py         # Empty init
│   ├── api.py              # Blueprint registration and health check
│   ├── clients.py          # Client CRUD and spouse linking endpoints
│   ├── documents.py        # Upload, retrieve, process document endpoints
│   ├── analysis.py         # Tax analysis and strategy retrieval endpoints
│   └── calculator.py       # Tax bracket and deduction lookup endpoints
├── services/
│   ├── __init__.py         # Empty init
│   ├── ocr_service.py      # OCR extraction (pdfplumber and pytesseract)
│   ├── tax_parser.py       # Form detection and field extraction
│   ├── analysis_engine.py  # Client analysis orchestration and caching
│   ├── irs_reference.py    # IRS reference lookup service
│   ├── tax_calculator.py   # Tax computation and bracket application
│   ├── tax_strategies.py   # Comprehensive tax strategy analysis
│   ├── state_tax_parser.py # State-specific tax parsing
│   └── tax_data_service.py # Tax table population and management
├── static/
│   ├── css/                # Stylesheet files
│   ├── js/                 # JavaScript files
│   └── uploads/            # Generated at runtime; uploaded tax documents
├── templates/
│   ├── index.html          # Main dashboard
│   ├── clients.html        # Client management interface
│   ├── upload.html         # Document upload interface
│   ├── analysis.html       # Analysis results and strategies
│   └── calculator.html     # Tax calculator interface
└── .planning/
    └── codebase/           # Analysis documents (this file)
```

## Directory Purposes

**ATSA_SEv2/ (root):**
- Purpose: Project root containing application entry point and configuration
- Contains: Flask app factory, configuration, requirements, documentation

**database/:**
- Purpose: Database initialization and seed data management
- Contains: Schema creation, IRS reference seeding, tax table population logic
- Key files: `init_db.py` (entry point for database setup)

**models/:**
- Purpose: SQLAlchemy ORM models representing database entities
- Contains: Client, Document, ExtractedData, AnalysisResult, AnalysisSummary, IRSReference, TaxBracket, StandardDeduction
- Key files: `__init__.py` exports all models and SQLAlchemy instance
- Database Tables: clients, documents, extracted_data, analysis_results, analysis_summaries, irs_references, tax_brackets, standard_deductions

**routes/:**
- Purpose: Flask Blueprint route handlers for HTTP endpoints
- Contains: CRUD endpoints, file processing, analysis triggers, lookups
- Key files: `api.py` (Blueprint aggregation), individual modules for feature domains
- Pattern: Each route module defines a Blueprint, registered in `api.py`, which is registered in `app.py`

**services/:**
- Purpose: Business logic and domain-specific operations
- Contains: OCR, tax parsing, analysis, calculations, reference lookups
- Key files:
  - `ocr_service.py`: Handles PDF and image text extraction
  - `tax_parser.py`: Detects and extracts tax form data
  - `analysis_engine.py`: Client analysis and strategy generation with caching
  - `tax_calculator.py`: Tax computation from brackets
  - `tax_strategies.py`: Recommendation generation
- Pattern: Mostly static methods; no state

**static/:**
- Purpose: Client-side assets and uploaded documents
- Contains:
  - `css/`: Stylesheets for template rendering
  - `js/`: JavaScript for frontend interactions
  - `uploads/`: User-uploaded tax documents (generated at runtime)
- Key path: `static/uploads/` used by document upload feature

**templates/:**
- Purpose: Jinja2 HTML templates for frontend
- Contains: Five main pages for dashboard, client management, uploads, analysis, and calculator
- Accessed via: Routes in `app.py` (`@app.route('/')` returns `index.html`, etc.)

## Key File Locations

**Entry Points:**
- `app.py`: Application factory (`create_app()`) and main frontend routes
- `database/init_db.py`: Database initialization on startup
- Run via: `python app.py` (debug mode) or WSGI server

**Configuration:**
- `config.py`: Database path, upload folder, max file size, OCR settings, encryption keys
- Environment variables: `SQLALCHEMY_DATABASE_URI`, `UPLOAD_FOLDER`, `SECRET_KEY`, `TESSERACT_CMD`, `SSN_ENCRYPTION_KEY`

**Core Logic:**
- `services/ocr_service.py`: PDF/image text extraction (static methods)
- `services/tax_parser.py`: Form detection and field extraction (static methods)
- `services/analysis_engine.py`: Analysis orchestration, caching logic, summary calculations
- `models/client.py`: Client model with SSN encryption/decryption methods

**Testing:**
- No test files present in codebase
- Test location if added: `tests/` (recommended parallel to `models/`, `services/`, `routes/`)

## Naming Conventions

**Files:**
- `snake_case.py` for Python modules
- Plural names for directories containing multiple related files: `routes/`, `services/`, `models/`
- Single concept per file: `ocr_service.py` has only OCRService class

**Directories:**
- Feature-based grouping: `routes/`, `services/`, `models/` organize by layer not feature
- Alternative: Could add `tax_analysis/`, `client_mgmt/` if domains grow
- Static content: `static/css/`, `static/js/` follow Flask conventions

**Database Models:**
- PascalCase class names: `Client`, `Document`, `ExtractedData`, `AnalysisResult`
- Plural table names: `__tablename__ = 'clients'`, `__tablename__ = 'documents'`
- Foreign keys: `client_id` references `clients.id` table

**Routes/Endpoints:**
- Nested resources: `/api/clients`, `/api/clients/{id}`, `/api/documents/{id}/process`
- Resource actions use POST with verbs: `POST /api/documents/{id}/process`, `POST /api/clients/{id}/link-spouse`
- HTTP methods: GET for retrieval, POST for creation/action, PUT for updates, DELETE for removal

**Service Classes:**
- Service naming: `OCRService`, `TaxParser`, `AnalysisEngine` (domain + Service/Engine suffix)
- Static method organization: Methods grouped logically with leading underscore for private helpers
- Example: `OCRService._extract_from_pdf()`, `TaxParser._detect_forms()`, `AnalysisEngine._get_numeric_value()`

## Where to Add New Code

**New Feature (Tax Strategy):**
- Primary code: `services/tax_strategies.py` (add new analysis method)
- Route endpoint: `routes/analysis.py` (add new endpoint if new retrieval pattern needed)
- Model: Use existing `AnalysisResult` and `AnalysisSummary` models
- Entry point: `AnalysisEngine.analyze_client()` calls `TaxStrategiesService.analyze_all_strategies()`

**New Component/Module (e.g., StateAnalysis):**
- Implementation: `services/state_analysis.py` (new service file)
- Integration: Call from `services/analysis_engine.py` at appropriate point in analysis flow
- Route exposure: Add endpoint to `routes/analysis.py` if API access needed
- Models: Add to `models/` if new database entities needed

**Utilities/Helpers:**
- Shared helpers: `services/` (even if small) keeps domain logic colocated
- Form extraction patterns: Add to `TaxParser.FORM_PATTERNS` dict for new forms
- Tax calculations: Add static methods to `AnalysisEngine` class

**New Tax Form Support:**
- Form patterns: Add regex pattern to `TaxParser.FORM_PATTERNS` dict
- Field extraction: Add `TaxParser._extract_{form_type}_data()` method
- Strategy analysis: Add relevant conditions to `TaxStrategiesService` methods
- Database: Existing `ExtractedData` table stores all form types, no schema change needed

**Frontend Pages:**
- New template: `templates/{feature}.html`
- Route: Add to `app.py` as new `@app.route()` decorated function
- Style: Add styles to `static/css/` or inline in template
- Interaction: Add JavaScript to `static/js/` for form handling

## Special Directories

**static/uploads/:**
- Purpose: Runtime-generated directory for uploaded tax documents
- Generated: Yes, created by `os.makedirs(UPLOAD_FOLDER, exist_ok=True)` in `app.py`
- Committed: No, directory is in `.gitignore`
- File naming: `{client_id}_{timestamp}_{original_filename}` for uniqueness

**database.db:**
- Purpose: SQLite database file (created at runtime)
- Generated: Yes, created by SQLAlchemy on `db.create_all()`
- Committed: No, database files excluded from version control
- Location: Root directory as defined in `config.py`

**.planning/codebase/:**
- Purpose: Architecture and analysis documentation
- Generated: Yes, created by analysis tools
- Committed: Yes, version control maintained for reference

---

*Structure analysis: 2026-02-04*
