# Codebase Concerns

**Analysis Date:** 2026-02-04

## Security Issues

**Hardcoded Default SECRET_KEY:**
- Issue: `config.py` line 18 uses a development secret key as fallback
- Files: `config.py`
- Impact: In production without proper SECRET_KEY environment variable, all Flask sessions and CSRF tokens are compromised
- Recommendation: Remove the fallback default. Require explicit environment variable in production. Add startup validation to fail on missing SECRET_KEY in non-dev environments

**Debug Mode Enabled in Production:**
- Issue: `app.py` line 52 runs with `debug=True` unconditionally
- Files: `app.py`
- Impact: Exposes detailed stack traces, allows code execution through the debugger, and weakens security posture
- Recommendation: Use environment variable to control debug mode: `app.run(debug=os.environ.get('FLASK_ENV') == 'development')`

**Weak Exception Handling:**
- Issue: Multiple bare `except:` clauses that catch all exceptions including KeyboardInterrupt and SystemExit
- Files: `services/ocr_service.py` line 69, `services/analysis_engine.py` line 280, `services/tax_parser.py` line 484, `models/irs_reference.py` line 19
- Impact: Masks critical errors and makes debugging difficult; can hide security issues
- Recommendation: Replace with specific exception types: `except (ValueError, TypeError, KeyError):` or similar

**No Input Validation on Numeric Parameters:**
- Issue: `routes/calculator.py` lines 36-39 accept `tax_year` as integer without bounds checking
- Files: `routes/calculator.py`
- Impact: Malicious users can request arbitrary years (negative, year 3000, etc.) causing unexpected behavior
- Recommendation: Add validation: `assert 1900 <= tax_year <= 2100`

**Unencrypted File Paths in Database:**
- Issue: `models/document.py` stores full file paths in `file_path` column without encryption
- Files: `models/document.py` line 10
- Impact: If database is compromised, attackers can directly access all uploaded files via known paths
- Recommendation: Either store relative paths only, or encrypt file paths in database

## Technical Debt

**Encryption Key Generation Weakness:**
- Issue: `models/client.py` lines 35-42 derives encryption key from SECRET_KEY using SHA256
- Files: `models/client.py`
- Impact: Not cryptographically secure for encryption; SHA256 is a hash not a key derivation function. Also limits key entropy if SECRET_KEY is weak
- Fix approach: Use PBKDF2 or Argon2 for key derivation, and store derived key in environment variable instead of deriving it each time

**Excessive Database Queries in Analysis:**
- Issue: `services/analysis_engine.py` calculates a hash of all ExtractedData timestamps on every analysis (lines 24-35)
- Files: `services/analysis_engine.py`
- Cause: No caching of version hash; recalculates even if not needed
- Impact: O(n) query overhead for every analysis when data count grows
- Improvement path: Store data_version_hash in the database, update only when ExtractedData changes. Or use database trigger/event-based approach

**Tax Data Placeholder Detection is Fragile:**
- Issue: `database/init_db.py` lines 151-192 detect placeholder tax data by checking if rate==0.05 and deduction==2000
- Files: `database/init_db.py`
- Cause: Magic numbers without documentation; relies on sampling (first 10 records)
- Impact: Could miss placeholder data if records are reordered; could false-positive if real data matches thresholds
- Fix approach: Add explicit `is_placeholder` flag to TaxBracket model, or use database metadata

**Missing Error Handling in Document Processing:**
- Issue: `routes/documents.py` line 78-116 updates OCR status but if commit fails, status becomes inconsistent
- Files: `routes/documents.py`
- Cause: No rollback on extraction failure; exception handling updates status to 'failed' after already committing 'processing'
- Impact: Database inconsistency; retrying same document will re-extract and re-analyze
- Fix approach: Use database transaction savepoints, or refactor status update logic to be more atomic

## Known Bugs

**SSN Decryption Failures Return None Silently:**
- Symptoms: `models/client.py` get_ssn() returns None if decryption fails (line 63)
- Files: `models/client.py` lines 54-63
- Trigger: If encryption key changes or corrupted data in database
- Current behavior: No error logged; frontend receives None without indication of failure
- Recommendation: Log encryption failures, return error indicator or throw exception to alert user

**Integer Overflow in Tax Calculations:**
- Symptoms: Very large income values could exceed float precision
- Files: `services/tax_calculator.py` (uses float throughout)
- Cause: Python floats have ~15-17 significant digits
- Impact: Calculations with income >$1 trillion may lose precision; unlikely in practice but possible
- Recommendation: Use Decimal type throughout tax calculations instead of float

## Fragile Areas

**OCR Service Dependency:**
- Files: `services/ocr_service.py`
- Why fragile: Dependency on external Tesseract binary for image OCR; fails silently if not installed (returns empty string)
- Safe modification: Keep graceful degradation, but add logging when Tesseract is unavailable
- Test coverage: No tests for OCR service; difficult to test without fixtures

**Tax Parser Form Detection:**
- Files: `services/tax_parser.py` lines 7-34
- Why fragile: Regex patterns brittle to OCR variations (spacing, case, line breaks)
- Safe modification: Add confidence scoring for form detection; allow manual override
- Test coverage: Gaps - no unit tests for regex patterns; only works if OCR produces exact strings

**Analysis Caching Strategy:**
- Files: `services/analysis_engine.py` lines 56-72
- Why fragile: Caching based on timestamp hash is subject to false cache invalidation if document timestamps are updated
- Safe modification: Add explicit cache invalidation endpoint, or use document modification time instead
- Test coverage: No tests for cache behavior; hard to verify when cache is actually used

## Performance Bottlenecks

**Database N+1 Queries in Analysis:**
- Problem: `services/analysis_engine.py` queries ExtractedData, then organizes by form_type without eager loading
- Files: `services/analysis_engine.py` lines 50, 75-79
- Cause: Each form_type access triggers separate SQL queries
- Impact: For client with 50+ extracted data records, could result in multiple database round-trips
- Improvement path: Use SQLAlchemy eager loading or single query with group_by

**Tax Parser Regex Compilation on Every Call:**
- Problem: `services/tax_parser.py` recompiles FORM_PATTERNS regex on every parse call
- Files: `services/tax_parser.py` lines 7-34, 72-74
- Cause: Patterns not pre-compiled; regex compiled inline
- Impact: Measurable overhead for processing multiple documents sequentially
- Improvement path: Pre-compile patterns at class initialization

**Full Table Scan for Analysis Summary:**
- Problem: `services/analysis_engine.py` line 59 queries for first AnalysisSummary without indexing on (client_id, tax_year)
- Files: `services/analysis_engine.py`
- Impact: O(n) scan if database grows to thousands of clients
- Improvement path: Add database index: `db.Index('ix_analysis_summary_client', AnalysisSummary.client_id)`

## Scaling Limits

**SQLite Database Limitation:**
- Current capacity: SQLite handles ~100MB databases reasonably; ~1M records
- Limit: Single-file database becomes slow with concurrent writes; no sharding support
- Scaling path: Migrate to PostgreSQL or MySQL when reaching 10K+ clients or handling concurrent uploads

**File Storage on Local Filesystem:**
- Current capacity: Depends on disk space; no limit enforcement at application level
- Limit: `app.config['MAX_CONTENT_LENGTH']` set to 16MB, but no total storage quota
- Scaling path: Move uploads to cloud storage (AWS S3, Google Cloud Storage) when reaching 1000+ documents

**Single-Threaded Flask Development Server:**
- Current capacity: Can handle ~10-50 concurrent users
- Limit: Built-in server not suitable for production load
- Scaling path: Deploy with Gunicorn/uWSGI with multiple worker processes

## Missing Critical Features

**No Audit Logging:**
- Problem: No logging of data access or modifications (who viewed which client, when)
- Blocks: Cannot comply with HIPAA/GLBA audit trail requirements
- Impact: Cannot track data access or detect unauthorized activity

**No Authentication/Authorization:**
- Problem: All endpoints accessible without login; no user roles or access control
- Blocks: Cannot restrict clients to own data; cannot implement multi-user scenarios
- Impact: Critical security gap - any user can view/modify any client

**No Data Validation Rules:**
- Problem: No schema validation for extracted tax data (e.g., wages should be positive, SSN format)
- Blocks: Cannot prevent garbage data from corrupting analysis
- Impact: Bad OCR data produces incorrect analysis results

**No Rate Limiting:**
- Problem: No protection against API abuse or brute force
- Blocks: System vulnerable to DoS attacks
- Impact: Single user could exhaust server resources with concurrent upload/analysis requests

## Test Coverage Gaps

**OCR Service Not Tested:**
- What's not tested: `services/ocr_service.py` extraction logic; no fixtures for PDF/image files
- Files: `services/ocr_service.py`
- Risk: Changes to OCR logic could break silently; image OCR completely untested
- Priority: High - OCR is critical path for document processing

**Tax Parser Regex Patterns Not Tested:**
- What's not tested: Form detection accuracy; handling of malformed OCR text
- Files: `services/tax_parser.py` lines 7-34
- Risk: OCR variations could cause missed form detection with no error indication
- Priority: High - parser is core business logic

**Analysis Engine Caching Not Tested:**
- What's not tested: Cache hit/miss behavior; behavior when data changes
- Files: `services/analysis_engine.py`
- Risk: Silent cache invalidation issues; hard to debug in production
- Priority: Medium - caching is optimization, not critical

**Document Upload Not Tested:**
- What's not tested: File validation, malicious file handling, concurrent uploads
- Files: `routes/documents.py`
- Risk: Could accept invalid files or have race conditions
- Priority: High - upload is entry point for data

**Tax Calculator Not Tested:**
- What's not tested: Bracket calculations; edge cases (zero income, very high income)
- Files: `services/tax_calculator.py`
- Risk: Incorrect tax calculations would produce wrong advice
- Priority: Critical - core business logic

---

*Concerns audit: 2026-02-04*
