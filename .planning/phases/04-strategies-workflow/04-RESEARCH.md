# Phase 4: Dual-Filer Strategies and Workflow - Research

**Researched:** 2026-02-04
**Domain:** Tax strategy personalization, spouse linking workflow, document attribution
**Confidence:** HIGH

## Summary

Phase 4 builds on the existing `TaxStrategiesService` (10 strategies) and `JointAnalysisService` (MFJ/MFS comparison) to deliver **per-spouse strategy recommendations**, **joint-only optimization strategies**, and **a complete end-to-end workflow** for dual filers. The research reveals that the existing strategy service already analyzes by income type but lacks filing status awareness and spouse-specific context. The linking workflow exists at the API level but lacks a smooth UI flow. Document upload has no spouse attribution mechanism.

The key insight is that **income type determines individual strategy eligibility** (LLC owner gets SEP-IRA/QBI, W-2 employee gets 401k/HSA) while **filing status determines joint strategy availability** (Spousal IRA, EITC, education credits require MFJ). The service layer already filters MFS-ineligible credits; Phase 4 extends this to show "why" and recommend alternatives.

**Primary recommendation:** Extend `TaxStrategiesService` with income-type-aware recommendations per spouse, add a new `JointStrategyService` for MFJ-only optimizations, enhance the linking workflow UI, and add document attribution to the upload flow.

## Current System Analysis

### TaxStrategiesService (services/tax_strategies.py)

**What exists:**
- 10 strategies analyzed: QBI, Section 179, Bonus Depreciation, R&D, Retirement, SE Tax, SE Health Insurance, Home Office, QSBS, FMLA Credit
- Strategy status: FULLY_UTILIZED, PARTIALLY_UTILIZED, NOT_UTILIZED, NOT_APPLICABLE, etc.
- Returns `AnalysisResult` objects with recommendations, flags, potential savings
- Takes `data_by_form` (extracted tax data) and `client` (Client model)

**What's missing:**
- No filtering by income type (doesn't distinguish LLC owner from W-2 employee)
- No spouse-specific recommendations
- No filing status-specific recommendations (all strategies shown regardless of MFJ/MFS)
- No joint optimization strategies (Spousal IRA, bracket utilization)

**Integration point:** `analyze_all_strategies(data_by_form, client)` line 48-92

### JointAnalysisService (services/joint_analysis_service.py)

**What exists:**
- REQ-05 credit eligibility filtering (lines 53-80, 120-147)
- CREDIT_ELIGIBILITY matrix for EITC, student loan, education credits, adoption credit
- `_filter_strategies_by_filing_status()` removes MFS-ineligible strategies
- Returns filtered strategies + list of removed credit names
- Joint analysis returns spouse1/spouse2 strategies via `AnalysisEngine.analyze_client()`

**What's missing:**
- No "why" explanation for removed strategies (just removed silently)
- No feasibility warning on individual strategy view
- No joint-only strategies (Spousal IRA, bracket utilization not generated)
- Filtering happens only in joint context, not when viewing individual analysis

**Integration point:** Lines 538-545 filter strategies for MFS, line 663 returns strategies

### Client Model (models/client.py)

**What exists:**
- `spouse_id` FK for linking (line 20)
- `filing_status` field (line 15)
- `deduction_method` field (line 16)
- Bidirectional relationship via `spouse` (line 25)

**What's missing:**
- No primary income type field (would need to derive from extracted data)

### Document Model (models/document.py)

**What exists:**
- `client_id` FK (line 8)
- `filename`, `file_path`, `file_type`, `tax_year`, `ocr_status`

**What's missing:**
- No `attribution` field (taxpayer/spouse/joint)
- No way to tag document as belonging to specific spouse in dual-filer context

### ExtractedData Model (models/extracted_data.py)

**What exists:**
- `document_id`, `client_id`, `form_type`, `field_name`, `field_value`
- Generic structure can store any field

**What's missing:**
- No attribution tracking (which spouse does this data belong to?)

**Note from LEARNINGS.md:** Phase 1 research identified that ExtractedData can use naming convention (`field_name='wages:taxpayer'`) for attribution without schema changes. Alternative: add `attribution` column.

### Spouse Linking (routes/clients.py)

**What exists:**
- `/clients/<id>/link-spouse` POST endpoint (lines 87-110)
- Links bidirectionally (client.spouse_id = spouse_id, spouse.spouse_id = client_id)
- Returns both client and spouse in response

**What's missing:**
- No validation that both spouses have compatible filing statuses
- No workflow to create both spouses in one flow
- No redirect to joint analysis after linking

### Upload UI (templates/upload.html, static/js/upload.js)

**What exists:**
- Client selector dropdown
- Tax year input
- Drag-and-drop file upload
- Document processing trigger

**What's missing:**
- No spouse attribution selector (Taxpayer/Spouse toggle)
- No indication of spouse context when client has `spouse_id`
- No workflow to upload documents for both spouses in sequence

### Joint Analysis UI (templates/joint_analysis.html, static/js/joint_analysis.js)

**What exists:**
- Split-screen layout with Split.js
- Spouse selector dropdowns (filtered to linked clients only)
- Per-spouse income breakdown panel
- MFJ vs MFS comparison cards and table
- Strategy display from individual analysis

**What's missing:**
- No per-spouse strategy recommendations section in panels
- No joint-only strategies section in comparison area
- No feasibility warnings on strategies
- No "Go to Upload" flow when data missing

## Gaps to Fill

### REQ-21: Per-Spouse Tax Strategies

**Gap:** Strategies are generated generically, not tailored to income type.

**Solution:** Create income type detection logic and strategy relevance mapping.

| Income Type | Detected By | Relevant Strategies |
|-------------|-------------|---------------------|
| Self-employed (LLC/Schedule C) | Schedule C present | SEP-IRA, Solo 401(k), QBI, SE Tax Deduction, SE Health Insurance, Home Office |
| W-2 Employee | W-2 present | 401(k) maximization, HSA, FSA, Backdoor Roth |
| Rental/Real Estate | Schedule E present | Depreciation, Section 179, 1031 exchange |
| Business Owner (K-1) | K-1 present | QBI, retirement plan structuring |
| Capital Gains | Schedule D present | QSBS, tax-loss harvesting |

**Implementation pattern:**
```python
def get_income_types(data_by_form):
    """Detect income types from extracted data"""
    income_types = []
    if 'Schedule C' in data_by_form:
        income_types.append('self_employed')
    if 'W-2' in data_by_form:
        income_types.append('w2_employee')
    if 'Schedule E' in data_by_form:
        income_types.append('rental_income')
    if 'K-1' in data_by_form:
        income_types.append('business_owner')
    return income_types
```

### REQ-22: Joint Optimization Strategies

**Gap:** No MFJ-only strategies generated.

**Solution:** Create `JointStrategyService` that generates joint-specific recommendations.

| Strategy | Availability | Benefit |
|----------|--------------|---------|
| Spousal IRA | MFJ only | Non-working spouse can contribute up to $7,500 (2026) |
| Bracket Utilization | MFJ preferred | Wider brackets keep more income in lower tiers |
| EITC | MFJ only (usually) | Up to $8,046 (2026) for qualifying families |
| Education Credits | MFJ only | AOTC up to $2,500, LLC up to $2,000 |
| Student Loan Interest | MFJ only | Up to $2,500 deduction |
| Adoption Credit | MFJ only | Up to $16,810 (2026) |

**Spousal IRA eligibility logic:**
```python
def check_spousal_ira_eligibility(spouse1_income, spouse2_income, filing_status):
    """
    Spousal IRA requires MFJ and one spouse with low/no earned income
    while combined income supports contribution
    """
    if filing_status != 'married_joint':
        return {'eligible': False, 'reason': 'Requires MFJ filing status'}

    combined = spouse1_income + spouse2_income
    limit_2026 = 7500  # $8,600 if age 50+

    # Non-working spouse can contribute if working spouse has sufficient income
    if spouse2_income < limit_2026 and spouse1_income >= limit_2026:
        return {
            'eligible': True,
            'beneficiary': 'spouse2',
            'max_contribution': min(limit_2026, combined - spouse1_ira_contribution)
        }
    return {'eligible': False, 'reason': 'Both spouses have sufficient earned income'}
```

**Bracket utilization detection:**
```python
def calculate_bracket_utilization_benefit(mfj_result, mfs_result):
    """
    Compare effective rates to show bracket benefit
    """
    mfj_effective = mfj_result['effective_rate']
    mfs_effective_combined = (mfs_result['spouse1']['total_tax'] + mfs_result['spouse2']['total_tax']) / mfj_result['combined_income'] * 100

    if mfj_effective < mfs_effective_combined:
        return {
            'strategy': 'Bracket Utilization',
            'benefit': f"MFJ saves {mfs_effective_combined - mfj_effective:.2f}% effective rate",
            'requires': 'MFJ'
        }
```

### REQ-23: Strategy Feasibility Flags

**Gap:** Strategies shown without filing status context.

**Solution:** Add `filing_status_requirements` to each strategy and display warnings.

**Feasibility model:**
```python
STRATEGY_FILING_REQUIREMENTS = {
    'spousal_ira': {'requires': 'married_joint', 'warning': 'Spousal IRA requires filing jointly'},
    'eitc': {'requires': 'married_joint', 'warning': 'EITC unavailable when filing separately'},
    'education_credits': {'requires': 'married_joint', 'warning': 'Education credits unavailable when filing separately'},
    'student_loan_interest': {'requires': 'married_joint', 'warning': 'Student loan interest deduction unavailable when filing separately'},
    'roth_ira_direct': {'mfs_limit': 10000, 'warning': 'Roth IRA MAGI limit is $10,000 for MFS (vs $242,000 MFJ)'},
    # Most strategies have no filing status restriction
    'qbi_deduction': {'requires': None, 'note': 'Available for both MFJ and MFS, but thresholds differ'},
}
```

**UI pattern:** Display warning badge on strategy card when viewing MFS analysis.

### REQ-24: Spouse Linking Workflow

**Gap:** Current flow requires manually entering spouse_id, no guided workflow.

**Current flow:**
1. Create Client A
2. Create Client B
3. Edit Client A, enter Client B's ID in spouse_id field
4. Navigate to Joint Analysis manually

**Target flow:**
1. Click "Create Married Couple" button (new)
2. Form shows fields for both spouses side-by-side
3. On save, both clients created and linked automatically
4. Redirect to joint analysis page with both spouses pre-selected

**Implementation pattern:**
```javascript
// New endpoint: POST /api/clients/create-couple
{
    spouse1: { first_name, last_name, filing_status, ... },
    spouse2: { first_name, last_name, filing_status, ... },
    link: true
}

// Response includes redirect URL
{
    spouse1: { id: 1, ... },
    spouse2: { id: 2, ... },
    joint_analysis_url: '/joint-analysis.html?spouse1_id=1&spouse2_id=2'
}
```

**UI additions:**
- "Create Married Couple" button on clients.html
- New modal with two-column form
- Filing status auto-set to married_joint or married_separate
- Success redirects to joint analysis

### REQ-25: Document Upload Attribution

**Gap:** No way to tag documents as belonging to specific spouse.

**Solution:** Add attribution field to Document model and upload UI.

**Database change:**
```python
class Document(db.Model):
    # ... existing fields ...
    attribution = db.Column(db.Text, default='taxpayer', nullable=False)  # 'taxpayer', 'spouse', 'joint'
```

**Upload UI change:**
```html
<!-- Show only when client has spouse_id -->
<div id="attribution-selector" style="display: none;">
    <label>Document belongs to:</label>
    <select id="document-attribution">
        <option value="taxpayer">Taxpayer (Primary)</option>
        <option value="spouse">Spouse</option>
        <option value="joint">Joint (Both)</option>
    </select>
</div>
```

**Data flow:**
1. User selects client with spouse_id
2. Attribution selector appears
3. User uploads W-2, selects "Spouse"
4. Document saved with attribution='spouse'
5. On process, ExtractedData flows to correct client:
   - If attribution='spouse', client_id = client.spouse_id
   - If attribution='taxpayer', client_id = selected client
   - If attribution='joint', create records for both clients

### REQ-26: Dual Data Entry Support

**Gap:** Upload UI doesn't clearly support manual entry alternative.

**Solution:** Add manual income entry form alongside upload.

**Pattern:** Tab interface or accordion
- Tab 1: Document Upload (existing)
- Tab 2: Manual Entry (new)

**Manual entry form fields:**
```html
<div class="manual-entry-form">
    <h4>W-2 Income</h4>
    <input type="number" id="wages" placeholder="Wages (Box 1)">
    <input type="number" id="federal_withheld" placeholder="Federal Tax Withheld (Box 2)">

    <h4>Self-Employment Income</h4>
    <input type="number" id="schedule_c_income" placeholder="Net Profit (Schedule C Line 31)">

    <h4>Other Income</h4>
    <input type="number" id="interest_income" placeholder="Interest Income">
    <input type="number" id="dividend_income" placeholder="Dividend Income">

    <button onclick="saveManualEntry()">Save Income Data</button>
</div>
```

**Backend:** Create ExtractedData records with form_type='MANUAL_ENTRY'.

## Recommended Implementation Patterns

### Pattern 1: Strategy Relevance by Income Type

**What:** Map income types to relevant strategies for personalized recommendations.

**Implementation:**
```python
INCOME_TYPE_STRATEGIES = {
    'self_employed': [
        'retirement_contributions',  # SEP-IRA, Solo 401(k)
        'qbi_deduction',
        'se_tax_deduction',
        'se_health_insurance',
        'home_office'
    ],
    'w2_employee': [
        'retirement_contributions',  # 401(k) via employer
        'hsa_contributions',  # If HDHP
        'backdoor_roth'  # If high income
    ],
    'business_owner': [
        'qbi_deduction',
        'section_179',
        'bonus_depreciation',
        'rd_deduction',
        'fmla_credit'
    ],
    'rental_income': [
        'section_179',
        'bonus_depreciation'
    ]
}

def filter_strategies_by_income_type(strategies, income_types):
    """Prioritize strategies relevant to detected income types"""
    relevant_strategy_ids = set()
    for income_type in income_types:
        relevant_strategy_ids.update(INCOME_TYPE_STRATEGIES.get(income_type, []))

    # Sort: relevant strategies first, then others
    def sort_key(s):
        info = s.get_detailed_info()
        is_relevant = info.get('strategy_id') in relevant_strategy_ids
        return (0 if is_relevant else 1, s.priority)

    return sorted(strategies, key=sort_key)
```

### Pattern 2: Joint Strategy Generation

**What:** Generate MFJ-only strategies when analyzing joint filing.

**Implementation:**
```python
class JointStrategyService:
    """Service for generating joint-only optimization strategies"""

    JOINT_STRATEGIES = [
        {
            'id': 'spousal_ira',
            'name': 'Spousal IRA Contribution',
            'requires': 'married_joint',
            'check': '_check_spousal_ira'
        },
        {
            'id': 'bracket_utilization',
            'name': 'Bracket Utilization Benefit',
            'requires': 'married_joint',
            'check': '_check_bracket_benefit'
        },
        {
            'id': 'eitc_eligibility',
            'name': 'Earned Income Tax Credit',
            'requires': 'married_joint',
            'check': '_check_eitc'
        }
    ]

    @staticmethod
    def generate_joint_strategies(spouse1_summary, spouse2_summary, joint_result):
        """Generate strategies only available when filing jointly"""
        strategies = []

        for strategy_def in JointStrategyService.JOINT_STRATEGIES:
            check_method = getattr(JointStrategyService, strategy_def['check'])
            result = check_method(spouse1_summary, spouse2_summary, joint_result)

            if result['applicable']:
                strategies.append({
                    'strategy_id': strategy_def['id'],
                    'strategy_name': strategy_def['name'],
                    'requires_filing_status': strategy_def['requires'],
                    'status': result['status'],
                    'potential_benefit': result.get('benefit', 0),
                    'recommendation': result.get('recommendation'),
                    'warning_if_mfs': f"Not available with MFS: {strategy_def['name']}"
                })

        return strategies
```

### Pattern 3: Feasibility Warning Display

**What:** Show warnings when strategy requires different filing status.

**UI implementation:**
```javascript
function renderStrategyWithFeasibility(strategy, currentFilingStatus) {
    const feasibility = STRATEGY_FILING_REQUIREMENTS[strategy.strategy_id];
    let warningHtml = '';

    if (feasibility?.requires && currentFilingStatus !== feasibility.requires) {
        warningHtml = `
            <div class="feasibility-warning">
                <span class="warning-icon">!</span>
                ${feasibility.warning}
            </div>
        `;
    }

    return `
        <div class="strategy-card ${strategy.status}">
            ${warningHtml}
            <h4>${strategy.strategy_name}</h4>
            <div class="strategy-details">
                ${strategy.recommendation}
            </div>
        </div>
    `;
}
```

### Pattern 4: Couple Creation Workflow

**What:** Guided flow to create and link married couple.

**Backend:**
```python
@clients_bp.route('/clients/create-couple', methods=['POST'])
def create_couple():
    """Create both spouse records and link them"""
    data = request.get_json()

    # Validate both spouses provided
    spouse1_data = data.get('spouse1')
    spouse2_data = data.get('spouse2')
    if not spouse1_data or not spouse2_data:
        return jsonify({'error': 'Both spouse1 and spouse2 required'}), 400

    # Create first spouse
    spouse1 = Client(
        first_name=spouse1_data['first_name'],
        last_name=spouse1_data['last_name'],
        filing_status=spouse1_data.get('filing_status', 'married_joint'),
        email=spouse1_data.get('email'),
        phone=spouse1_data.get('phone')
    )
    db.session.add(spouse1)
    db.session.flush()  # Get spouse1.id

    # Create second spouse linked to first
    spouse2 = Client(
        first_name=spouse2_data['first_name'],
        last_name=spouse2_data['last_name'],
        filing_status=spouse2_data.get('filing_status', 'married_joint'),
        email=spouse2_data.get('email'),
        phone=spouse2_data.get('phone'),
        spouse_id=spouse1.id
    )
    db.session.add(spouse2)
    db.session.flush()

    # Link first spouse to second
    spouse1.spouse_id = spouse2.id
    db.session.commit()

    return jsonify({
        'spouse1': spouse1.to_dict(),
        'spouse2': spouse2.to_dict(),
        'joint_analysis_url': f'/joint-analysis.html?spouse1_id={spouse1.id}&spouse2_id={spouse2.id}'
    }), 201
```

### Pattern 5: Document Attribution Flow

**What:** Tag documents to correct spouse during upload.

**Backend enhancement:**
```python
@documents_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    # ... existing validation ...

    attribution = request.form.get('attribution', 'taxpayer')

    # Determine actual client_id based on attribution
    actual_client_id = client_id
    if attribution == 'spouse':
        client = Client.query.get(client_id)
        if client and client.spouse_id:
            actual_client_id = client.spouse_id
        else:
            return jsonify({'error': 'No spouse linked for spouse attribution'}), 400

    document = Document(
        client_id=actual_client_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        tax_year=tax_year,
        attribution=attribution,
        ocr_status='pending'
    )
    # ... rest of upload logic ...
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Income type detection | Custom ML classifier | Form type presence check | W-2 presence = W-2 income, Schedule C presence = self-employment |
| Strategy eligibility | Complex rule engine | Simple dictionary lookup | Eligibility rules are static, lookup is sufficient |
| Tax bracket comparison | Custom bracket calculator | Existing TaxCalculator | Already implemented correctly for all filing statuses |
| Filing status validation | Custom validation logic | JointAnalysisService patterns | Already has credit eligibility validation |

**Key insight:** Most "new" functionality is composing existing services differently, not new calculations.

## Common Pitfalls

### Pitfall 1: Showing MFJ-Only Strategies to MFS Filers

**What goes wrong:** User sees Spousal IRA recommendation while viewing MFS analysis.
**Why it happens:** Strategy generation doesn't check filing status context.
**How to avoid:** Always pass filing_status to strategy generation, filter or warn.
**Warning signs:** Strategy appears without feasibility context.

### Pitfall 2: Attribution Without Spouse Link

**What goes wrong:** User selects "Spouse" attribution but client has no spouse_id.
**Why it happens:** UI shows attribution options before checking spouse link.
**How to avoid:** Only show attribution selector when client.spouse_id exists.
**Warning signs:** Documents uploaded to wrong client.

### Pitfall 3: Joint Strategies Without Both Spouses' Data

**What goes wrong:** Spousal IRA recommendation shown but spouse has no income data.
**Why it happens:** Joint strategy generated before spouse analysis complete.
**How to avoid:** Check both spouses have analysis summaries before generating joint strategies.
**Warning signs:** "$0 benefit" or incomplete recommendations.

### Pitfall 4: Income Type Detection Without Documents

**What goes wrong:** No relevant strategies shown because no forms detected.
**Why it happens:** Income type detection relies on form presence.
**How to avoid:** Fall back to manual entry data, or show generic recommendations.
**Warning signs:** "No applicable strategies" despite known income.

### Pitfall 5: Duplicate Strategy Recommendations

**What goes wrong:** Same strategy appears in individual AND joint section.
**Why it happens:** Individual strategies not deduplicated against joint.
**How to avoid:** Joint strategies should be distinct from individual, OR tag source clearly.
**Warning signs:** "Maximize 401(k)" appears twice.

## Dependency Analysis

### Requirement Dependencies

```
REQ-21 (Per-Spouse Strategies)
  |
  +-- Requires income type detection (from ExtractedData)
  +-- Requires TaxStrategiesService extension
  |
REQ-22 (Joint Strategies)
  |
  +-- Requires JointAnalysisService extension
  +-- Depends on REQ-21 (per-spouse data for joint recommendations)
  |
REQ-23 (Feasibility Flags)
  |
  +-- Requires STRATEGY_FILING_REQUIREMENTS dictionary
  +-- Integrates with REQ-21 and REQ-22 display
  |
REQ-24 (Linking Workflow)
  |
  +-- Standalone UI/API work
  +-- No dependencies on other REQs
  +-- Should complete first (enables testing of others)
  |
REQ-25 (Document Attribution)
  |
  +-- Requires Document model change (add attribution column)
  +-- Requires upload UI enhancement
  +-- Depends on REQ-24 (client must have spouse_id)
  |
REQ-26 (Manual Entry)
  |
  +-- Requires new UI form
  +-- Creates ExtractedData directly
  +-- Independent of REQ-25
```

### Recommended Build Order

1. **Wave 1: Workflow Foundation** (REQ-24)
   - Create couple endpoint
   - UI flow for couple creation
   - Redirect to joint analysis

2. **Wave 2: Data Entry** (REQ-25, REQ-26)
   - Document attribution model + UI
   - Manual entry form + backend

3. **Wave 3: Strategy Enhancement** (REQ-21, REQ-22, REQ-23)
   - Income type detection
   - Per-spouse strategy filtering
   - Joint strategy generation
   - Feasibility warnings

## Code Examples

### Income Type Detection
```python
# Source: Pattern derived from existing TaxStrategiesService form checks

def detect_income_types(client_id):
    """Detect income types from client's extracted data"""
    from models import ExtractedData

    forms = db.session.query(ExtractedData.form_type).filter_by(
        client_id=client_id
    ).distinct().all()
    form_types = {f[0] for f in forms}

    income_types = []

    if 'W-2' in form_types:
        income_types.append('w2_employee')
    if 'Schedule C' in form_types:
        income_types.append('self_employed')
    if 'Schedule E' in form_types:
        income_types.append('rental_income')
    if 'K-1' in form_types:
        income_types.append('business_owner')
    if 'Schedule D' in form_types or 'Form 8949' in form_types:
        income_types.append('capital_gains')
    if '1099-INT' in form_types or '1099-DIV' in form_types:
        income_types.append('investment_income')

    return income_types if income_types else ['unknown']
```

### Joint Strategy Check
```python
# Source: Pattern derived from IRS Spousal IRA rules

def _check_spousal_ira(spouse1_summary, spouse2_summary, joint_result):
    """Check Spousal IRA eligibility and benefit"""
    IRA_LIMIT_2026 = 7500
    IRA_LIMIT_50PLUS = 8600

    spouse1_income = spouse1_summary.get('total_income', 0)
    spouse2_income = spouse2_summary.get('total_income', 0)
    combined_income = spouse1_income + spouse2_income

    # Check if one spouse has low/no earned income
    low_income_spouse = None
    if spouse1_income < IRA_LIMIT_2026 and spouse2_income >= IRA_LIMIT_2026:
        low_income_spouse = 'spouse1'
        max_contribution = IRA_LIMIT_2026
    elif spouse2_income < IRA_LIMIT_2026 and spouse1_income >= IRA_LIMIT_2026:
        low_income_spouse = 'spouse2'
        max_contribution = IRA_LIMIT_2026
    else:
        return {'applicable': False, 'reason': 'Both spouses have sufficient earned income'}

    # Calculate tax benefit (assume 22% marginal rate if not known)
    marginal_rate = joint_result.get('mfj', {}).get('marginal_rate', 22) / 100
    benefit = max_contribution * marginal_rate

    return {
        'applicable': True,
        'status': 'POTENTIALLY_MISSED' if low_income_spouse else 'NOT_APPLICABLE',
        'benefit': benefit,
        'recommendation': f"Non-working spouse ({low_income_spouse}) can contribute up to ${max_contribution:,} to IRA",
        'details': {
            'beneficiary': low_income_spouse,
            'max_contribution': max_contribution,
            'estimated_tax_savings': benefit
        }
    }
```

### Strategy Display with Feasibility Warning
```javascript
// Source: Pattern for joint_analysis.js enhancement

function renderPerSpouseStrategies(strategies, clientName, filingStatus) {
    const strategiesHtml = strategies.map(s => {
        const requirement = STRATEGY_FILING_REQUIREMENTS[s.strategy_id];
        let warningHtml = '';

        if (requirement && requirement.requires && filingStatus !== requirement.requires) {
            warningHtml = `
                <div class="strategy-warning">
                    <span class="warning-badge">Requires ${requirement.requires.toUpperCase()}</span>
                    <span class="warning-text">${requirement.warning}</span>
                </div>
            `;
        }

        return `
            <div class="strategy-item ${s.status.toLowerCase()}">
                ${warningHtml}
                <div class="strategy-name">${s.strategy_name}</div>
                <div class="strategy-status">${formatStatus(s.status)}</div>
                ${s.recommendations?.length ? `
                    <ul class="strategy-recommendations">
                        ${s.recommendations.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }).join('');

    return `
        <div class="spouse-strategies">
            <h4>${clientName}'s Tax Strategies</h4>
            ${strategiesHtml}
        </div>
    `;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Show all strategies | Filter by filing status | Phase 1 (REQ-05) | MFS ineligible credits removed |
| Single-filer focus | Dual-filer joint analysis | Phase 1-3 | MFJ vs MFS comparison |
| Generic recommendations | Income-type-aware | Phase 4 (this) | Personalized per spouse |

**2026 Tax Law Context:**
- OBBBA extended SALT cap increase ($40,400 MFJ / $20,000 MFS) through 2029
- Spousal IRA limits: $7,500 standard, $8,600 catch-up (50+)
- EITC still requires MFJ for married filers (with ARPA exception)
- Education credits remain MFJ-only

## Open Questions

1. **Age-based contribution limits:** Should system track spouse ages for catch-up contributions?
   - What we know: IRA catch-up is $1,100 extra at age 50+
   - What's unclear: Do we track birthdates?
   - Recommendation: Add optional birth_year to Client model, use for limit calculations

2. **State-specific joint strategies:** Do state tax rules differ for joint strategies?
   - What we know: 9 community property states have different MFS rules
   - What's unclear: Scope of ATSA state support
   - Recommendation: Defer state-specific joint strategies to future phase

3. **Manual entry validation:** How much validation on manually entered data?
   - What we know: OCR extraction has parsing validation
   - What's unclear: Should manual entry have same validation?
   - Recommendation: Basic range validation (income > 0), warn on suspicious values

## Sources

### Primary (HIGH confidence)
- [IRS EITC Qualification Rules](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc)
- [IRS Education Credits (AOTC/LLC)](https://www.irs.gov/credits-deductions/individuals/education-credits-aotc-and-llc)
- [IRS 2026 Tax Inflation Adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill)
- Existing codebase: services/tax_strategies.py, services/joint_analysis_service.py

### Secondary (MEDIUM confidence)
- [Fidelity IRA Contribution Limits 2025-2026](https://www.fidelity.com/learning-center/smart-money/ira-contribution-limits)
- [Vanguard Roth IRA Income Limits 2026](https://investor.vanguard.com/investor-resources-education/iras/roth-ira-income-limits)
- [Tax Foundation 2026 Tax Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/)

### Tertiary (for pattern validation)
- [W-2 Tax Strategies for High Earners 2026](https://defiantcap.com/w2-tax-planning-strategies-high-income-earners/)
- [Self-Employment Tax Strategies 2026](https://unclekam.com/tax-strategy-blog/self-employment-tax-rate/)

## Metadata

**Confidence breakdown:**
- Current system analysis: HIGH - Verified in existing codebase
- Strategy requirements: HIGH - IRS official sources
- Implementation patterns: HIGH - Follows established codebase patterns
- Joint strategy calculations: MEDIUM - Logic derived from IRS rules, needs testing

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable domain, tax rules don't change mid-year)
