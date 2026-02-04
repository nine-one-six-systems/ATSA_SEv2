# Coding Conventions

**Analysis Date:** 2026-02-04

## Naming Patterns

**Files:**
- Snake case with underscores: `tax_calculator.py`, `ocr_service.py`, `analysis_engine.py`
- Model files: `client.py`, `document.py`, `analysis.py`
- Route files: `clients.py`, `documents.py`, `calculator.py`
- Service files: `tax_calculator.py`, `tax_parser.py`, `analysis_engine.py`

**Classes:**
- PascalCase for all classes: `TaxCalculator`, `OCRService`, `AnalysisEngine`, `Client`, `Document`, `ExtractedData`
- Service classes typically end with "Service": `OCRService`, `IRSReferenceService`, `AnalysisEngine`
- Model classes are entity names: `Client`, `Document`, `AnalysisResult`, `TaxBracket`

**Functions and Methods:**
- Snake case: `extract_text()`, `calculate_federal_tax()`, `process_document()`, `get_numeric_value()`
- Private methods prefixed with underscore: `_extract_from_pdf()`, `_calculate_summary()`, `_get_encryption_key()`
- Static methods used extensively with `@staticmethod` decorator

**Variables:**
- Snake case: `filing_status`, `standard_deduction`, `taxable_income`, `client_id`, `file_path`
- Constants in UPPER_CASE: `DEPENDENT_EXEMPTION`, `SOCIAL_SECURITY_RATE`, `UPLOAD_FOLDER`, `ALLOWED_EXTENSIONS`
- Boolean variables prefixed with `is_` or `has_`: `is_ocr_available()`, `allowed_file()`, `force_refresh`

**Database/Model Attributes:**
- Snake case column names: `first_name`, `last_name`, `filing_status`, `tax_year`, `ocr_status`
- Timestamp fields: `created_at`, `updated_at`, `extracted_at`, `last_analyzed_at`
- Foreign key fields: `client_id`, `spouse_id`, with relationship defined via backref

## Code Style

**Formatting:**
- No explicit linter/formatter configured (ESLint/Prettier not found)
- Indentation: 4 spaces (Python standard)
- Line length: No strict limit observed, but most lines stay under 100 characters
- Blank lines: 2 between class definitions, 1 between method definitions within class

**Linting:**
- No linting configuration detected (.eslintrc, .flake8, pylintrc not present)
- Code follows PEP 8 conventions by convention

## Import Organization

**Order:**
1. Standard library imports: `import os`, `from datetime import datetime`, `from pathlib import Path`
2. Third-party framework imports: `from flask import Flask, Blueprint, request, jsonify`
3. Third-party library imports: `import pdfplumber`, `import pytesseract`, `from PIL import Image`
4. Local application imports: `from models import db, Client`, `from services.tax_calculator import TaxCalculator`
5. Blank line separates each group

**Examples:**
- `models/__init__.py` (line 1-12): SQLAlchemy first, then all model imports in order
- `routes/calculator.py` (line 1-3): Flask imports, then local imports
- `services/tax_strategies.py` (line 6-8): Standard library (Decimal, typing), then local imports

**Path Aliases:**
- Not detected in codebase
- Direct relative imports used: `from models import db, Client`
- Absolute imports from project root: `from services.tax_calculator import TaxCalculator`

## Error Handling

**Patterns:**

**Try-except with specific exception types:**
```python
# models/analysis.py, line 31-34
try:
    income_sources_list = json.loads(self.income_sources)
except (json.JSONDecodeError, TypeError):
    pass
```

**Try-except with generic Exception and re-raise:**
```python
# services/ocr_service.py, line 25-33
try:
    if file_type.lower() == 'pdf':
        return OCRService._extract_from_pdf(file_path)
    elif file_type.lower() in ['jpg', 'jpeg', 'png']:
        return OCRService._extract_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
except Exception as e:
    raise Exception(f"OCR extraction failed: {str(e)}")
```

**Try-except with Flask error responses:**
```python
# routes/calculator.py, line 58-152
try:
    data = request.get_json()
    # ... processing ...
    return jsonify({...}), 200
except Exception as e:
    return jsonify({
        'success': False,
        'error': str(e)
    }), 400
```

**Try-except with logging (Flask context):**
```python
# routes/documents.py, line 92-98
try:
    strategies, summary = AnalysisEngine.analyze_client(document.client_id)
    analysis_triggered = True
except Exception as analysis_ex:
    analysis_error = str(analysis_ex)
    current_app.logger.error(f'Analysis failed for client {document.client_id}: {analysis_error}')
```

**Bare except (discouraged but present):**
```python
# services/analysis_engine.py, line 275-281
try:
    if form_type in data_dict and field_name in data_dict[form_type]:
        value = data_dict[form_type][field_name]
        if value:
            return float(value)
except:
    pass
```

**Guidelines:**
- Catch specific exception types where possible
- Use generic `Exception` when wrapping/re-raising with context
- For silent failures (try-pass), use bare `except` only in helper methods
- Flask routes return JSON error responses with HTTP status codes
- Database operations use Flask-SQLAlchemy error handling (get_or_404)
- Validation errors return 400 status with error message in JSON

## Logging

**Framework:** `logging` module via Flask's `current_app.logger`

**Patterns:**
- Only one logging pattern found: `current_app.logger.error()` in `routes/documents.py:98`
- Called when background analysis fails: "Analysis failed for client {id}: {error}"
- No debug, info, or warning logs found
- No structured logging framework detected

**When to log:**
- Log errors in route handlers when async/background operations fail
- Include context (client_id, operation name) in error messages

## Comments

**When to Comment:**
- Docstrings on all public methods and classes
- Inline comments for complex logic or non-obvious calculations
- Comments explain "why" not "what" (code should be self-documenting)
- Section comments for major algorithm steps (e.g., "Social Security tax (capped at wage base)")

**JSDoc/Docstring Style:**
- Google-style docstrings with triple quotes
- Parameters documented with type hints and description
- Return type and value documented
- Examples present in services (see `tax_calculator.py:11-21`, `analysis_engine.py:38-48`)

**Pattern:**
```python
# From services/tax_calculator.py, line 11-21
@staticmethod
def convert_income_to_annual(amount, frequency):
    """
    Convert income from various frequencies to annual amount.

    Args:
        amount: Income amount
        frequency: 'annual', 'monthly', 'bi_monthly', 'bi_weekly', 'weekly'

    Returns:
        float: Annual income amount
    """
```

**Inline comment pattern:**
```python
# From models/client.py, line 41
# For development, use a default key (should be changed in production)

# From services/tax_calculator.py, line 194
# Social Security tax (capped at wage base)
```

## Function Design

**Size:**
- Small utility functions (2-10 lines): `allowed_file()`, `is_ocr_available()`
- Medium functions (30-50 lines): Most route handlers, helper methods
- Large functions (100-800 lines): Complex calculations like `calculate_federal_tax()`, `calculate_long_term_capital_gains_tax()`
- Very large methods indicate candidate for refactoring

**Parameters:**
- Most functions take 3-7 parameters
- S-Corp calculations use named parameters with defaults: `income_source='w2'`, `tax_year=2026`
- Keyword-only arguments not used; positional and optional parameters mixed
- Default values provide sensible fallbacks

**Return Values:**
- Single return value: primitives (float, str, int, bool)
- Complex returns: dictionaries with nested structure (e.g., tax calculation results)
- Model methods return `to_dict()` for serialization
- Helper methods return tuple for multi-value results (rare - mostly dictionaries)

**Example with multiple returns:**
```python
# From services/analysis_engine.py, line 38-48
@staticmethod
def analyze_client(client_id, force_refresh=False):
    """
    Analyze a client's tax situation and generate recommendations

    Args:
        client_id: ID of the client to analyze
        force_refresh: If True, force reanalysis even if data hasn't changed

    Returns:
        tuple: (list of AnalysisResult objects, summary dict)
    """
```

## Module Design

**Exports:**
- Barrel file pattern: `models/__init__.py` imports all models and re-exports
- `services/__init__.py` imports and exposes main services
- `routes/api.py` imports all route blueprints and registers them

**Example barrel file:**
```python
# From models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.client import Client
from models.document import Document
from models.extracted_data import ExtractedData
from models.analysis import AnalysisResult, AnalysisSummary
from models.irs_reference import IRSReference
from models.tax_tables import TaxBracket, StandardDeduction

__all__ = ['db', 'Client', 'Document', 'ExtractedData', 'AnalysisResult', 'AnalysisSummary', 'IRSReference', 'TaxBracket', 'StandardDeduction']
```

**Circular Import Handling:**
- Models import `db` from `models/__init__.py`
- Services import models directly: `from models import db, Client, ExtractedData`
- Routes import both models and services: `from models import db, Client` and `from services.tax_calculator import TaxCalculator`
- No circular dependency issues detected

**Module Organization:**
- Models layer: `models/` - SQLAlchemy ORM definitions
- Service layer: `services/` - Business logic (calculations, parsing, analysis)
- Route layer: `routes/` - Flask blueprints and HTTP handlers
- Config layer: `config.py` - Configuration constants
- Database: `database/init_db.py` - Database initialization

---

*Convention analysis: 2026-02-04*
