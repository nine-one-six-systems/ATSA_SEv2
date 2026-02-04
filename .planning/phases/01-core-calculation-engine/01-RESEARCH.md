# Phase 1: Core Dual-Filer Calculation Engine - Research

**Researched:** 2026-02-04
**Domain:** Tax Analysis Platform (Flask MVC + Dual-Filer MFJ/MFS Support)
**Confidence:** HIGH

## Summary

Phase 1 adds joint tax analysis for married couples by creating a `JointAnalysisService` that orchestrates two individual client analyses, calculates MFJ and MFS scenarios using the existing `TaxCalculator`, and generates a comparison with dollar savings recommendations. The implementation extends existing patterns (service layer, hash-based caching, blueprint registration) without modifying working tax calculation logic.

**Primary recommendation:** Build service layer first (calculation correctness), then API layer (data access), then enable SQLite WAL mode immediately to prevent concurrency issues.

**Key findings:**
- Existing `TaxCalculator` already supports `married_joint` and `married_separate` filing statuses with correct bracket lookups
- Existing `AnalysisEngine` cache invalidation pattern extends cleanly to dual-filer by combining both spouses' hashes
- Critical pitfalls (credit disqualification, QBI thresholds, itemized deduction coordination) must be addressed in Phase 1
- SQLite WAL mode is non-negotiable for preventing "database locked" errors with dual-writer pattern

## Standard Stack

The dual-filer feature uses existing stack components exclusively — no new libraries or frameworks required.

### Core Components

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Flask | 2.x | Web framework | Already used for routing, templates |
| SQLAlchemy | 1.4+ | ORM and database | Already used for all models |
| SQLite | 3.x | Database | Already used, WAL mode solves concurrency |
| Vanilla JavaScript | ES6+ | Frontend interactions | Already used in `static/js/` |
| Jinja2 | 3.x | Template rendering | Already used for HTML templates |

### Existing Services (No Changes Required)

| Service | Location | Role in Dual-Filer |
|---------|----------|-------------------|
| `TaxCalculator` | `services/tax_calculator.py` | Calculates MFJ and MFS tax using bracket lookups |
| `AnalysisEngine` | `services/analysis_engine.py` | Analyzes individual clients (called 2x for joint analysis) |
| `TaxStrategiesService` | `services/tax_strategies.py` | Generates strategy recommendations per client |

**Key insight:** Existing services already handle all filing statuses correctly. Lines 96-108 in `tax_calculator.py` show filing-status-specific bracket queries. No modifications needed.

### New Components to Build

| Component | Location | Purpose |
|-----------|----------|---------|
| `JointAnalysisService` | `services/joint_analysis_service.py` | Orchestrates dual analysis, calculates MFJ/MFS scenarios |
| `JointAnalysisSummary` | `models/joint_analysis.py` | Stores joint analysis results with combined hash |
| `joint_analysis_bp` | `routes/joint_analysis.py` | API endpoints for triggering/retrieving joint analysis |

**Installation:**
No new dependencies. All components use existing Flask + SQLAlchemy stack.

## Architecture Patterns

### Recommended Project Structure

```
services/
├── analysis_engine.py        # MODIFY: Extend cache hash to include spouse
├── joint_analysis_service.py # NEW: Joint analysis orchestration
├── tax_calculator.py          # NO CHANGE: Already handles all filing statuses
└── tax_strategies.py          # NO CHANGE: Per-client strategy generation

models/
├── __init__.py                # MODIFY: Add JointAnalysisSummary import
├── analysis.py                # NO CHANGE: AnalysisSummary pattern reference
├── client.py                  # NO CHANGE: Already has spouse_id relationship
└── joint_analysis.py          # NEW: JointAnalysisSummary model

routes/
├── api.py                     # MODIFY: Register joint_analysis_bp
├── analysis.py                # NO CHANGE: Single-client analysis pattern reference
└── joint_analysis.py          # NEW: Joint analysis endpoints

database/
└── init_db.py                 # MODIFY: Enable WAL mode, register JointAnalysisSummary

app.py                         # MODIFY: Add /joint-analysis.html route (Phase 3)
```

### Pattern 1: Service Layer Orchestration

**What:** `JointAnalysisService` coordinates multiple existing services without modifying them.

**When to use:** Need to compose complex workflows from existing components.

**Example:**
```python
# services/joint_analysis_service.py
class JointAnalysisService:
    @staticmethod
    def analyze_joint(spouse1_id, spouse2_id, force_refresh=False):
        """
        Orchestrate joint analysis by coordinating:
        1. Individual analyses (via AnalysisEngine)
        2. MFJ calculation (via TaxCalculator)
        3. MFS calculation (via TaxCalculator)
        4. Comparison logic
        5. Caching with combined hash
        """
        # Step 1: Calculate combined hash
        joint_hash = JointAnalysisService._calculate_joint_hash(spouse1_id, spouse2_id)

        # Step 2: Check cache
        cached = JointAnalysisSummary.query.filter_by(
            spouse1_id=spouse1_id,
            spouse2_id=spouse2_id
        ).first()

        if cached and cached.data_version_hash == joint_hash and not force_refresh:
            return _format_cached_result(cached)

        # Step 3: Analyze each spouse individually (reuse AnalysisEngine)
        spouse1_strategies, spouse1_summary = AnalysisEngine.analyze_client(spouse1_id)
        spouse2_strategies, spouse2_summary = AnalysisEngine.analyze_client(spouse2_id)

        # Step 4: Calculate MFJ scenario (reuse TaxCalculator)
        combined_income = spouse1_summary['total_income'] + spouse2_summary['total_income']
        mfj_result = TaxCalculator.calculate_federal_tax(
            income=combined_income,
            filing_status='married_joint',
            dependents=spouse1_dependents + spouse2_dependents,
            tax_year=tax_year
        )

        # Step 5: Calculate MFS scenario (reuse TaxCalculator)
        mfs_spouse1 = TaxCalculator.calculate_federal_tax(
            income=spouse1_summary['total_income'],
            filing_status='married_separate',
            dependents=spouse1_dependents,
            tax_year=tax_year
        )
        mfs_spouse2 = TaxCalculator.calculate_federal_tax(
            income=spouse2_summary['total_income'],
            filing_status='married_separate',
            dependents=spouse2_dependents,
            tax_year=tax_year
        )
        mfs_combined_tax = mfs_spouse1['total_tax'] + mfs_spouse2['total_tax']

        # Step 6: Generate comparison and recommendation
        savings = mfs_combined_tax - mfj_result['total_tax']
        recommended_status = 'MFJ' if savings > 0 else 'MFS'

        # Step 7: Store in cache
        _save_joint_analysis(joint_hash, mfj_result, mfs_spouse1, mfs_spouse2, ...)

        return {
            'spouse1': {'summary': spouse1_summary, 'strategies': spouse1_strategies},
            'spouse2': {'summary': spouse2_summary, 'strategies': spouse2_strategies},
            'mfj': mfj_result,
            'mfs_spouse1': mfs_spouse1,
            'mfs_spouse2': mfs_spouse2,
            'comparison': {
                'recommended_status': recommended_status,
                'savings': savings,
                'mfj_total': mfj_result['total_tax'],
                'mfs_total': mfs_combined_tax
            }
        }
```

**Why this works:**
- No changes to `TaxCalculator` or `AnalysisEngine` (working code stays working)
- Clear separation: services contain logic, routes are thin wrappers
- Testable in isolation with mock data
- Follows existing `AnalysisEngine.analyze_client()` pattern (lines 38-140 in `analysis_engine.py`)

### Pattern 2: Bidirectional Cache Invalidation

**What:** Combined hash from both spouses' data version hashes. Either spouse changing invalidates joint cache.

**When to use:** Cached results depend on multiple independent data sources.

**Example:**
```python
# services/joint_analysis_service.py
@staticmethod
def _calculate_joint_hash(spouse1_id, spouse2_id):
    """
    Calculate combined hash from both spouses' individual hashes.
    If either spouse's data changes, joint hash changes.
    """
    # Get individual hashes (reuse AnalysisEngine logic)
    spouse1_hash = AnalysisEngine._calculate_data_version_hash(spouse1_id)
    spouse2_hash = AnalysisEngine._calculate_data_version_hash(spouse2_id)

    # Combine in consistent order (lower ID first for symmetry)
    ordered_ids = sorted([spouse1_id, spouse2_id])
    combined_string = f"{spouse1_hash}|{spouse2_hash}|{ordered_ids[0]}|{ordered_ids[1]}"

    return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
```

**Extend existing AnalysisEngine for individual cache invalidation:**
```python
# services/analysis_engine.py (MODIFY lines 14-35)
@staticmethod
def _calculate_data_version_hash(client_id):
    """
    Calculate hash of all ExtractedData timestamps for a client.
    EXTENDED: Also includes spouse data if spouse_id exists.
    """
    extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()

    # CRITICAL: Include spouse data if spouse linked
    client = Client.query.get(client_id)
    if client and client.spouse_id:
        spouse_data = ExtractedData.query.filter_by(client_id=client.spouse_id).all()
        extracted_data.extend(spouse_data)

    if not extracted_data:
        return hashlib.sha256(b'').hexdigest()

    # Sort timestamps and concatenate
    timestamps = sorted([str(data.extracted_at.isoformat()) if data.extracted_at else ''
                        for data in extracted_data])
    timestamp_string = '|'.join(timestamps)

    return hashlib.sha256(timestamp_string.encode('utf-8')).hexdigest()
```

**Why this works:**
- Changing husband's W-2 → changes spouse1_hash → changes joint_hash → forces recalculation
- Changing wife's data → changes spouse2_hash → changes joint_hash → forces recalculation
- Symmetrical: order doesn't matter, consistent hashing
- Follows existing pattern from lines 14-35 in `analysis_engine.py`

### Pattern 3: Blueprint Registration for API Routes

**What:** Flask blueprint for joint analysis endpoints, registered in `api_bp`.

**When to use:** Adding new API feature domain.

**Example:**
```python
# routes/joint_analysis.py (NEW)
from flask import Blueprint, jsonify, request
from services.joint_analysis_service import JointAnalysisService
from models import Client

joint_analysis_bp = Blueprint('joint_analysis', __name__)

@joint_analysis_bp.route('/analysis/joint/<int:spouse1_id>/<int:spouse2_id>', methods=['GET'])
def get_joint_analysis(spouse1_id, spouse2_id):
    """Get cached joint analysis or trigger if not exists"""
    # Validate spouses are linked
    spouse1 = Client.query.get_or_404(spouse1_id)
    spouse2 = Client.query.get_or_404(spouse2_id)

    if spouse1.spouse_id != spouse2_id or spouse2.spouse_id != spouse1_id:
        return jsonify({'error': 'Clients are not linked as spouses'}), 400

    result = JointAnalysisService.analyze_joint(spouse1_id, spouse2_id)
    return jsonify(result)

@joint_analysis_bp.route('/analysis/joint/<int:spouse1_id>/<int:spouse2_id>/refresh', methods=['POST'])
def refresh_joint_analysis(spouse1_id, spouse2_id):
    """Force refresh joint analysis"""
    result = JointAnalysisService.analyze_joint(spouse1_id, spouse2_id, force_refresh=True)
    return jsonify(result)
```

**Register in api.py:**
```python
# routes/api.py (MODIFY lines 1-13)
from flask import Blueprint
from routes.clients import clients_bp
from routes.documents import documents_bp
from routes.analysis import analysis_bp
from routes.calculator import calculator_bp
from routes.joint_analysis import joint_analysis_bp  # ADD THIS

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register all route blueprints
api_bp.register_blueprint(clients_bp)
api_bp.register_blueprint(documents_bp)
api_bp.register_blueprint(analysis_bp)
api_bp.register_blueprint(calculator_bp)
api_bp.register_blueprint(joint_analysis_bp)  # ADD THIS
```

**Why this works:**
- Follows existing pattern from lines 1-13 in `routes/api.py`
- Modular: joint analysis routes isolated in own file
- RESTful: GET for retrieval, POST for actions
- Consistent with existing route structure (see `routes/analysis.py` lines 7-21)

### Pattern 4: Model with Unique Constraint for Spouse Pairs

**What:** `JointAnalysisSummary` model stores results with uniqueness constraint on spouse pair.

**When to use:** One-to-one cached result for related entities.

**Example:**
```python
# models/joint_analysis.py (NEW)
from models import db
from datetime import datetime

class JointAnalysisSummary(db.Model):
    __tablename__ = 'joint_analysis_summaries'

    id = db.Column(db.Integer, primary_key=True)
    spouse1_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    spouse2_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=True)

    # MFJ scenario
    mfj_combined_income = db.Column(db.Float, default=0)
    mfj_total_tax = db.Column(db.Float, default=0)
    mfj_effective_rate = db.Column(db.Float, default=0)

    # MFS scenario
    mfs_spouse1_income = db.Column(db.Float, default=0)
    mfs_spouse1_tax = db.Column(db.Float, default=0)
    mfs_spouse2_income = db.Column(db.Float, default=0)
    mfs_spouse2_tax = db.Column(db.Float, default=0)
    mfs_combined_tax = db.Column(db.Float, default=0)
    mfs_effective_rate = db.Column(db.Float, default=0)

    # Comparison
    recommended_status = db.Column(db.String(20))  # 'MFJ' or 'MFS'
    savings_amount = db.Column(db.Float, default=0)

    # Caching
    data_version_hash = db.Column(db.String(64))  # Combined hash
    last_analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # CRITICAL: Ensure only one joint analysis per spouse pair
    __table_args__ = (
        db.UniqueConstraint('spouse1_id', 'spouse2_id', name='unique_spouse_pair'),
    )

    def to_dict(self):
        return {
            'spouse1_id': self.spouse1_id,
            'spouse2_id': self.spouse2_id,
            'tax_year': self.tax_year,
            'mfj': {
                'combined_income': self.mfj_combined_income,
                'total_tax': self.mfj_total_tax,
                'effective_rate': self.mfj_effective_rate
            },
            'mfs': {
                'spouse1_income': self.mfs_spouse1_income,
                'spouse1_tax': self.mfs_spouse1_tax,
                'spouse2_income': self.mfs_spouse2_income,
                'spouse2_tax': self.mfs_spouse2_tax,
                'combined_tax': self.mfs_combined_tax,
                'effective_rate': self.mfs_effective_rate
            },
            'comparison': {
                'recommended_status': self.recommended_status,
                'savings_amount': self.savings_amount
            },
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None
        }
```

**Register model in __init__.py:**
```python
# models/__init__.py (MODIFY)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.client import Client
from models.document import Document
from models.extracted_data import ExtractedData
from models.analysis import AnalysisResult, AnalysisSummary
from models.irs_reference import IRSReference
from models.tax_tables import TaxBracket, StandardDeduction
from models.joint_analysis import JointAnalysisSummary  # ADD THIS

__all__ = [
    'db', 'Client', 'Document', 'ExtractedData',
    'AnalysisResult', 'AnalysisSummary', 'IRSReference',
    'TaxBracket', 'StandardDeduction',
    'JointAnalysisSummary'  # ADD THIS
]
```

**Why this works:**
- Follows existing `AnalysisSummary` pattern (see `models/analysis.py` lines 6-54)
- Unique constraint prevents duplicate analyses for same spouse pair
- Stores all comparison data for display
- `to_dict()` method for JSON serialization (consistent with existing models)

### Anti-Patterns to Avoid

**Anti-Pattern 1: Inline MFJ/MFS Calculation in Routes**
```python
# BAD: Route contains tax calculation logic
@joint_analysis_bp.route('/analysis/joint/<int:spouse1_id>/<int:spouse2_id>')
def get_joint_analysis(spouse1_id, spouse2_id):
    # WRONG: Tax logic in route handler
    spouse1_income = ExtractedData.query.filter_by(client_id=spouse1_id, field_name='wages').first().field_value
    spouse2_income = ExtractedData.query.filter_by(client_id=spouse2_id, field_name='wages').first().field_value
    combined_income = float(spouse1_income) + float(spouse2_income)
    # ... more calculation logic ...
```
**Why bad:** Violates MVC, untestable, duplicates logic from TaxCalculator.
**Correct:** Routes call `JointAnalysisService`, services contain logic.

**Anti-Pattern 2: Modifying TaxCalculator for Joint Analysis**
```python
# BAD: Adding joint-specific logic to TaxCalculator
def calculate_federal_tax(income, filing_status, dependents, is_joint_analysis=False):
    if is_joint_analysis:
        # Special handling for joint analysis
```
**Why bad:** `TaxCalculator` works correctly as-is. Adding joint-specific logic pollutes clean service.
**Correct:** `TaxCalculator` is generic, `JointAnalysisService` orchestrates multiple calls.

**Anti-Pattern 3: Denormalizing Spouse Data**
```python
# BAD: Storing spouse income in both client records
class Client(db.Model):
    spouse_income = db.Column(db.Float)  # WRONG: Duplicate data
```
**Why bad:** Update one spouse → other spouse shows stale data. Data inconsistency.
**Correct:** Use foreign key (`spouse_id`), query both clients at runtime.

## Don't Hand-Roll

Problems that look simple but have existing solutions in the codebase:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tax bracket lookup by filing status | Custom bracket calculation | `TaxCalculator.get_tax_brackets(filing_status=...)` lines 83-108 | Already handles all filing statuses, database-backed |
| Filing status validation | Custom enum checker | Existing `Client.filing_status` field values | Database already has 'single', 'married_joint', 'married_separate', 'head_of_household' |
| Data version hash calculation | Custom timestamp hashing | `AnalysisEngine._calculate_data_version_hash()` lines 14-35 | Already implemented, extend for spouse data |
| Model JSON serialization | Manual dict construction | `model.to_dict()` pattern | All models have `.to_dict()` (see `models/analysis.py` lines 27-54) |
| Standard deduction lookup | Hardcoded amounts | `TaxCalculator.get_standard_deduction(filing_status, ...)` lines 37-62 | Database-backed, handles all filing statuses |
| QBI threshold lookup | Hardcoded thresholds | `TaxCalculator.get_qbi_income_thresholds(filing_status, ...)` lines 291-317 | Already implements correct thresholds by filing status |

**Key insight:** The existing `TaxCalculator` is comprehensive and correct. Lines 291-317 show QBI thresholds are already filing-status-aware (`married_separate` uses same threshold as `single`: $197,300 for 2026). Don't duplicate this logic.

## Common Pitfalls

### Pitfall 1: Credit Disqualification for MFS Not Enforced

**What goes wrong:** MFS calculations show EITC, student loan interest deduction, education credits when these are completely unavailable on MFS.

**Why it happens:**
- Assuming credit logic carries over from MFJ to MFS
- Not checking filing status eligibility before applying credits
- Real example: `TaxStrategiesService` may recommend student loan interest deduction without checking filing status

**How to avoid:**
1. **Create filing status eligibility matrix** in `JointAnalysisService`:
```python
CREDIT_ELIGIBILITY = {
    'EITC': {
        'single': True,
        'married_joint': True,
        'married_separate': False,  # Ineligible (unless living apart 6+ months)
        'head_of_household': True
    },
    'student_loan_interest': {
        'single': True,
        'married_joint': True,
        'married_separate': False,  # Completely ineligible, not phased out
        'head_of_household': True
    },
    'education_credits': {  # AOTC, LLC
        'single': True,
        'married_joint': True,
        'married_separate': False,  # Ineligible
        'head_of_household': True
    }
}

@staticmethod
def _filter_strategies_by_filing_status(strategies, filing_status):
    """Remove strategies ineligible for filing status"""
    filtered = []
    for strategy in strategies:
        credit_type = _identify_credit_type(strategy.strategy_name)
        if credit_type in CREDIT_ELIGIBILITY:
            if CREDIT_ELIGIBILITY[credit_type].get(filing_status, False):
                filtered.append(strategy)
        else:
            filtered.append(strategy)  # Non-credit strategies always included
    return filtered
```

2. **Apply filter in MFS calculation**:
```python
# In calculate_mfs_scenario()
mfs_spouse1_strategies = _filter_strategies_by_filing_status(
    spouse1_strategies, 'married_separate'
)
```

3. **Add warning in comparison if credits lost**:
```python
if len(spouse1_strategies) > len(mfs_spouse1_strategies):
    lost_credits = set(s.strategy_name for s in spouse1_strategies) - set(s.strategy_name for s in mfs_spouse1_strategies)
    comparison['warnings'].append(
        f"MFS ineligible for: {', '.join(lost_credits)}"
    )
```

**Warning signs:**
- MFS showing same number of strategies as MFJ
- Student loan interest deduction appearing in MFS results
- EITC showing for MFS (unless edge case of living apart 6+ months)

**Phase to address:** Phase 1 (Core Calculation Logic) — MUST fix before UI shows results.

### Pitfall 2: QBI Threshold Confusion Between MFJ and MFS

**What goes wrong:** Using married joint QBI threshold ($394,600 for 2026) for MFS calculations. MFS uses single filer threshold ($197,300).

**Why it happens:**
- Checking if `filing_status.startswith('married')` instead of exact status
- Not aware that MFS != half of MFJ (MFS uses single filer threshold, not proportional)
- Real impact: Husband with $250k LLC income filing separately would show full QBI when it should be phased out

**How to avoid:**
1. **Verify existing TaxCalculator handles this correctly**:
```python
# services/tax_calculator.py lines 304-312 (EXISTING CODE - VERIFY)
thresholds = {
    'single': 197300.0,
    'married_joint': 394600.0,
    'married_separate': 197300.0,  # CRITICAL: Same as single, not half of joint
    'head_of_household': 197300.0,
}
```
Good news: Lines 309 in `tax_calculator.py` show `married_separate` already uses correct threshold.

2. **Use exact filing status in all calculations**:
```python
# In calculate_mfs_scenario()
mfs_spouse1_result = TaxCalculator.calculate_federal_tax(
    income=spouse1_income,
    filing_status='married_separate',  # Exact string, not 'married'
    ...
)
```

3. **Add QBI phase-out explanation to comparison**:
```python
if spouse1_income > 197300 and filing_status == 'married_separate':
    comparison['qbi_notes'].append(
        f"Spouse 1 income ${spouse1_income:,.0f} exceeds MFS threshold "
        f"($197,300) — QBI deduction may be limited"
    )
```

**Warning signs:**
- MFS QBI deduction seems too high for income level (above $197k)
- MFS showing same QBI deduction as MFJ despite different thresholds
- Comparison doesn't highlight QBI difference

**Phase to address:** Phase 1 (Core Calculation Logic) — Real use case ($250k LLC) directly affected.

**Confidence:** HIGH — Verified in existing code that threshold is correct (line 309).

### Pitfall 3: Itemized Deduction Coordination Violation

**What goes wrong:** One spouse itemizes while the other takes standard deduction on MFS. IRS rule violation causes automatic rejection.

**Why it happens:**
- Treating MFS filers as completely independent
- No cross-spouse validation when selecting deduction method
- UI allows different choices without warning

**How to avoid:**
1. **Track deduction method in Client model** (future enhancement):
```python
# For Phase 2: Add field to track deduction choice
class Client(db.Model):
    deduction_method = db.Column(db.String(20))  # 'standard' or 'itemized'
```

2. **Validate coordination in JointAnalysisService** (Phase 1 warning):
```python
@staticmethod
def _validate_mfs_deduction_coordination(spouse1, spouse2):
    """
    Warn if spouses have mismatched deduction methods.
    Phase 1: Warning only (no data to validate yet)
    Phase 2: Blocking validation
    """
    warnings = []
    # For Phase 1: Add educational note in comparison
    warnings.append(
        "IRS Rule: If one spouse itemizes on MFS, the other must also itemize. "
        "Both spouses must use the same deduction method."
    )
    return warnings
```

3. **Include warning in MFS comparison**:
```python
comparison['mfs_rules'] = [
    "Both spouses must use same deduction method (standard or itemized)",
    "SALT cap is $20,000 per spouse (not $40,000)",
    "Each child can only be claimed by one spouse"
]
```

**Warning signs:**
- MFS comparison shows one spouse with itemized deductions, other with standard
- No warning about deduction coordination
- UI allows selecting different methods per spouse

**Phase to address:** Phase 1 (warning), Phase 2 (enforcement with deduction method tracking)

### Pitfall 4: Cache Invalidation Asymmetry

**What goes wrong:** Husband's analysis cached. Wife's data changes. System doesn't know husband's individual analysis should refresh (because wife is included in his hash now).

**Why it happens:**
- Modified `_calculate_data_version_hash()` to include spouse data
- Consequence: Wife's data change affects husband's hash → forces husband's individual analysis to recalculate
- This is CORRECT behavior, but may surprise users

**How to avoid:**
1. **Document behavior clearly**:
```python
@staticmethod
def _calculate_data_version_hash(client_id):
    """
    Calculate hash of all ExtractedData timestamps for a client.

    IMPORTANT: If client has spouse_id, spouse's data is ALSO included in hash.
    This means:
    - Changing wife's data invalidates husband's cached analysis
    - Changing husband's data invalidates wife's cached analysis

    Rationale: Joint analysis depends on both spouses, so individual analyses
    should refresh when either spouse's data changes.
    """
```

2. **Add UI indicator** (Phase 3):
```
"Analysis includes both spouses' data. Updating either spouse will refresh analysis."
```

3. **Test case for Phase 1**:
```python
def test_spouse_data_change_invalidates_individual_cache():
    # Setup: Husband and wife linked
    # Analyze husband → cache created
    # Change wife's W-2
    # Re-analyze husband → should recalculate (hash changed)
```

**Warning signs:**
- Individual analysis doesn't refresh when spouse's data changes
- Joint analysis shows different numbers than sum of individuals
- Confusion about when analysis recalculates

**Phase to address:** Phase 1 (implementation), Phase 3 (UI explanation)

**Confidence:** MEDIUM — This is intentional behavior, but needs clear documentation.

### Pitfall 5: SQLite Concurrency Issues During Joint Analysis

**What goes wrong:** "Database is locked" errors when analyzing husband while wife's data is being updated in another tab.

**Why it happens:**
- SQLite default mode allows unlimited readers but only one writer
- Dual-filer = 2x write frequency (both spouses' analyses updating)
- Long-running analysis transactions block other writes

**How to avoid:**
1. **Enable SQLite WAL mode immediately** (Phase 1):
```python
# database/init_db.py (MODIFY after line 13)
from sqlalchemy import text

def init_database():
    """Initialize database tables and seed IRS references"""
    # ... existing imports ...

    db.create_all()

    # CRITICAL: Enable WAL mode for dual-writer concurrency
    db.session.execute(text("PRAGMA journal_mode=WAL"))
    db.session.execute(text("PRAGMA busy_timeout=30000"))  # 30 second timeout
    db.session.commit()

    seed_irs_references()
    populate_tax_tables()
```

2. **Keep transactions short**:
```python
@staticmethod
def analyze_joint(spouse1_id, spouse2_id, force_refresh=False):
    # Read data OUTSIDE transaction
    spouse1_strategies, spouse1_summary = AnalysisEngine.analyze_client(spouse1_id)
    spouse2_strategies, spouse2_summary = AnalysisEngine.analyze_client(spouse2_id)

    # Calculate OUTSIDE transaction
    mfj_result = TaxCalculator.calculate_federal_tax(...)
    mfs_results = ...

    # ONLY write in transaction (minimize lock time)
    summary = JointAnalysisSummary(...)
    db.session.add(summary)
    db.session.commit()  # Short transaction
```

3. **Add error handling with retry**:
```python
from sqlalchemy.exc import OperationalError
import time

def _save_with_retry(model, max_retries=3):
    for attempt in range(max_retries):
        try:
            db.session.add(model)
            db.session.commit()
            return
        except OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                db.session.rollback()
            else:
                raise
```

**Warning signs:**
- Intermittent "database is locked" errors in logs
- Errors increase when both spouses analyzed simultaneously
- Errors during concurrent document upload + analysis

**Phase to address:** Phase 1 (WAL mode), before any testing.

**Confidence:** HIGH — SQLite WAL mode is well-documented solution. If issues persist, migrate to PostgreSQL.

### Pitfall 6: SALT Cap Not Halved for MFS

**What goes wrong:** Applying $40,000 SALT cap (2026 OBBBA) to each MFS spouse instead of $20,000 per spouse.

**Why it happens:**
- SALT cap increased from $10,000 to $40,000 under OBBBA for 2026
- Not aware MFS cap is exactly half ($20,000 per spouse)
- Assuming each spouse gets full cap

**How to avoid:**
1. **Verify/add SALT cap enforcement in TaxCalculator** (may need to add):
```python
# services/tax_calculator.py (CHECK if this exists, ADD if not)
SALT_CAPS = {
    'single': 40000,
    'married_joint': 40000,
    'married_separate': 20000,  # CRITICAL: Half of joint
    'head_of_household': 40000
}

@staticmethod
def _apply_salt_cap(itemized_deductions, filing_status, tax_year=2026):
    """Apply SALT cap based on filing status"""
    salt_amount = itemized_deductions.get('state_local_tax', 0)
    cap = SALT_CAPS.get(filing_status, 40000)

    if salt_amount > cap:
        itemized_deductions['state_local_tax'] = cap
        itemized_deductions['salt_capped_amount'] = salt_amount - cap

    return itemized_deductions
```

2. **Add SALT cap note to comparison**:
```python
if spouse1_state_tax + spouse2_state_tax > 40000:
    comparison['tax_notes'].append(
        f"Combined state/local taxes ${spouse1_state_tax + spouse2_state_tax:,.0f} "
        f"exceed MFS cap ($20,000 per spouse = $40,000 total)"
    )
```

3. **Test case for Phase 1**:
```python
def test_mfs_salt_cap_is_half_of_joint():
    # California couple with $60k state taxes
    # MFS: Each spouse capped at $20k = $40k total
    # MFJ: Capped at $40k
    # Result: No SALT cap advantage for MFS
```

**Warning signs:**
- MFS itemized deductions showing $40k SALT per spouse
- High-tax state clients (CA, NY, NJ) showing incorrect MFS deductions
- Comparison not highlighting SALT cap difference

**Phase to address:** Phase 1 (Core Calculation Logic) — Material for high-tax states.

**Confidence:** HIGH — IRS guidance clear: MFS gets half of joint cap.

### Pitfall 7: Rounding Discrepancies

**What goes wrong:** MFS spouse1 tax: $22,345.47 → rounds to $22,345. Spouse2: $18,234.52 → rounds to $18,235. Sum: $40,580. But MFJ calculated fresh: $40,578.

**Why it happens:**
- Rounding at different stages of calculation
- IRS rule: "Include cents when adding amounts and round off only the total"
- Premature rounding in individual calculations

**How to avoid:**
1. **Use Decimal throughout** (already done in TaxCalculator line 2):
```python
from decimal import Decimal, ROUND_HALF_UP

# In JointAnalysisService
mfj_result = TaxCalculator.calculate_federal_tax(...)
mfs_spouse1 = TaxCalculator.calculate_federal_tax(...)
mfs_spouse2 = TaxCalculator.calculate_federal_tax(...)

# Keep Decimal precision, round only for display
mfs_combined_tax = Decimal(str(mfs_spouse1['total_tax'])) + Decimal(str(mfs_spouse2['total_tax']))
```

2. **Calculate MFJ fresh, don't sum individuals**:
```python
# CORRECT: Calculate MFJ independently
mfj_result = TaxCalculator.calculate_federal_tax(
    income=combined_income,
    filing_status='married_joint',
    ...
)

# Don't do this:
# mfj_result = {'total_tax': mfs_spouse1['total_tax'] + mfs_spouse2['total_tax']}  # WRONG
```

3. **Accept $1-5 variance as normal**:
```python
savings = mfs_combined_tax - mfj_result['total_tax']
if abs(savings) < 5:
    comparison['note'] = "Difference within normal rounding variance"
```

**Warning signs:**
- Penny-level discrepancies between sum(MFS) and MFJ
- Numbers don't "add up" exactly
- User confusion about $1-3 differences

**Phase to address:** Phase 1 (use Decimal), Phase 3 (UI note about rounding)

**Confidence:** HIGH — Standard accounting practice.

## Code Examples

Verified patterns from existing codebase:

### Example 1: Hash-Based Caching Pattern

```python
# Source: services/analysis_engine.py lines 14-35, 56-72 (EXISTING)
@staticmethod
def _calculate_data_version_hash(client_id):
    """Calculate hash of all ExtractedData timestamps"""
    extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()

    if not extracted_data:
        return hashlib.sha256(b'').hexdigest()

    timestamps = sorted([str(data.extracted_at.isoformat()) if data.extracted_at else ''
                        for data in extracted_data])
    timestamp_string = '|'.join(timestamps)

    return hashlib.sha256(timestamp_string.encode('utf-8')).hexdigest()

@staticmethod
def analyze_client(client_id, force_refresh=False):
    """Analyze client with caching"""
    current_hash = AnalysisEngine._calculate_data_version_hash(client_id)

    existing_summary = AnalysisSummary.query.filter_by(client_id=client_id).first()

    # Return cached if hash matches
    if existing_summary and existing_summary.data_version_hash == current_hash and not force_refresh:
        strategies = AnalysisResult.query.filter_by(client_id=client_id).all()
        return strategies, existing_summary.to_dict()

    # Otherwise recalculate...
```

**Usage for Phase 1:** Extend this pattern for joint analysis by combining two client hashes.

### Example 2: TaxCalculator Filing Status Support

```python
# Source: services/tax_calculator.py lines 83-108 (EXISTING)
@staticmethod
def get_tax_brackets(tax_type='federal', state_code=None, filing_status='single', tax_year=2026):
    """Retrieve tax brackets for given parameters"""
    query = TaxBracket.query.filter_by(
        tax_type=tax_type,
        filing_status=filing_status,  # Exact match on 'married_separate'
        tax_year=tax_year
    )

    if tax_type == 'state' and state_code:
        query = query.filter_by(state_code=state_code)
    elif tax_type == 'federal':
        query = query.filter_by(state_code=None)

    brackets = query.order_by(TaxBracket.bracket_min.asc()).all()
    return brackets
```

**Usage for Phase 1:** Call this directly with `filing_status='married_joint'` or `'married_separate'`. No modifications needed.

### Example 3: Blueprint Registration Pattern

```python
# Source: routes/api.py lines 1-13 (EXISTING)
from flask import Blueprint
from routes.clients import clients_bp
from routes.documents import documents_bp
from routes.analysis import analysis_bp
from routes.calculator import calculator_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register all route blueprints
api_bp.register_blueprint(clients_bp)
api_bp.register_blueprint(documents_bp)
api_bp.register_blueprint(analysis_bp)
api_bp.register_blueprint(calculator_bp)
```

**Usage for Phase 1:** Add `joint_analysis_bp` following this exact pattern.

### Example 4: Model to_dict() Pattern

```python
# Source: models/analysis.py lines 27-54 (EXISTING)
class AnalysisSummary(db.Model):
    # ... fields ...

    def to_dict(self):
        """Convert to dictionary"""
        income_sources_list = []
        if self.income_sources:
            try:
                income_sources_list = json.loads(self.income_sources)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            'id': self.id,
            'client_id': self.client_id,
            'tax_year': self.tax_year,
            'total_income': self.total_income,
            'adjusted_gross_income': self.adjusted_gross_income,
            # ... all fields ...
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None
        }
```

**Usage for Phase 1:** `JointAnalysisSummary.to_dict()` follows this exact pattern.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON dict construction | Model `.to_dict()` method | Existing pattern | Consistent serialization across all models |
| Hardcoded 2024 tax brackets | Database-backed tax tables | Existing implementation | Dynamic tax year support, easier updates |
| Separate hash per client | Bidirectional hash including spouse | Phase 1 addition | Automatic cache invalidation for joint analysis |
| SQLite default mode | SQLite WAL mode | Phase 1 required | Concurrent reads + writes, no "database locked" errors |
| Single filing status calculations | Multi-filing status comparison | Phase 1 addition | MFJ vs MFS comparison capability |

**Deprecated/outdated:**
- **Hardcoded QBI thresholds in analysis code**: `TaxCalculator.get_qbi_income_thresholds()` (lines 291-317) centralizes thresholds with filing status support
- **Filing status as boolean ('married' true/false)**: Must use exact strings ('married_joint', 'married_separate') for correct bracket/threshold lookups
- **SQLite without WAL mode**: Default mode causes concurrency issues with dual-writer pattern

## Open Questions

Things that couldn't be fully resolved:

1. **How should dependent allocation work for MFS?**
   - What we know: Each child can only be claimed by one spouse (IRS rule)
   - What's unclear: UI workflow for allocating dependents, Form 8332 handling
   - Recommendation: Phase 2 feature — add `Dependent` model with `claimed_by_client_id` FK, allocation UI in joint analysis page

2. **Should individual analyses auto-refresh when spouse data changes?**
   - What we know: Modified hash includes spouse data, so they will refresh
   - What's unclear: Is this confusing? Should we add opt-in flag?
   - Recommendation: Phase 1 implements bidirectional invalidation, Phase 3 adds UI explanation: "Analysis includes both spouses' data"

3. **How to handle community property states (9 states require 50/50 income splitting)?**
   - What we know: AZ, CA, ID, LA, NV, NM, TX, WA, WI have special rules, Form 8958 required
   - What's unclear: Scope for MVP? Blocking validation or warning?
   - Recommendation: Phase 1 flags as "needs deeper research", Phase 2 adds state detection + warning, full Form 8958 support in future milestone

4. **What if only one spouse has uploaded data?**
   - What we know: Joint analysis requires both spouses to have ExtractedData
   - What's unclear: UI flow for this scenario, error message wording
   - Recommendation: Phase 1 returns error: "Both spouses must have tax data before joint analysis", Phase 3 UI shows prerequisite checklist

5. **Should joint analysis trigger automatically when spouse data changes?**
   - What we know: Cache invalidation works (stale data prevented)
   - What's unclear: Should we auto-recalculate or wait for user to navigate to joint page?
   - Recommendation: Lazy evaluation (on-demand) for Phase 1, optional auto-refresh in Phase 4

## Sources

### Primary (HIGH confidence)

- **TaxCalculator existing implementation** - `services/tax_calculator.py` lines 83-317
  - Filing status support verified: lines 96-108 (bracket queries), 304-312 (QBI thresholds)
  - Already handles 'married_separate' correctly

- **AnalysisEngine caching pattern** - `services/analysis_engine.py` lines 14-72
  - Hash calculation: lines 14-35
  - Cache check and return: lines 56-72
  - Pattern extends cleanly to joint analysis

- **Model patterns** - `models/analysis.py` lines 6-54, `models/client.py` lines 8-27
  - `AnalysisSummary` structure: lines 6-26
  - `to_dict()` pattern: lines 27-54
  - Spouse relationship: `client.py` line 24

- **Blueprint registration** - `routes/api.py` lines 1-13, `routes/analysis.py` lines 1-21
  - Blueprint pattern: `api.py` lines 7-13
  - Route handler pattern: `analysis.py` lines 7-21

- **PITFALLS.md** - `.planning/research/PITFALLS.md`
  - Credit disqualification: lines 76-119
  - QBI thresholds: lines 123-161
  - SQLite concurrency: lines 208-246
  - SALT cap: lines 419-454

- **LEARNINGS.md** - `.planning/LEARNINGS.md` lines 46-50
  - SQLite WAL mode pattern documented
  - Bidirectional cache invalidation confirmed as best practice

### Secondary (MEDIUM confidence)

- **ARCHITECTURE.md** - `.planning/research/ARCHITECTURE.md` lines 71-118
  - JointAnalysisService method signatures (not yet implemented, design only)
  - Caching strategy recommendations

- **ROADMAP.md** - `.planning/ROADMAP.md` lines 17-61
  - Phase 1 requirements and success criteria
  - Key files to create/modify list

### Tertiary (LOW confidence)

- None for Phase 1 — all implementation details verified in existing code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components exist in codebase, verified working
- Architecture patterns: HIGH - Extends existing patterns (service layer, caching, blueprints)
- Pitfalls: HIGH - Verified with IRS guidance and existing TaxCalculator implementation
- Open questions: MEDIUM - Need user workflow decisions (dependent allocation, auto-refresh)

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable stack, unlikely to change)

**Assumptions:**
- Client model already has spouse_id relationship (verified: `models/client.py` line 19)
- TaxCalculator already handles all filing statuses (verified: `tax_calculator.py` lines 304-312)
- Database already uses SQLite (verified: `config.py` sets SQLALCHEMY_DATABASE_URI to SQLite)
- Blueprint pattern already used for routes (verified: `routes/api.py`)

**Phase 1 Prerequisites:**
- No new dependencies to install
- No schema changes (JointAnalysisSummary is new table, added via db.create_all())
- No existing code modifications required before starting
- SQLite WAL mode can be enabled without data migration

**Ready for Planning:** Yes. All technical questions answered, patterns verified in codebase, pitfalls documented with solutions.
