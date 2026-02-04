# Testing Patterns

**Analysis Date:** 2026-02-04

## Test Framework

**Status:** No testing framework detected

- No test files found in codebase (`test_*.py`, `*_test.py`, `tests/` directory)
- No pytest configuration (`pytest.ini`, `setup.cfg` with `[tool:pytest]`)
- No unittest patterns found
- No mock/patch decorators detected
- No test requirements in `requirements.txt`

**Recommendation:** Implement test framework as testing is critical gap. No test coverage exists.

## Test File Organization

**Location:** Not applicable - no tests present

**Naming:** Would use standard Python conventions if implemented:
- `test_*.py` for files
- `test_*()` for functions
- `Test*` for classes

**Structure:** Would separate into `tests/` directory mirroring `src/` layout:
```
tests/
├── test_models/
│   ├── test_client.py
│   ├── test_analysis.py
│   └── test_tax_tables.py
├── test_routes/
│   ├── test_clients.py
│   ├── test_documents.py
│   ├── test_calculator.py
│   └── test_analysis.py
├── test_services/
│   ├── test_tax_calculator.py
│   ├── test_ocr_service.py
│   ├── test_tax_parser.py
│   └── test_analysis_engine.py
└── conftest.py  # Shared fixtures
```

## Test Framework Recommendation

**Recommended Stack:**
- **Runner:** pytest
- **Assertion:** pytest built-in assertions
- **Mocking:** pytest-mock or unittest.mock
- **Database:** pytest-flask with SQLAlchemy test fixtures
- **Coverage:** pytest-cov

**Required additions to requirements.txt:**
```
pytest==7.4.0
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.11.1
```

**Configuration file (pytest.ini):**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=. --cov-report=html --cov-report=term-missing
```

**Run Commands:**
```bash
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest -k "test_name"       # Run specific test by name
pytest --cov               # With coverage report
pytest -m integration      # Run only integration tests (if marked)
pytest -x                  # Stop on first failure
pytest --lf                # Run only last failed tests
```

## Test Structure Pattern

**Based on existing code, recommended test pattern:**

```python
# tests/test_services/test_tax_calculator.py
import pytest
from services.tax_calculator import TaxCalculator
from models import TaxBracket, StandardDeduction

class TestTaxCalculator:
    """Tests for TaxCalculator service"""

    @pytest.fixture
    def tax_calculator(self):
        """Provide TaxCalculator instance"""
        return TaxCalculator

    def test_convert_income_to_annual_monthly(self, tax_calculator):
        """Test conversion from monthly to annual income"""
        result = tax_calculator.convert_income_to_annual(5000, 'monthly')
        assert result == 60000.0

    def test_convert_income_to_annual_invalid_frequency(self, tax_calculator):
        """Test with invalid frequency defaults to 1.0 multiplier"""
        result = tax_calculator.convert_income_to_annual(5000, 'unknown')
        assert result == 5000.0

    def test_convert_income_zero(self, tax_calculator):
        """Test with zero income returns zero"""
        result = tax_calculator.convert_income_to_annual(0, 'annual')
        assert result == 0.0
```

**Patterns:**
- Class-based organization with `Test` prefix
- Fixtures for setup/teardown and dependency injection
- Descriptive test names: `test_action_scenario`
- Docstrings explain "what" is being tested
- Use `assert` for all validations

## Mocking Strategy

**Framework:** Would use `unittest.mock` or `pytest-mock`

**What to Mock:**
- Database queries: Use in-memory SQLite for testing
- External services: OCR Service (pdfplumber, pytesseract)
- File I/O: Mock file uploads and reads
- Environment variables: Mock TESSERACT_CMD, SECRET_KEY

**What NOT to Mock:**
- Core business logic: TaxCalculator calculations must run real
- Model layer: Use test database
- JSON serialization: Test actual to_dict() implementations
- Math operations: Must be precise

**Example mocking pattern needed:**

```python
# tests/test_services/test_ocr_service.py
from unittest.mock import Mock, patch, MagicMock
from services.ocr_service import OCRService
import pytest

class TestOCRService:
    """Tests for OCRService"""

    @patch('services.ocr_service.pdfplumber.open')
    def test_extract_from_pdf_success(self, mock_pdf_open):
        """Test successful PDF text extraction"""
        # Setup mock
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test extracted text"
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Execute
        result = OCRService._extract_from_pdf('test.pdf')

        # Assert
        assert result == "Test extracted text"
        mock_pdf_open.assert_called_once_with('test.pdf')

    @patch('services.ocr_service.pytesseract.image_to_string')
    @patch('services.ocr_service.Image.open')
    def test_extract_from_image_success(self, mock_image_open, mock_ocr):
        """Test successful image OCR"""
        mock_image = Mock()
        mock_image.mode = 'RGB'
        mock_image_open.return_value = mock_image
        mock_ocr.return_value = "Extracted from image"

        result = OCRService._extract_from_image('test.jpg')

        assert result == "Extracted from image"
        mock_ocr.assert_called_once_with(mock_image)
```

## Fixtures and Factories

**Test Data Strategy:**

```python
# tests/conftest.py
import pytest
from models import db, Client, Document, TaxBracket, StandardDeduction
from app import create_app

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Provide Flask test client"""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Provide application context"""
    with app.app_context():
        yield app

@pytest.fixture
def test_client(app_context):
    """Create test client model"""
    client = Client(
        first_name='John',
        last_name='Doe',
        filing_status='single',
        email='john@example.com',
        ssn=None
    )
    db.session.add(client)
    db.session.commit()
    return client

@pytest.fixture
def test_client_married(app_context):
    """Create test married filing jointly client"""
    client = Client(
        first_name='Jane',
        last_name='Smith',
        filing_status='married_joint',
        email='jane@example.com',
        ssn=None
    )
    db.session.add(client)
    db.session.commit()
    return client

# Factory pattern for tax brackets
def create_tax_bracket(filing_status, tax_type, bracket_min, bracket_max, tax_rate, tax_year=2026):
    """Factory to create test tax bracket"""
    bracket = TaxBracket(
        filing_status=filing_status,
        tax_type=tax_type,
        state_code=None if tax_type == 'federal' else 'CA',
        bracket_min=bracket_min,
        bracket_max=bracket_max,
        tax_rate=tax_rate,
        tax_year=tax_year
    )
    db.session.add(bracket)
    db.session.commit()
    return bracket

@pytest.fixture
def federal_brackets_2026(app_context):
    """Create 2026 federal tax brackets for single filer"""
    return [
        create_tax_bracket('single', 'federal', 0, 11600, 0.10),
        create_tax_bracket('single', 'federal', 11600, 47150, 0.12),
        create_tax_bracket('single', 'federal', 47150, 100525, 0.22),
    ]
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Model-specific factories: `tests/factories.py` or `tests/test_models/conftest.py`
- Route-specific fixtures: `tests/test_routes/conftest.py`

## Coverage

**Requirements:** Not enforced - no coverage tool configured

**Target:** Recommend minimum 80% overall coverage
- Models: 100% (simple data classes)
- Services: 90%+ (core business logic)
- Routes: 70% (handles error cases from services)

**View Coverage:**
```bash
pytest --cov=.
pytest --cov=. --cov-report=html    # Generate HTML report
open htmlcov/index.html              # View in browser
```

## Test Types

**Unit Tests:**
- **Scope:** Individual functions and methods in isolation
- **Approach:** Test single responsibility; mock external dependencies
- **Example:** `test_services/test_tax_calculator.py` - test each tax calculation method
- **Location:** `tests/test_services/`, `tests/test_models/`

```python
def test_calculate_taxable_income():
    """Test taxable income calculation"""
    result = TaxCalculator.calculate_taxable_income(
        gross_income=100000,
        standard_deduction=13850,
        qbi_deduction=0
    )
    assert result == 86150.0
    assert result >= 0  # Cannot be negative
```

**Integration Tests:**
- **Scope:** Multiple components working together
- **Approach:** Test real database, real service interactions
- **Example:** Test document upload → OCR → parsing → analysis workflow
- **Location:** `tests/test_integration/`
- **Markers:** Use `@pytest.mark.integration` for selective running

```python
@pytest.mark.integration
def test_document_upload_to_analysis_workflow(client, app_context, test_client):
    """Test complete workflow from document upload to tax analysis"""
    # 1. Upload document
    # 2. Process with OCR
    # 3. Parse tax data
    # 4. Trigger analysis
    # 5. Verify analysis results
```

**E2E Tests:**
- **Status:** Not recommended at this time (no frontend testing framework)
- **If implemented:** Use Selenium + Flask test client
- **Scope:** Complete user flows through API

## Common Patterns

**Async Testing:**
Document processing has async analysis (but no async/await used):

```python
# routes/documents.py, line 92-98 shows nested try-except pattern
# Test pattern would be:

def test_document_analysis_failure_handled(client, app_context, test_client):
    """Test that analysis failure doesn't fail document processing"""
    # Mock AnalysisEngine to raise error
    with patch('routes.documents.AnalysisEngine.analyze_client') as mock_analysis:
        mock_analysis.side_effect = Exception("Analysis failed")

        # Upload and process document
        response = client.post('/api/documents/1/process')

        # Should succeed despite analysis error
        assert response.status_code == 200
        data = response.get_json()
        assert data['analysis_triggered'] == False
        assert 'analysis_error' in data
```

**Error Testing:**
Test both happy path and error conditions:

```python
def test_calculate_tax_missing_income():
    """Test tax calculation with missing required field"""
    # Should return 400 with error message
    response = client.post('/api/calculator/calculate', json={
        'filing_status': 'single'
        # missing 'income'
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_create_client_missing_required_field():
    """Test client creation without required fields"""
    response = client.post('/api/clients', json={
        'first_name': 'John'
        # missing last_name and filing_status
    })
    assert response.status_code == 400
    assert 'Missing required field' in response.get_json()['error']
```

**Database State Testing:**
```python
def test_client_ssn_encrypted(app_context):
    """Test that SSN is encrypted when stored"""
    client = Client(
        first_name='John',
        last_name='Doe',
        filing_status='single',
        ssn='123-45-6789'
    )
    db.session.add(client)
    db.session.commit()

    # Retrieve from database
    retrieved = Client.query.first()

    # SSN should be encrypted (not plain text)
    assert retrieved.ssn != '123-45-6789'

    # But should decrypt to original
    assert retrieved.get_ssn() == '123-45-6789'
```

---

*Testing analysis: 2026-02-04*
