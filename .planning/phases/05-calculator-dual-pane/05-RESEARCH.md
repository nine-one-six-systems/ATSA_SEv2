# Phase 5: Calculator Dual-Pane Mode - Research

**Researched:** 2026-02-05
**Domain:** Dual-pane tax calculator UI with MFJ/MFS per-spouse input and combined results
**Confidence:** HIGH

## Summary

This phase transforms the existing single-pane tax calculator (calculator.html) into a dual-pane tool when the user selects a married filing status (MFJ or MFS). The research investigated five key areas: (1) how to architect the form transformation from single-pane to dual-pane, (2) how MFJ calculations actually work when spouses have different income sources, (3) how to handle shared dependents, (4) what API endpoint strategy to use, and (5) how to build the MFJ vs MFS comparison in results.

The standard approach is to keep the filing status toggle at the top of the form and dynamically transform the form area below it -- hiding the single-pane form and showing a Split.js-powered dual-pane layout when MFJ or MFS is selected. The existing TaxCalculator service already handles all filing statuses correctly and requires no modification. The key insight is that MFJ calculation requires combining both spouses' incomes into a single call to `TaxCalculator.calculate_federal_tax()` with `filing_status='married_joint'`, while MFS requires two separate calls with `filing_status='married_separate'`. FICA/SE taxes are always per-individual regardless of filing status.

**Primary recommendation:** Create a new `/api/calculator/calculate-dual` endpoint that accepts both spouses' data, orchestrates TaxCalculator calls for MFJ (combined income) and MFS (per-spouse), and returns per-spouse breakdowns plus joint totals plus MFJ-vs-MFS comparison in a single response.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Split.js | 1.6.5 | Resizable dual-pane layout | Already in use on joint_analysis.html, 2kb CDN, no npm needed |
| Vanilla JS (ES6+) | N/A | Form logic, DOM manipulation, API calls | Consistent with existing codebase, no framework overhead |
| CSS Grid + Flexbox | N/A | Macro layout (panes) + micro layout (form elements) | Proven pattern from v1.0 split-screen implementation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Intl.NumberFormat | Built-in | Currency formatting | Already used in calculator.js for formatCurrency() |
| localStorage | Built-in | Persist split pane sizes | Save user's preferred pane width ratio |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Split.js CDN | CSS resize property | CSS resize lacks drag handle UX, no programmatic control, no callbacks |
| New /calculate-dual endpoint | Extend existing /calculate | Extending pollutes single-calculation contract, harder to maintain |
| DOM cloning for spouse panes | Template literals in JS | Cloning preserves event bindings but is fragile; template literals are explicit |

**Installation:**
```html
<!-- Already in use, same CDN as joint_analysis.html -->
<script src="https://unpkg.com/split.js@1.6.5/dist/split.min.js"></script>
```

No additional npm packages needed.

## Architecture Patterns

### Recommended Project Structure
```
Changes to existing files:
  templates/calculator.html      # Add dual-pane HTML structure, Split.js CDN
  static/js/calculator.js        # Add dual-pane logic, form transformation, API call
  static/css/style.css           # Add calculator dual-pane CSS (reuse .spouse-panel patterns)
  routes/calculator.py           # Add /calculator/calculate-dual endpoint

No new files required.
```

### Pattern 1: Form Transformation on Filing Status Change
**What:** When user clicks MFJ or MFS toggle button, the single-pane form hides and a dual-pane layout appears. When user clicks Single/HoH/QSS, dual-pane hides and single-pane reappears.
**When to use:** Always -- this is the core UX pattern for CALC-01 through CALC-06.
**Example:**
```javascript
// Source: Derived from existing handleFilingStatusChange() in calculator.js
function handleFilingStatusChange(status) {
    // Update toggle buttons (existing logic)
    document.querySelectorAll('.filing-status-toggle .toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.status === status) btn.classList.add('active');
    });
    document.getElementById('filing-status').value = status;

    const isDualPane = (status === 'married_joint' || status === 'married_separate');
    const singleForm = document.getElementById('single-pane-form');
    const dualForm = document.getElementById('dual-pane-form');

    if (isDualPane) {
        singleForm.style.display = 'none';
        dualForm.style.display = 'block';
        initCalculatorSplit();  // Initialize Split.js if not already
    } else {
        singleForm.style.display = 'block';
        dualForm.style.display = 'none';
        destroyCalculatorSplit();  // Clean up Split.js
    }
}
```

### Pattern 2: Server-Side Orchestration for Dual Calculation
**What:** A single API endpoint receives both spouses' data, runs MFJ (combined) and MFS (per-spouse) calculations server-side, returns structured response.
**When to use:** Always for dual-pane submissions -- never calculate taxes client-side.
**Why:** The existing TaxCalculator already handles all income source types (W2, LLC, S-Corp) with correct QBI, FICA, SE tax, capital gains. Duplicating this in JS would be a maintenance nightmare and error-prone.
**Example:**
```python
# Source: Extends existing pattern in routes/calculator.py
@calculator_bp.route('/calculator/calculate-dual', methods=['POST'])
def calculate_dual_tax():
    data = request.get_json()
    husband = data['husband']
    wife = data['wife']
    dependents = int(data.get('dependents', 0))
    tax_year = int(data.get('tax_year', 2026))

    # --- MFJ: Combine incomes into single calculation ---
    # MFJ combines both spouses' incomes and applies joint brackets/deductions
    # FICA/SE tax is ALWAYS per-individual, even for MFJ
    mfj_result = _calculate_mfj(husband, wife, dependents, tax_year)

    # --- MFS: Calculate each spouse independently ---
    mfs_husband = _calculate_single_spouse(husband, 'married_separate', dependents, tax_year)
    mfs_wife = _calculate_single_spouse(wife, 'married_separate', 0, tax_year)
    # Note: dependents assigned to husband by default; user chose allocation

    # --- Build comparison ---
    comparison = _build_comparison(mfj_result, mfs_husband, mfs_wife)

    return jsonify({
        'success': True,
        'husband': mfj_result['husband_breakdown'],
        'wife': mfj_result['wife_breakdown'],
        'mfj': mfj_result['joint_totals'],
        'mfs_husband': mfs_husband,
        'mfs_wife': mfs_wife,
        'comparison': comparison
    })
```

### Pattern 3: MFJ Income Combination Logic
**What:** For MFJ, combine both spouses' incomes by type, calculate joint federal tax on combined ordinary income using MFJ brackets, but keep FICA/SE per-individual.
**When to use:** MFJ calculations only.
**Critical insight from IRS:** When filing jointly, all income is combined into a single AGI. The joint standard deduction ($32,200 for 2026) applies once to the combined income. Tax brackets are MFJ brackets. But payroll taxes (FICA, SE) are always calculated per-individual -- marriage does not combine or offset payroll taxes.
**Example:**
```python
def _calculate_mfj(husband_data, wife_data, dependents, tax_year):
    # Convert both to annual income
    h_annual = TaxCalculator.convert_income_to_annual(
        husband_data['income'], husband_data['income_frequency'])
    w_annual = TaxCalculator.convert_income_to_annual(
        wife_data['income'], wife_data['income_frequency'])

    # For S-Corp types, use salary + distributions
    if husband_data['income_source'] in ['llc_s_corp', 's_corp']:
        h_annual = husband_data['salary'] + husband_data['distributions']
    if wife_data['income_source'] in ['llc_s_corp', 's_corp']:
        w_annual = wife_data['salary'] + wife_data['distributions']

    combined_income = h_annual + w_annual

    # Get MFJ standard deduction (applied once to combined income)
    std_deduction = TaxCalculator.get_standard_deduction('married_joint', 'federal', None, tax_year)

    # Calculate combined QBI (sum of both spouses' QBI-eligible income)
    h_qbi = _get_qbi_eligible_income(husband_data)
    w_qbi = _get_qbi_eligible_income(wife_data)
    combined_qbi = h_qbi + w_qbi

    # QBI deduction uses MFJ thresholds ($394,600 for 2026)
    taxable_before_qbi = max(0, combined_income - std_deduction)
    qbi_result = TaxCalculator.calculate_qbi_deduction(
        combined_qbi, taxable_before_qbi, 'married_joint', tax_year)

    # Combined ordinary income tax using MFJ brackets
    taxable_income = max(0, combined_income - std_deduction - qbi_result['deduction_amount'])
    brackets = TaxCalculator.get_tax_brackets('federal', None, 'married_joint', tax_year)
    tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)

    # Child Tax Credit on joint return (all dependents on one return)
    ctc = TaxCalculator.calculate_child_tax_credit(dependents, tax_year)
    income_tax = max(0, tax_result['total_tax'] - ctc)

    # FICA/SE taxes are PER-INDIVIDUAL (critical: not combined)
    h_payroll = _calculate_individual_payroll_tax(husband_data, 'married_joint', tax_year)
    w_payroll = _calculate_individual_payroll_tax(wife_data, 'married_joint', tax_year)

    total_tax = income_tax + h_payroll['total'] + w_payroll['total']
    # ... return structured result
```

### Pattern 4: Shared Controls at Top, Per-Spouse Below
**What:** Filing status toggle and dependents selector remain at the page level (above the split panes). Per-spouse inputs (income, frequency, source, S-Corp fields, state) are duplicated in each pane.
**When to use:** Always -- this reflects tax reality where filing status and dependents are household-level decisions.
**Layout:**
```
+--------------------------------------------------+
| Filing Status:  [Single] [MFJ] [MFS] [HoH] [QSS]|
| Dependents:     [0 v]                            |
+--------------------------------------------------+
| Husband (Left)      |  | Wife (Right)            |
| Income: [____]       |  | Income: [____]          |
| Frequency: [Annual]  |G | Frequency: [Annual]     |
| Source: [W2 v]       |u | Source: [LLC v]          |
| [S-Corp fields]      |t | [S-Corp fields]         |
| State: [CA v]        |t | State: [NY v]           |
|                      |e |                         |
|                      |r |                         |
+--------------------------------------------------+
| [Analyze] button                                  |
+--------------------------------------------------+
| Results: Per-spouse + Joint totals + Comparison   |
+--------------------------------------------------+
```

### Anti-Patterns to Avoid
- **Client-side tax calculation:** Never calculate MFJ/MFS in JavaScript. The TaxCalculator handles QBI, FICA, SE tax, capital gains, bracket stacking -- duplicating this in JS guarantees divergence and bugs.
- **Separate API calls per spouse:** Do not make two separate `/calculate` calls from the frontend. One `/calculate-dual` call lets the server orchestrate correctly (especially for MFJ where incomes must be combined).
- **Modifying TaxCalculator:** The existing service already handles all filing statuses with correct thresholds. The new endpoint orchestrates it; it does not modify it.
- **Per-spouse dependents for MFJ:** On a joint return, dependents are claimed once for the household. Do not show per-spouse dependent selectors for MFJ. For MFS, dependents must be allocated to one spouse only.
- **Applying MFJ standard deduction per spouse:** The $32,200 MFJ standard deduction applies ONCE to combined income, not $32,200 per spouse.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resizable split panes | CSS-only two-column layout | Split.js (already in project) | Drag handle, size persistence, responsive destroy/recreate |
| Tax bracket calculation | JS bracket math | TaxCalculator.calculate_federal_tax() server-side | 4 income source types, QBI, capital gains stacking, FICA, SE tax |
| Currency formatting | Manual toFixed() | Intl.NumberFormat (already in calculator.js) | Handles edge cases, locale-aware |
| Income frequency conversion | Manual multiplier | TaxCalculator.convert_income_to_annual() | Already handles all 5 frequencies correctly |
| State tax calculation | Inline state tax logic | TaxCalculator.calculate_state_tax() | Handles 50 states + DC, surtaxes, no-income-tax states |

**Key insight:** The entire TaxCalculator service (891 lines) already solves every calculation problem. This phase is purely about UI transformation and API orchestration -- zero tax logic needs to be written.

## Common Pitfalls

### Pitfall 1: Applying MFJ Standard Deduction Per Spouse
**What goes wrong:** Each spouse gets the full $32,200 MFJ standard deduction, effectively doubling it to $64,400.
**Why it happens:** Treating MFJ as "two separate MFS calculations with joint brackets" instead of "one combined calculation."
**How to avoid:** MFJ = combine incomes, apply ONE standard deduction ($32,200), apply joint brackets to combined taxable income. The deduction is not split or doubled.
**Warning signs:** MFJ tax coming out significantly lower than expected; MFJ always wins over MFS.

### Pitfall 2: Combining FICA/SE Taxes for MFJ
**What goes wrong:** Adding both spouses' salaries together and calculating FICA on the combined amount, potentially pushing over Social Security wage base differently.
**Why it happens:** Treating all taxes as "combined" for MFJ.
**How to avoid:** FICA and SE taxes are ALWAYS per-individual. Each spouse's W2 salary has its own Social Security wage base cap ($175,000 for 2026). Each spouse's LLC income has its own SE tax calculation. Calculate FICA/SE per person, then add to combined income tax.
**Warning signs:** FICA tax is much higher or lower than expected for a two-income couple.
**IRS rule:** "Payroll taxes are still calculated per individual -- each spouse pays Social Security and Medicare tax on their own earnings."

### Pitfall 3: Forgetting S-Corp Income Type Differences Between Spouses
**What goes wrong:** Both spouse panes assume the same income source type.
**Why it happens:** Copy-pasting form logic without making income source independent per pane.
**How to avoid:** Each spouse pane MUST have its own income source dropdown that independently shows/hides S-Corp salary/distributions fields. The API must accept different income_source values per spouse.
**Warning signs:** Changing one spouse's income source affects the other pane.

### Pitfall 4: Dependent Double-Counting
**What goes wrong:** Both MFJ and MFS calculations count dependents for both spouses.
**Why it happens:** Not understanding that MFJ claims dependents once on the joint return, while MFS requires explicit allocation to one spouse.
**How to avoid:**
- MFJ: Total dependents count from the shared control. All dependents on the joint return.
- MFS: Dependents claimed by ONE spouse only. The API should accept `dependents_husband` and `dependents_wife` for MFS, where `dependents_husband + dependents_wife = total_dependents`.
- For the calculator MVP, simplify: dependents are shared for MFJ (total count) and allocated to one spouse for MFS (default to husband, or add allocation dropdown).
**Warning signs:** MFS child tax credit is doubled compared to MFJ.

### Pitfall 5: Regression on Single-Pane Filing Statuses
**What goes wrong:** Single/HoH/QSS filing status selection breaks or shows dual-pane layout.
**Why it happens:** Form transformation logic has edge cases (rapid toggling, default state on page load).
**How to avoid:**
- Page loads in single-pane mode (Single is default).
- Only MFJ and MFS trigger dual-pane.
- Switching from MFJ back to Single must fully restore single-pane and destroy Split.js instance.
- Test: load page, verify single works, switch to MFJ, switch back to Single, verify single still works.
**Warning signs:** Split.js gutter visible in single-pane mode; form fields from dual-pane leak into single-pane submission.

### Pitfall 6: Split.js Not Destroyed Before Re-Init
**What goes wrong:** Multiple Split.js instances accumulate, causing jittery drag behavior or layout corruption.
**Why it happens:** Toggling MFJ -> Single -> MFJ without destroying the previous Split.js instance.
**How to avoid:** Always call `splitInstance.destroy()` before setting `splitInstance = null`. Check `if (splitInstance)` before creating a new one. Follow the exact pattern from joint_analysis.js.
**Warning signs:** Gutter multiplies, pane widths jump unpredictably.

### Pitfall 7: QBI Calculation with Mixed Income Sources
**What goes wrong:** For MFJ, QBI is calculated only on one spouse's qualifying income, ignoring the other.
**Why it happens:** Only checking if the first spouse has LLC/S-Corp income for QBI eligibility.
**How to avoid:** Sum QBI-eligible income from BOTH spouses. If husband has LLC ($100k QBI) and wife has W2 ($0 QBI), combined QBI = $100k. If both have LLCs, combined QBI = sum of both. Use MFJ QBI threshold ($394,600) for the combined amount.
**Warning signs:** QBI deduction disappears when second spouse has W2 income.

## Code Examples

Verified patterns from existing codebase:

### HTML Structure for Dual-Pane Calculator
```html
<!-- Source: Derived from joint_analysis.html patterns -->

<!-- Shared controls (above split) -->
<div class="calculator-shared-controls">
    <!-- Filing Status Toggle (existing, moved here) -->
    <div class="form-group">
        <label>Filing Status *</label>
        <div class="filing-status-toggle">
            <button type="button" class="toggle-btn active" data-status="single">Single</button>
            <button type="button" class="toggle-btn" data-status="married_joint">MFJ</button>
            <button type="button" class="toggle-btn" data-status="married_separate">MFS</button>
            <button type="button" class="toggle-btn" data-status="head_of_household">HoH</button>
            <button type="button" class="toggle-btn" data-status="qualifying_surviving_spouse">QSS</button>
        </div>
        <input type="hidden" id="filing-status" value="single">
    </div>

    <!-- Dependents (shared for household) -->
    <div class="form-group">
        <label for="dependents">Child Tax Credit (17 and under)</label>
        <select id="dependents">
            <option value="0" selected>0</option>
            <!-- ... 1-15 ... -->
        </select>
    </div>
</div>

<!-- Single-Pane Form (default, visible for Single/HoH/QSS) -->
<div id="single-pane-form">
    <!-- Existing calculator form fields (income, frequency, source, state, etc.) -->
</div>

<!-- Dual-Pane Form (hidden by default, visible for MFJ/MFS) -->
<div id="dual-pane-form" style="display: none;">
    <div class="calculator-split-container" id="calc-split-container">
        <div id="husband-pane" class="spouse-calc-panel">
            <h4>Husband</h4>
            <!-- Income, frequency toggle, source dropdown, S-Corp fields, state -->
        </div>
        <div id="wife-pane" class="spouse-calc-panel">
            <h4>Wife</h4>
            <!-- Income, frequency toggle, source dropdown, S-Corp fields, state -->
        </div>
    </div>
</div>

<!-- Shared Analyze button -->
<div class="form-actions">
    <button type="submit" class="btn btn-primary">Analyze</button>
</div>
```

### Split.js Initialization for Calculator
```javascript
// Source: Pattern from joint_analysis.js lines 44-75
let calcSplitInstance = null;

function initCalculatorSplit() {
    if (calcSplitInstance) return;  // Already initialized
    if (typeof Split === 'undefined') return;
    if (window.innerWidth <= 768) return;  // Mobile: stack vertically

    let sizes = [50, 50];
    const saved = localStorage.getItem('calculatorSplitSizes');
    if (saved) {
        try { sizes = JSON.parse(saved); } catch (e) { /* use defaults */ }
    }

    calcSplitInstance = Split(['#husband-pane', '#wife-pane'], {
        sizes: sizes,
        minSize: 280,
        gutterSize: 10,
        cursor: 'col-resize',
        onDragEnd: function(sizes) {
            localStorage.setItem('calculatorSplitSizes', JSON.stringify(sizes));
        }
    });
}

function destroyCalculatorSplit() {
    if (calcSplitInstance) {
        calcSplitInstance.destroy();
        calcSplitInstance = null;
    }
}
```

### Dual-Pane Form Submission
```javascript
// Source: Extends existing calculateTax() pattern in calculator.js
async function calculateDualTax() {
    const filingStatus = document.getElementById('filing-status').value;
    const dependents = parseInt(document.getElementById('dependents').value) || 0;

    // Gather husband data
    const husband = gatherSpouseData('husband');
    const wife = gatherSpouseData('wife');

    // Validation
    if (!validateSpouseData(husband, 'Husband') || !validateSpouseData(wife, 'Wife')) return;

    const response = await fetch(`${API_BASE}/calculator/calculate-dual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filing_status: filingStatus,
            husband: husband,
            wife: wife,
            dependents: dependents,
            tax_year: 2026
        })
    });

    const result = await response.json();
    if (result.success) {
        displayDualResults(result);
    }
}

function gatherSpouseData(prefix) {
    return {
        income: parseFloat(document.getElementById(`${prefix}-income`).value) || 0,
        income_frequency: document.getElementById(`${prefix}-frequency`).value || 'annual',
        income_source: document.getElementById(`${prefix}-source`).value || 'w2',
        salary: parseFloat(document.getElementById(`${prefix}-salary`).value) || 0,
        distributions: parseFloat(document.getElementById(`${prefix}-distributions`).value) || 0,
        state_code: document.getElementById(`${prefix}-state`).value || null
    };
}
```

### API Endpoint for Dual Calculation
```python
# Source: Extends routes/calculator.py pattern
@calculator_bp.route('/calculator/calculate-dual', methods=['POST'])
def calculate_dual_tax():
    try:
        data = request.get_json()
        husband = data.get('husband', {})
        wife = data.get('wife', {})
        dependents = int(data.get('dependents', 0))
        tax_year = int(data.get('tax_year', 2026))

        # Calculate MFJ (combined incomes, joint brackets)
        mfj_result = _calculate_mfj_scenario(husband, wife, dependents, tax_year)

        # Calculate MFS for each spouse independently
        # For MFS, dependents go to husband by default (simplification)
        mfs_husband = _calculate_spouse_tax(husband, 'married_separate', dependents, tax_year)
        mfs_wife = _calculate_spouse_tax(wife, 'married_separate', 0, tax_year)

        # Build comparison
        mfj_total = mfj_result['totals']['total_tax']
        mfs_total = mfs_husband['totals']['total_tax'] + mfs_wife['totals']['total_tax']
        savings = abs(mfj_total - mfs_total)
        recommended = 'MFJ' if mfj_total <= mfs_total else 'MFS'

        return jsonify({
            'success': True,
            'mfj': mfj_result,
            'mfs_husband': mfs_husband,
            'mfs_wife': mfs_wife,
            'comparison': {
                'mfj_total_tax': round(mfj_total, 2),
                'mfs_combined_tax': round(mfs_total, 2),
                'savings': round(savings, 2),
                'recommended': recommended,
                'reason': f'Filing {recommended} saves ${savings:,.2f}'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
```

### Results Display Structure
```javascript
// Source: Extends existing displayResults() pattern in calculator.js
function displayDualResults(result) {
    const resultsDiv = document.getElementById('calculator-results');
    resultsDiv.style.display = 'block';

    const html = `
        <!-- Per-Spouse Breakdown (RSLT-01) -->
        <div class="dual-results-grid">
            <div class="spouse-result-card">
                <h4>Husband - Tax Breakdown</h4>
                ${renderSpouseTaxBreakdown(result.mfj.husband_breakdown)}
            </div>
            <div class="spouse-result-card">
                <h4>Wife - Tax Breakdown</h4>
                ${renderSpouseTaxBreakdown(result.mfj.wife_breakdown)}
            </div>
        </div>

        <!-- Joint Totals (RSLT-02) -->
        <div class="result-card totals-card">
            <h4>Joint Total Tax Liability (MFJ)</h4>
            ${renderJointTotals(result.mfj)}
        </div>

        <!-- MFJ vs MFS Comparison (RSLT-03) -->
        <div class="comparison-section">
            <h4>MFJ vs MFS Comparison</h4>
            ${renderFilingComparison(result.comparison, result.mfj, result.mfs_husband, result.mfs_wife)}
        </div>
    `;

    resultsDiv.innerHTML = html;
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

## Key Design Decisions

### Decision 1: New Endpoint vs. Extending Existing
**Decision:** Create new `/api/calculator/calculate-dual` endpoint.
**Rationale:**
- The existing `/calculate` endpoint has a clean single-person contract (income, source, status, state).
- Dual-pane requires fundamentally different input shape (two sets of income data).
- MFJ requires income combination logic that does not apply to single filers.
- Keeping endpoints separate avoids flag-driven complexity (`if is_dual_pane:`) in a single function.
- The existing endpoint must remain untouched for CALC-06 (no regression).
**Confidence:** HIGH -- Clean separation of concerns is the proven pattern in this codebase (see separate joint_analysis routes).

### Decision 2: MFJ Calculation Approach
**Decision:** Combine both incomes into a single MFJ call for income tax, but calculate FICA/SE per individual.
**Rationale:**
- IRS rules: MFJ combines all income into one AGI, applies one standard deduction, uses joint brackets.
- IRS rules: FICA/SE taxes are always per-individual. Marriage does not combine payroll taxes.
- The existing `TaxCalculator.calculate_federal_tax()` handles the income tax portion correctly when given combined income + 'married_joint' filing status.
- For mixed income sources (e.g., husband W2 + wife S-Corp), need to determine QBI-eligible portion and calculate payroll taxes separately.
**Confidence:** HIGH -- IRS rules verified via Tax Foundation and IRS.gov.

### Decision 3: Dependent Handling
**Decision:** Shared dependents control at page level. For MFJ, all dependents on joint return. For MFS, default allocation to husband with optional override.
**Rationale:**
- MFJ: Dependents are claimed once on the joint return. Total count applies to combined income tax calculation.
- MFS: Each child can only be claimed by ONE spouse. For calculator MVP, default to husband.
- Phase 6 could add per-spouse allocation UI for MFS if needed.
- The calculator is a quick what-if tool, not a full tax return -- simplified allocation is appropriate.
**Confidence:** HIGH for MFJ behavior. MEDIUM for MFS default allocation (simplification is pragmatic but not fully flexible).

### Decision 4: Filing Status Toggle UX
**Decision:** Keep filing status toggle at top of page. Form area below transforms between single-pane and dual-pane.
**Rationale:**
- Filing status is a household-level decision that determines the entire form layout.
- Matches industry pattern (TurboTax, TaxSlayer Pro show filing status first, then appropriate inputs).
- Smooth transition: hide single form, show dual form (no page reload needed).
- Default state is Single (single-pane) matching current behavior.
**Confidence:** HIGH -- Consistent with existing UX and industry standards.

### Decision 5: MFJ vs MFS Comparison
**Decision:** Always calculate BOTH MFJ and MFS scenarios when dual-pane is active, show comparison in results.
**Rationale:**
- Requirements RSLT-03 explicitly asks for comparison "when both can be calculated."
- Since we have both spouses' data, we can always calculate both scenarios.
- The comparison shows total tax for each, savings amount, and recommended filing status.
- This is the core value proposition -- tax professionals need this comparison instantly.
**Confidence:** HIGH -- Directly matches requirements.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate pages per spouse | Split-screen single page | 2024+ | Better UX, side-by-side comparison |
| Client-side tax calc | Server-side with API | Always best practice | Accuracy, single source of truth |
| Fixed 50/50 split | User-resizable Split.js | Split.js 1.6+ | Accommodates different content sizes |
| Framework-dependent UI | Vanilla JS + CSS Grid | 2024+ ES6 maturity | No build step, smaller bundle, fewer deps |

**Deprecated/outdated:**
- React/Vue for this use case: Overkill for a Flask template app; would require build tooling and framework overhead for simple form logic.
- CSS-only resizable: The `resize` CSS property lacks drag handle UX and programmatic control.

## Open Questions

Things that couldn't be fully resolved:

1. **MFS Dependent Allocation UI**
   - What we know: IRS requires each child claimed by one spouse only on MFS.
   - What's unclear: Should the calculator MVP allow per-child allocation (dropdown per child) or just total allocation (all to husband/wife)?
   - Recommendation: For MVP, keep simple. Add a dropdown "Dependents claimed by: [Husband/Wife]" for MFS mode. This is a calculator, not a tax return.

2. **Mixed Income Source MFJ Tax Calculation Complexity**
   - What we know: When one spouse has W2 and another has S-Corp, MFJ income tax applies to combined ordinary income using joint brackets.
   - What's unclear: How to display per-spouse federal breakdown in MFJ mode when income is combined. Do we prorate the joint income tax back to each spouse?
   - Recommendation: Show joint income tax as a single figure (not prorated). Show per-spouse FICA/SE/state taxes. Show combined total. This matches how IRS Form 1040 works -- there is no "per-spouse federal income tax" on a joint return.

3. **State Tax with Different States per Spouse**
   - What we know: CALC-05 requires independent state selection per spouse.
   - What's unclear: How to calculate state tax for MFJ when spouses are in different states (e.g., husband CA, wife NY). Most state returns use combined income for MFJ.
   - Recommendation: For MVP, calculate each spouse's state tax using their selected state and their individual income. Note that this is a simplification -- real multi-state MFJ returns are more complex. Add a disclaimer in results.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `services/tax_calculator.py` (891 lines) -- all tax calculations verified
- Existing codebase: `routes/calculator.py` -- current API contract verified
- Existing codebase: `static/js/calculator.js` -- current form logic verified
- Existing codebase: `templates/joint_analysis.html` + `static/js/joint_analysis.js` -- Split.js pattern verified
- [Tax Foundation 2026 Tax Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) -- MFJ standard deduction $32,200, CTC $2,200, brackets verified
- [IRS 2026 Tax Adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill) -- Official IRS source for 2026 tax parameters

### Secondary (MEDIUM confidence)
- [Split.js GitHub README](https://github.com/nathancahill/split/blob/master/packages/splitjs/README.md) -- API options verified: destroy(), getSizes(), setSizes(), collapse(), minSize, maxSize
- [TurboTax MFJ Income Combination](https://turbotax.intuit.com/tax-tips/marriage/should-you-and-your-spouse-file-taxes-jointly-or-separately/L7gyjnqyM) -- Confirmed MFJ combines all income, single return
- [Fidelity 2026 Brackets](https://www.fidelity.com/learning-center/personal-finance/tax-brackets) -- Confirmed payroll taxes always per-individual

### Tertiary (LOW confidence)
- TaxSlayer Pro MFJ vs MFS UX pattern -- could not access full documentation (403), but search results confirm multi-column comparison layout is industry standard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already in use, no new dependencies
- Architecture: HIGH -- Extends proven patterns from v1.0 (Split.js, service orchestration, API endpoints)
- Tax calculation logic: HIGH -- TaxCalculator already handles all scenarios; MFJ combination rules verified with IRS
- Pitfalls: HIGH -- 7 pitfalls identified from domain knowledge and codebase analysis
- UX patterns: MEDIUM -- Industry standard (filing status first, per-spouse inputs), but exact transition UX is design judgment

**Research date:** 2026-02-05
**Valid until:** 2026-03-05 (stable domain -- tax rules fixed for tax year, Split.js stable)
