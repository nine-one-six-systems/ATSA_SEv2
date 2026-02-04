# Architecture Patterns for Dual-Filer Tax Analysis

**Domain:** Tax Analysis Platform (Flask MVC)
**Researched:** 2026-02-04
**Confidence:** HIGH

## Recommended Architecture

The dual-filer feature extends the existing Flask MVC architecture by adding a **Joint Analysis Service** that aggregates two individual client analyses into a unified MFJ vs MFS comparison. The architecture preserves the existing single-filer flow while adding a parallel joint analysis pathway.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation Layer                    │
│  ┌────────────────────┐        ┌────────────────────────┐  │
│  │  Single Analysis   │        │  Joint Analysis View   │  │
│  │  View (existing)   │        │  (NEW - split-screen) │  │
│  └────────────────────┘        └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                         Route Layer                          │
│  ┌────────────────────┐        ┌────────────────────────┐  │
│  │ /analysis/client/  │        │ /analysis/joint/       │  │
│  │ <id> (existing)    │        │ <spouse1>/<spouse2>    │  │
│  │                    │        │ (NEW)                  │  │
│  └────────────────────┘        └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        Service Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          AnalysisEngine (existing)                     │ │
│  │          - analyze_client(client_id)                   │ │
│  │          - Returns: (strategies, summary)              │ │
│  │          - Uses: data_version_hash for caching         │ │
│  └────────────────────────────────────────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         JointAnalysisService (NEW)                     │ │
│  │         - analyze_joint(spouse1_id, spouse2_id)        │ │
│  │         - calculate_mfj_vs_mfs_comparison()            │ │
│  │         - Uses: TaxCalculator for joint brackets       │ │
│  └────────────────────────────────────────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          TaxCalculator (existing)                      │ │
│  │          - Already supports married_joint brackets     │ │
│  │          - Already supports married_separate brackets  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                         Model Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ Client (exists)  │  │ AnalysisResult   │  │ Analysis  │ │
│  │ - spouse_id FK   │  │ (existing)       │  │ Summary   │ │
│  │ - bidirectional  │  │                  │  │ (existing)│ │
│  └──────────────────┘  └──────────────────┘  └───────────┘ │
│           │                                                  │
│           └──> spouse relationship (existing)               │
└─────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### 1. JointAnalysisService (NEW Service Layer Component)

**Responsibility:** Orchestrates dual-filer analysis by coordinating individual analyses and joint calculations.

**Communicates With:**
- `AnalysisEngine` - to trigger individual client analyses
- `TaxCalculator` - to calculate MFJ and MFS scenarios
- `Client` model - to retrieve spouse data
- `AnalysisResult` and `AnalysisSummary` models - to aggregate individual results

**Key Methods:**
```python
class JointAnalysisService:
    @staticmethod
    def analyze_joint(spouse1_id, spouse2_id, force_refresh=False):
        """
        Analyze both spouses individually, then calculate joint scenarios.

        Returns: {
            'spouse1': {...individual analysis...},
            'spouse2': {...individual analysis...},
            'joint_mfj': {...married filing jointly...},
            'joint_mfs': {...married filing separately...},
            'comparison': {
                'recommended_status': 'MFJ' or 'MFS',
                'savings': amount,
                'reasons': [...]
            }
        }
        """

    @staticmethod
    def calculate_mfj_scenario(spouse1_summary, spouse2_summary):
        """Combine incomes through married_joint brackets"""

    @staticmethod
    def calculate_mfs_scenario(spouse1_summary, spouse2_summary):
        """Separate incomes through married_separate brackets"""

    @staticmethod
    def _calculate_joint_data_version_hash(spouse1_id, spouse2_id):
        """
        Calculate hash from both spouses' data timestamps.
        Used for caching joint analysis results.
        """
```

**Caching Strategy:**
- Joint analysis caching combines both spouses' `data_version_hash`
- Hash calculation: `sha256(spouse1_hash + '|' + spouse2_hash + '|' + filing_status)`
- Cache invalidation: when either spouse's data changes (upload/edit)
- Stored in new `JointAnalysisSummary` model (similar structure to `AnalysisSummary`)

### 2. TaxCalculator (Existing - No Changes Required)

**Current Capabilities:**
- Already supports `married_joint` filing status with appropriate brackets
- Already supports `married_separate` filing status with appropriate brackets
- Handles bracket lookups from `TaxBracket` model filtered by `filing_status`
- Handles standard deduction lookups from `StandardDeduction` model

**Usage in Joint Analysis:**
```python
# MFJ scenario
combined_income = spouse1_income + spouse2_income
mfj_result = TaxCalculator.calculate_federal_tax(
    income=combined_income,
    filing_status='married_joint',
    dependents=total_dependents,
    tax_year=tax_year
)

# MFS scenario
mfs_spouse1 = TaxCalculator.calculate_federal_tax(
    income=spouse1_income,
    filing_status='married_separate',
    dependents=spouse1_dependents,
    tax_year=tax_year
)
mfs_spouse2 = TaxCalculator.calculate_federal_tax(
    income=spouse2_income,
    filing_status='married_separate',
    dependents=spouse2_dependents,
    tax_year=tax_year
)
```

### 3. Split-Screen UI Component (NEW Frontend Component)

**Responsibility:** Display side-by-side comparison of spouses' individual analyses with joint calculation below.

**Structure:**
```html
<div class="joint-analysis-view">
    <!-- Header with client names and filing status comparison -->
    <div class="joint-header">
        <h2>Joint Analysis: [Spouse1] & [Spouse2]</h2>
    </div>

    <!-- Split-screen individual analyses -->
    <div class="split-screen-container">
        <div class="spouse-panel spouse-left">
            <h3>[Spouse1 Name]</h3>
            <!-- Individual summary (reuse existing summary-grid component) -->
            <div class="summary-grid">...</div>
            <!-- Individual strategies (reuse existing strategy-card) -->
            <div class="strategies-section">...</div>
        </div>

        <div class="spouse-panel spouse-right">
            <h3>[Spouse2 Name]</h3>
            <!-- Individual summary (reuse existing summary-grid component) -->
            <div class="summary-grid">...</div>
            <!-- Individual strategies (reuse existing strategy-card) -->
            <div class="strategies-section">...</div>
        </div>
    </div>

    <!-- Joint analysis section below split-screen -->
    <div class="joint-analysis-section">
        <h3>Filing Status Comparison</h3>

        <!-- MFJ vs MFS comparison cards -->
        <div class="filing-status-comparison">
            <div class="filing-option mfj">
                <h4>Married Filing Jointly (MFJ)</h4>
                <div class="tax-summary">
                    <div class="metric">Combined Income: $X</div>
                    <div class="metric">Total Tax: $Y</div>
                    <div class="metric">Effective Rate: Z%</div>
                </div>
            </div>

            <div class="filing-option mfs">
                <h4>Married Filing Separately (MFS)</h4>
                <div class="tax-summary">
                    <div class="metric">Combined Tax: $Y</div>
                    <div class="metric">Difference: +$X (more than MFJ)</div>
                </div>
            </div>
        </div>

        <!-- Recommendation -->
        <div class="recommendation-card">
            <strong>Recommendation:</strong> File as [MFJ/MFS]
            <div class="savings">Saves $X compared to [alternative]</div>
            <ul class="reasons">
                <li>[Reason 1]</li>
                <li>[Reason 2]</li>
            </ul>
        </div>

        <!-- Joint optimization strategies -->
        <div class="joint-strategies-section">
            <h4>Joint Optimization Strategies</h4>
            <!-- Strategies that apply to the couple, not individuals -->
        </div>
    </div>
</div>
```

**CSS Considerations:**
- Split-screen uses CSS Grid or Flexbox with `grid-template-columns: 1fr 1fr`
- Responsive breakpoint at tablet size: stack vertically below 768px
- Shared component styles: reuse existing `.summary-card`, `.strategy-card` classes
- Visual separator: vertical divider line between spouse panels
- Sticky header: joint-header remains visible during scroll

**JavaScript Data Flow:**
```javascript
// Joint analysis page
async function loadJointAnalysis(spouse1_id, spouse2_id) {
    // Fetch joint analysis data
    const response = await fetch(`/api/analysis/joint/${spouse1_id}/${spouse2_id}`);
    const data = await response.json();

    // Render split-screen
    renderSpousePanel('left', data.spouse1);
    renderSpousePanel('right', data.spouse2);

    // Render joint comparison
    renderFilingComparison(data.joint_mfj, data.joint_mfs, data.comparison);
}
```

### 4. Route Layer Extensions (NEW Routes)

**New Blueprint:** `/api/analysis/joint/...`

```python
# routes/joint_analysis.py (NEW FILE)
from flask import Blueprint, jsonify
from services.joint_analysis_service import JointAnalysisService

joint_analysis_bp = Blueprint('joint_analysis', __name__)

@joint_analysis_bp.route('/analysis/joint/<int:spouse1_id>/<int:spouse2_id>', methods=['GET'])
def get_joint_analysis(spouse1_id, spouse2_id):
    """Get cached joint analysis or trigger if not exists"""
    result = JointAnalysisService.analyze_joint(spouse1_id, spouse2_id)
    return jsonify(result)

@joint_analysis_bp.route('/analysis/joint/<int:spouse1_id>/<int:spouse2_id>/refresh', methods=['POST'])
def refresh_joint_analysis(spouse1_id, spouse2_id):
    """Force refresh joint analysis"""
    result = JointAnalysisService.analyze_joint(spouse1_id, spouse2_id, force_refresh=True)
    return jsonify(result)
```

**Template Route:**
```python
# app.py (add route)
@app.route('/joint-analysis.html')
def joint_analysis():
    return render_template('joint_analysis.html')
```

### 5. Model Layer Extensions

**New Model: JointAnalysisSummary**

```python
# models/joint_analysis.py (NEW FILE)
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
    mfs_combined_tax = db.Column(db.Float, default=0)
    mfs_effective_rate = db.Column(db.Float, default=0)

    # Comparison
    recommended_status = db.Column(db.String(20))  # 'MFJ' or 'MFS'
    savings_amount = db.Column(db.Float, default=0)

    # Caching
    data_version_hash = db.Column(db.String(64))  # Combined hash
    last_analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure only one joint analysis per spouse pair
    __table_args__ = (
        db.UniqueConstraint('spouse1_id', 'spouse2_id', name='unique_spouse_pair'),
    )
```

**Existing Model: Client (No Changes)**
- Already has `spouse_id` foreign key
- Already has bidirectional relationship via `spouse` and `linked_spouse`
- Joint analysis service uses these relationships to navigate between spouses

## Data Flow

### Flow 1: Individual Analysis (Existing - Unchanged)

```
User Action → Route → AnalysisEngine → TaxCalculator → Models
                         │                    │
                         └──── ExtractedData ─┘
                         │
                         └──── AnalysisSummary (cached with data_version_hash)
```

1. User clicks "Run Analysis" for a client
2. `POST /api/analysis/analyze/<client_id>`
3. `AnalysisEngine.analyze_client(client_id)`
4. Calculate `data_version_hash` from ExtractedData timestamps
5. Check cache: if hash matches existing AnalysisSummary, return cached
6. If no cache or force_refresh: run full analysis
7. Store results in AnalysisResult and AnalysisSummary tables
8. Return strategies and summary to frontend

### Flow 2: Joint Analysis (NEW)

```
User Action → Joint Route → JointAnalysisService
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              AnalysisEngine  AnalysisEngine  TaxCalculator
              (spouse 1)      (spouse 2)      (MFJ/MFS)
                    │             │             │
                    └─────────────┴─────────────┘
                                  │
                                  ▼
                          JointAnalysisSummary (cached)
                                  │
                                  ▼
                              Frontend
```

**Step-by-step:**

1. **User navigates to joint analysis page**
   - URL: `/joint-analysis.html?spouse1=X&spouse2=Y`
   - Frontend: `loadJointAnalysis(spouse1_id, spouse2_id)`

2. **Frontend requests joint analysis**
   - `GET /api/analysis/joint/<spouse1_id>/<spouse2_id>`

3. **JointAnalysisService orchestrates**
   ```python
   def analyze_joint(spouse1_id, spouse2_id, force_refresh=False):
       # Step 3a: Calculate joint data version hash
       joint_hash = _calculate_joint_data_version_hash(spouse1_id, spouse2_id)

       # Step 3b: Check cache
       existing = JointAnalysisSummary.query.filter_by(
           spouse1_id=spouse1_id,
           spouse2_id=spouse2_id
       ).first()

       if existing and existing.data_version_hash == joint_hash and not force_refresh:
           return _format_cached_result(existing)

       # Step 3c: Analyze each spouse individually (uses AnalysisEngine)
       spouse1_strategies, spouse1_summary = AnalysisEngine.analyze_client(spouse1_id)
       spouse2_strategies, spouse2_summary = AnalysisEngine.analyze_client(spouse2_id)

       # Step 3d: Calculate MFJ scenario
       mfj_result = calculate_mfj_scenario(spouse1_summary, spouse2_summary)

       # Step 3e: Calculate MFS scenario
       mfs_result = calculate_mfs_scenario(spouse1_summary, spouse2_summary)

       # Step 3f: Compare and recommend
       comparison = compare_filing_statuses(mfj_result, mfs_result)

       # Step 3g: Generate joint optimization strategies
       joint_strategies = generate_joint_strategies(
           spouse1_summary, spouse2_summary, mfj_result
       )

       # Step 3h: Store in cache
       save_joint_analysis_summary(joint_hash, mfj_result, mfs_result, comparison)

       # Step 3i: Return composite result
       return {
           'spouse1': {'summary': spouse1_summary, 'strategies': spouse1_strategies},
           'spouse2': {'summary': spouse2_summary, 'strategies': spouse2_strategies},
           'joint_mfj': mfj_result,
           'joint_mfs': mfs_result,
           'comparison': comparison,
           'joint_strategies': joint_strategies
       }
   ```

4. **Frontend renders split-screen**
   - Left panel: spouse1 individual analysis (reuse existing components)
   - Right panel: spouse2 individual analysis (reuse existing components)
   - Below: joint comparison section (new component)

### Flow 3: Cache Invalidation

**Trigger: Either spouse's data changes**

```
Document Upload/Edit → ExtractedData updated → data_version_hash changes
                                                       │
                                                       ▼
                                        Next individual analysis: recalculates
                                                       │
                                                       ▼
                                        Next joint analysis: detects hash mismatch
                                                       │
                                                       ▼
                                        JointAnalysisService re-runs analysis
```

**Implementation:**
```python
def _calculate_joint_data_version_hash(spouse1_id, spouse2_id):
    """
    Calculate joint hash from both spouses' individual hashes.
    If either spouse's data changes, joint hash changes.
    """
    spouse1_hash = AnalysisEngine._calculate_data_version_hash(spouse1_id)
    spouse2_hash = AnalysisEngine._calculate_data_version_hash(spouse2_id)

    # Combine hashes in consistent order (lower ID first for symmetry)
    ordered_ids = sorted([spouse1_id, spouse2_id])
    combined_string = f"{spouse1_hash}|{spouse2_hash}|{ordered_ids[0]}|{ordered_ids[1]}"

    return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
```

## Build Order and Dependencies

### Phase 1: Service Layer Foundation
**Build first because**: Core logic must exist before routes and UI can consume it.

1. **Create JointAnalysisService**
   - `services/joint_analysis_service.py`
   - Methods: `analyze_joint()`, `calculate_mfj_scenario()`, `calculate_mfs_scenario()`
   - Depends on: `AnalysisEngine` (existing), `TaxCalculator` (existing)

2. **Create JointAnalysisSummary model**
   - `models/joint_analysis.py`
   - Migration: add `joint_analysis_summaries` table
   - Depends on: `Client` model (existing via foreign keys)

3. **Add joint strategies generation**
   - Extend `TaxStrategiesService` or create `JointStrategiesService`
   - Examples: income splitting, retirement contribution allocation, dependent allocation
   - Depends on: Both spouses' data

**Testing checkpoint:** Unit tests for JointAnalysisService with mock data.

### Phase 2: API Layer
**Build second because**: Frontend needs API endpoints to fetch data.

4. **Create joint_analysis route blueprint**
   - `routes/joint_analysis.py`
   - Routes: `GET /api/analysis/joint/<id1>/<id2>`, `POST .../refresh`
   - Depends on: JointAnalysisService (Phase 1)

5. **Register blueprint in app.py**
   - `app.register_blueprint(joint_analysis_bp)`

**Testing checkpoint:** Integration tests for API endpoints with test database.

### Phase 3: UI Layer
**Build third because**: UI consumes API and displays results.

6. **Create split-screen template**
   - `templates/joint_analysis.html`
   - Structure: header + split-screen container + joint section
   - Reuses: existing CSS classes from `static/css/style.css`

7. **Create joint analysis JavaScript**
   - `static/js/joint_analysis.js`
   - Functions: `loadJointAnalysis()`, `renderSpousePanel()`, `renderFilingComparison()`
   - Reuses: existing functions from `analysis.js` (e.g., `renderStrategyCard()`)

8. **Add split-screen CSS**
   - Extend `static/css/style.css` with `.split-screen-container`, `.spouse-panel`
   - Media queries for responsive stacking

9. **Add navigation entry point**
   - Update client list UI: "View Joint Analysis" link when client has spouse
   - Link format: `/joint-analysis.html?spouse1=X&spouse2=Y`

**Testing checkpoint:** Manual UI testing with two linked clients.

### Phase 4: Workflows and Polish
**Build last because**: These refine the user experience.

10. **Spouse linking workflow enhancement**
    - Client edit form: improved spouse selection dropdown
    - Validation: prevent self-linking, enforce bidirectional link consistency

11. **Data entry improvements**
    - Bulk upload: support uploading documents for both spouses in one session
    - Manual entry: quick-switch between spouses

12. **Joint analysis refresh UX**
    - Auto-refresh indicator when either spouse's data changes
    - "Recalculate" button with timestamp of last analysis

## Architecture Anti-Patterns to Avoid

### Anti-Pattern 1: Denormalizing Spouse Data
**What:** Storing spouse1's data redundantly in spouse2's record or vice versa.
**Why bad:** Data duplication leads to inconsistency when one spouse's data updates.
**Instead:** Use foreign key relationship (`spouse_id`) and query both records when needed. JointAnalysisService fetches both clients at runtime.

### Anti-Pattern 2: Global Filing Status on Client Model
**What:** Adding `joint_filing_status` field to Client model that applies to both spouses.
**Why bad:** Creates ambiguity (which spouse's record is source of truth?) and violates single responsibility.
**Instead:** Filing status is determined per-analysis. JointAnalysisSummary stores the recommended status for a specific analysis run.

### Anti-Pattern 3: Inline Joint Calculation in Routes
**What:** Putting MFJ/MFS calculation logic directly in route handlers.
**Why bad:** Violates separation of concerns, makes testing difficult, prevents code reuse.
**Instead:** Service layer pattern - routes delegate to JointAnalysisService which orchestrates all calculations.

### Anti-Pattern 4: Single Mega-Component for Split-Screen
**What:** Building split-screen UI as one monolithic JavaScript function.
**Why bad:** Not reusable, difficult to maintain, couples individual and joint rendering.
**Instead:** Reuse existing components (`renderStrategyCard()`, summary display) and compose them in split-screen layout.

### Anti-Pattern 5: Eager Loading All Joint Analyses
**What:** Pre-calculating joint analyses for all spouse pairs on every data change.
**Why bad:** Expensive computation for data that may never be viewed.
**Instead:** Lazy evaluation - joint analysis runs on-demand when user navigates to joint analysis page. Cache with `data_version_hash` prevents redundant calculations.

### Anti-Pattern 6: Client-Side Tax Calculation
**What:** Calculating MFJ/MFS tax amounts in JavaScript from individual summaries.
**Why bad:** Tax bracket logic is complex, error-prone, and already exists in TaxCalculator.
**Instead:** Server-side calculation in JointAnalysisService using TaxCalculator. Frontend only displays results.

## Scalability Considerations

| Concern | Current (Single-Filer) | With Dual-Filer | At Scale (1000+ couples) |
|---------|------------------------|-----------------|--------------------------|
| **Database queries** | 1 query per client analysis | 2 individual + 1 joint query | Add database indexes on spouse_id, consider read replicas |
| **Cache size** | 1 AnalysisSummary per client | +1 JointAnalysisSummary per couple | Monitor storage, implement cache expiration (e.g., 30 days) |
| **Cache invalidation** | Single hash per client | Combined hash for couple | Batch invalidation: queue-based processing for couples when data changes |
| **Computation time** | ~500ms per analysis | ~1200ms (2 individual + joint) | Add background job processing (Celery/RQ) for joint analyses |
| **UI rendering** | Single panel | Split-screen (2 panels + joint) | Consider pagination for strategies, lazy-load joint section |

**Optimization Strategies:**
1. **Parallel execution:** Run spouse1 and spouse2 analyses concurrently (Python asyncio or multiprocessing)
2. **Selective refresh:** Only re-run analysis for spouse whose data changed, reuse cached result for other spouse
3. **Progressive rendering:** Load individual panels first, then fetch and render joint section
4. **Database indexes:** Add indexes on `(spouse1_id, spouse2_id)` in JointAnalysisSummary for fast lookups

## Technology Stack Compatibility

All dual-filer components use existing stack patterns:

| Component | Technology | Pattern | Notes |
|-----------|-----------|---------|-------|
| **Service Layer** | Python (Flask) | Service class with static methods | Matches AnalysisEngine pattern |
| **Model Layer** | SQLAlchemy | Declarative models with relationships | Matches existing Client/Analysis models |
| **Route Layer** | Flask Blueprint | RESTful API endpoints | Matches existing analysis_bp pattern |
| **Frontend** | Vanilla JavaScript + Fetch API | Async/await pattern | Matches existing analysis.js pattern |
| **Templating** | Jinja2 | Server-side rendering for page structure | Matches existing templates |
| **Styling** | Vanilla CSS | Component-based classes | Extends existing style.css |
| **Caching** | Database-backed (SQLite) | Hash-based versioning | Extends existing data_version_hash pattern |

**No new dependencies required.** All components built with existing Flask, SQLAlchemy, and vanilla JS stack.

## Sources and Confidence

**HIGH confidence areas:**
- Flask service layer pattern: verified with [Cosmic Python architecture patterns](https://www.cosmicpython.com/book/chapter_04_service_layer.html)
- Tax bracket handling: existing TaxCalculator already implements married_joint and married_separate (verified in codebase)
- Data versioning: existing AnalysisEngine uses SHA-256 hash of timestamps (verified in code)

**MEDIUM confidence areas:**
- Split-screen UI pattern: general web design pattern, but [specific implementation](https://fireart.studio/blog/4-ways-to-design-a-perfect-split-screen-homepage/) may require iteration based on UX testing

**LOW confidence areas:**
- Performance at scale (1000+ couples): requires load testing to validate optimization strategies

**Verification recommendations:**
- Unit test JointAnalysisService with sample spouse data before UI development
- Integration test API endpoints with database to verify hash-based caching
- UX test split-screen layout on multiple screen sizes (desktop, tablet, mobile)

---

**Architecture complete. Ready for roadmap creation.**

This architecture preserves existing patterns, minimizes changes to working code, and provides clear build dependencies for phased implementation.
