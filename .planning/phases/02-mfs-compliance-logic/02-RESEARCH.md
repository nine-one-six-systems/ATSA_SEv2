# Phase 2: MFS-Specific Compliance Logic - Research

**Researched:** 2026-02-04
**Domain:** Tax compliance - MFS deduction coordination, SALT caps, expense allocation
**Confidence:** HIGH

## Summary

This research investigates IRS compliance rules specific to Married Filing Separately (MFS) status that must be enforced in dual-filer tax analysis. The three critical compliance areas are: (1) deduction method coordination (if one spouse itemizes, both must itemize), (2) SALT cap enforcement ($20,000 per MFS spouse in 2026 under OBBBA, not $40,400), and (3) shared expense allocation (mortgage interest, property taxes split by ownership/payment).

The current implementation in Phase 1 uses standard deductions only — no itemized deduction path exists. Adding MFS compliance requires: database schema additions for deduction method and expense allocation tracking, service layer validation to enforce deduction coordination, and SALT cap logic by filing status.

**Primary recommendation:** Extend existing models with minimal new fields, enforce coordination rules at service layer (not database constraints alone), and use flexible JSON storage for expense allocation percentages to avoid complex schema changes.

## Standard Stack

The established libraries/tools for this domain:

### Core (Existing - No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask-SQLAlchemy | 2.0+ | ORM for database models | Already used throughout codebase, handles migrations |
| SQLite (WAL mode) | 3.x | Local database | Phase 1 enabled WAL mode for dual-writer concurrency |
| TaxCalculator | internal | Tax calculation engine | Already handles all filing statuses correctly (lines 83-108) |
| JointAnalysisService | internal | MFJ/MFS orchestration | Phase 1 implementation, extend for itemized path |

### Supporting (No New Dependencies)
No external libraries needed. All compliance logic builds on existing stack.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON fields for allocation | Separate ExpenseAllocation table | JSON simpler for MVP, separate table better for complex queries/reporting |
| Service-layer validation | Database CHECK constraints | Service layer more flexible, easier to test, clearer error messages |
| Enum for deduction_method | Boolean is_itemized flag | Enum clearer ("standard" vs "itemized"), future-proof for other methods |

**Installation:**
```bash
# No new dependencies — use existing stack
```

## Architecture Patterns

### Recommended Model Extensions

**Client model additions:**
```python
# models/client.py - Add to existing Client model
deduction_method = db.Column(db.String(20), default='standard')  # 'standard' or 'itemized'
```

**New ItemizedDeduction model (optional for Phase 2, recommended for Phase 3+):**
```python
# models/itemized_deduction.py
class ItemizedDeduction(db.Model):
    __tablename__ = 'itemized_deductions'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)

    # Schedule A categories
    medical_expenses = db.Column(db.Float, default=0)
    state_local_taxes = db.Column(db.Float, default=0)  # Before SALT cap
    mortgage_interest = db.Column(db.Float, default=0)
    charitable_contributions = db.Column(db.Float, default=0)

    # Allocation metadata (JSON for flexibility)
    # Example: {"mortgage_interest": {"allocation": "both", "taxpayer_pct": 60, "spouse_pct": 40}}
    allocation_metadata = db.Column(db.Text, nullable=True)  # JSON

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Simpler alternative for MVP (recommended for Phase 2):**
Store itemized deduction amounts directly in ExtractedData with special field_name convention:
```python
# Use existing ExtractedData model with naming convention
# field_name examples:
#   "itemized:medical_expenses"
#   "itemized:state_local_taxes"
#   "itemized:mortgage_interest:taxpayer_pct:60"
#   "itemized:mortgage_interest:spouse_pct:40"
```

### Pattern 1: Deduction Method Coordination Enforcement
**What:** When one MFS spouse changes deduction method, validate and potentially block the change
**When to use:** On any update to Client.deduction_method when filing_status='married_separate'
**Example:**
```python
# Source: IRS FAQ - Other Deduction Questions
# https://www.irs.gov/faqs/itemized-deductions-standard-deduction/other-deduction-questions

def validate_deduction_method_change(client_id, new_method):
    """
    Enforce IRS rule: if one MFS spouse itemizes, both must itemize.

    Returns:
        dict: {'allowed': bool, 'message': str, 'action': str}
    """
    client = Client.query.get(client_id)

    if client.filing_status != 'married_separate':
        return {'allowed': True, 'message': 'No coordination required', 'action': 'allow'}

    if not client.spouse_id:
        return {'allowed': True, 'message': 'No spouse linked', 'action': 'allow'}

    spouse = Client.query.get(client.spouse_id)

    # If spouse is itemizing and client wants standard, block
    if spouse.deduction_method == 'itemized' and new_method == 'standard':
        return {
            'allowed': False,
            'message': f'Cannot use standard deduction - spouse is itemizing. Both spouses must use the same deduction method when filing separately.',
            'action': 'block',
            'required_method': 'itemized'
        }

    # If client wants to itemize, spouse must also itemize
    if new_method == 'itemized' and spouse.deduction_method == 'standard':
        return {
            'allowed': True,  # Allow but require confirmation
            'message': f'Changing to itemized deductions will require spouse to also itemize.',
            'action': 'confirm_cascade',
            'cascade_to_spouse': True
        }

    return {'allowed': True, 'message': 'Coordination satisfied', 'action': 'allow'}
```

### Pattern 2: SALT Cap by Filing Status
**What:** Apply correct SALT deduction cap based on filing status and MAGI phase-out
**When to use:** When calculating itemized deductions for any filing status
**Example:**
```python
# Source: IRS Schedule A Instructions, One Big Beautiful Bill Act (OBBBA)
# https://www.irs.gov/instructions/i1040sca

def calculate_salt_deduction(state_local_taxes, filing_status, magi, tax_year=2026):
    """
    Calculate SALT deduction with cap and income phase-out.

    2026 SALT caps under OBBBA:
    - MFJ: $40,400 (phases out above $505,000 MAGI to floor of $10,000)
    - MFS: $20,000 per spouse (phases out above $250,000 MAGI to floor of $5,000)
    - Single: $40,400 (same phase-out as MFJ)
    - HOH: $40,400 (same phase-out as MFJ)

    Phase-out: $0.30 reduction for every $1 over threshold
    """
    if tax_year == 2026:
        caps = {
            'married_joint': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
            'married_separate': {'base': 20000, 'floor': 5000, 'phaseout_start': 250000},
            'single': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
            'head_of_household': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000}
        }
    else:
        # Pre-OBBBA (TCJA original)
        caps = {
            'married_joint': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
            'married_separate': {'base': 5000, 'floor': 5000, 'phaseout_start': float('inf')},
            'single': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
            'head_of_household': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')}
        }

    cap_data = caps.get(filing_status, caps['single'])
    base_cap = cap_data['base']
    floor_cap = cap_data['floor']
    phaseout_start = cap_data['phaseout_start']

    # Apply income phase-out
    if magi > phaseout_start:
        excess_magi = magi - phaseout_start
        reduction = excess_magi * 0.30  # $0.30 per $1 over threshold
        effective_cap = max(floor_cap, base_cap - reduction)
    else:
        effective_cap = base_cap

    # Apply cap to actual state/local taxes paid
    deduction = min(state_local_taxes, effective_cap)

    return {
        'raw_salt': state_local_taxes,
        'cap_applied': effective_cap,
        'deduction_allowed': deduction,
        'capped_amount': max(0, state_local_taxes - deduction),
        'phaseout_applied': magi > phaseout_start
    }
```

### Pattern 3: Expense Allocation Tracking
**What:** Track who paid shared expenses and in what percentage for MFS
**When to use:** When spouses file separately and have joint expenses (mortgage, property taxes)
**Example:**
```python
# Source: IRS FAQ - Real Estate Taxes, Mortgage Interest
# https://www.irs.gov/faqs/itemized-deductions-standard-deduction/real-estate-taxes-mortgage-interest-points-other-property-expenses

def allocate_shared_expense(expense_type, total_amount, allocation_method, taxpayer_pct=None):
    """
    Allocate shared expense between spouses for MFS.

    Allocation methods:
    - 'taxpayer': 100% to taxpayer, 0% to spouse
    - 'spouse': 0% to taxpayer, 100% to spouse
    - 'both': Split by percentage (taxpayer_pct, spouse_pct must sum to 100)
    - 'joint': 50/50 split (default for joint payment from joint account)

    IRS rule: "If mortgage interest on a residence both you and your spouse own
    is paid from a joint checking account in which you both have an equal interest,
    then each spouse may deduct half of the interest expense."
    """
    if allocation_method == 'taxpayer':
        return {
            'taxpayer_amount': total_amount,
            'spouse_amount': 0,
            'taxpayer_pct': 100,
            'spouse_pct': 0,
            'method': 'taxpayer'
        }

    elif allocation_method == 'spouse':
        return {
            'taxpayer_amount': 0,
            'spouse_amount': total_amount,
            'taxpayer_pct': 0,
            'spouse_pct': 100,
            'method': 'spouse'
        }

    elif allocation_method == 'both':
        if taxpayer_pct is None:
            raise ValueError("taxpayer_pct required for 'both' allocation")

        spouse_pct = 100 - taxpayer_pct

        if not (0 <= taxpayer_pct <= 100):
            raise ValueError("taxpayer_pct must be between 0 and 100")

        taxpayer_amount = total_amount * (taxpayer_pct / 100)
        spouse_amount = total_amount * (spouse_pct / 100)

        return {
            'taxpayer_amount': round(taxpayer_amount, 2),
            'spouse_amount': round(spouse_amount, 2),
            'taxpayer_pct': taxpayer_pct,
            'spouse_pct': spouse_pct,
            'method': 'both'
        }

    else:  # 'joint' or default
        return {
            'taxpayer_amount': total_amount / 2,
            'spouse_amount': total_amount / 2,
            'taxpayer_pct': 50,
            'spouse_pct': 50,
            'method': 'joint'
        }
```

### Anti-Patterns to Avoid

- **Storing deduction coordination state in both spouse records:** Only store in Client.deduction_method per spouse, derive coordination state at query time. Denormalization leads to inconsistency.

- **Database foreign key constraints for deduction coordination:** Don't use FK constraints to enforce "both must itemize" — service layer validation is more flexible and provides better error messages.

- **Hard-coding SALT caps in TaxCalculator:** SALT caps change by year and legislation (TCJA → OBBBA → 2030 reversion). Use lookup tables or constants by tax_year.

- **Separate database tables for each itemized deduction category:** Too normalized for this use case. Use JSON metadata or single table with category columns.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SALT deduction calculation | Custom SALT cap logic | TaxCalculator extension with lookup table | SALT caps vary by year, filing status, income phase-outs. Pre-OBBBA vs post-OBBBA vs 2030 reversion. |
| Deduction coordination validation | Ad-hoc if/else checks | Centralized validation service method | Coordination rules may expand (community property states, special allocations). Need single source of truth. |
| Expense allocation storage | Multiple boolean flags | JSON allocation metadata | Flexible schema for allocation rules (percentage, fixed amount, conditional). Avoids 10+ columns per expense type. |
| Filing status enum values | String literals 'married separate' | Consistent constants from TaxCalculator | Already uses 'married_separate', 'married_joint'. Don't introduce variants. |

**Key insight:** Tax compliance rules are complex, version-dependent, and interconnected. Centralize in service layer with year-based lookups rather than scattering logic across models/routes.

## Common Pitfalls

### Pitfall 1: Not Enforcing Deduction Coordination on Data Change
**What goes wrong:** Spouse A switches to itemized deductions, Spouse B remains on standard deduction. Joint analysis proceeds with invalid configuration. IRS e-file system rejects return.
**Why it happens:** Validation only runs on form submission, not on data updates. Spouses can get out of sync.
**How to avoid:**
- Add validation hook on `Client.deduction_method` setter
- Service method checks spouse's deduction method before allowing change
- UI displays warning and blocks/cascades change
- Cache invalidation triggers re-check of joint analysis
**Warning signs:**
- Joint analysis shows different deduction methods for MFS spouses
- No validation error despite method mismatch
- User can save Client with deduction_method='standard' while spouse has 'itemized'

### Pitfall 2: Applying Full SALT Cap to Each MFS Spouse
**What goes wrong:** California couple with $60k combined state/local taxes files MFS. Each spouse deducts $40,400 (2026 cap), totaling $80,800 deduction. IRS requires $20,000 per spouse ($40k total for MFS couple).
**Why it happens:** Copy-paste MFJ SALT logic without filing-status-specific cap lookup. Misreading "cap increases to $40,400" without noting MFS gets half.
**How to avoid:**
- SALT cap lookup by filing status (not just year)
- Unit test with MFS scenario: $60k SALT → $20k allowed per spouse
- Display cap amount in UI: "SALT cap for MFS: $20,000 per spouse"
**Warning signs:**
- MFS calculation shows SALT deduction > $20,000 per spouse (2026)
- Joint analysis comparison shows MFS total SALT > MFJ SALT cap
- No income phase-out calculation for high earners

### Pitfall 3: Assuming 50/50 Split for All Joint Expenses
**What goes wrong:** Taxpayer paid 100% of mortgage interest from separate account. Software allocates 50% to each spouse. Spouse deducts interest they didn't pay, violating IRS rules.
**Why it happens:** Defaulting to equal split without checking payment source or ownership.
**How to avoid:**
- Require allocation method input: 'taxpayer', 'spouse', 'both' (with %), or 'joint' (50/50)
- Display warning: "Only deduct expenses you actually paid (or your share of joint payment)"
- Reference Form 1098 to determine who paid mortgage interest
**Warning signs:**
- No allocation metadata stored with expense amounts
- UI defaults to 50/50 without asking user
- Same mortgage interest amount appears for both spouses despite separate payment

### Pitfall 4: Allowing Itemized Deductions Without SALT Cap Enforcement
**What goes wrong:** Taxpayer enters $80,000 SALT, software calculates itemized deductions using full amount. Total itemized deductions exceed realistic cap, inflating tax benefit.
**Why it happens:** Itemized deduction calculation skips SALT cap check, or cap is applied as advisory (not enforced).
**How to avoid:**
- SALT cap calculation runs before summing itemized deductions
- Display both raw SALT and capped SALT in breakdown
- UI shows: "SALT paid: $80,000 | Cap: $20,000 | Deduction: $20,000 | Excess: $60,000"
**Warning signs:**
- Itemized deductions include full SALT amount without cap notation
- No separate SALT cap calculation in code
- Test case with high SALT doesn't reduce deduction

### Pitfall 5: Missing Income Phase-Out for High-Income SALT Filers
**What goes wrong:** MFS filer with $400k MAGI claims full $20,000 SALT deduction. IRS requires phase-out: cap reduces from $20k to $5k floor at MAGI $400k.
**Why it happens:** SALT cap calculation ignores MAGI-based phase-out introduced in OBBBA.
**How to avoid:**
- Include MAGI in SALT cap calculation function
- Apply phase-out formula: reduce $0.30 per $1 over threshold
- Test with high-income scenarios (MAGI $250k, $400k, $600k for MFS)
**Warning signs:**
- SALT cap calculation doesn't accept MAGI parameter
- No test cases with MAGI > phase-out threshold
- High-income MFS filers show same SALT deduction as moderate-income filers

## Code Examples

Verified patterns from official sources:

### Deduction Method Coordination Check
```python
# Source: IRS FAQ - Other Deduction Questions
# https://www.irs.gov/faqs/itemized-deductions-standard-deduction/other-deduction-questions

def check_mfs_deduction_coordination(spouse1_id, spouse2_id):
    """
    Verify both MFS spouses use the same deduction method.

    Returns:
        dict: {
            'valid': bool,
            'spouse1_method': str,
            'spouse2_method': str,
            'error': str or None
        }
    """
    spouse1 = Client.query.get(spouse1_id)
    spouse2 = Client.query.get(spouse2_id)

    # Validate both are MFS
    for spouse in [spouse1, spouse2]:
        if spouse.filing_status != 'married_separate':
            return {
                'valid': False,
                'spouse1_method': spouse1.deduction_method,
                'spouse2_method': spouse2.deduction_method,
                'error': f'Deduction coordination only applies to married_separate filing status'
            }

    # Check coordination
    if spouse1.deduction_method != spouse2.deduction_method:
        return {
            'valid': False,
            'spouse1_method': spouse1.deduction_method,
            'spouse2_method': spouse2.deduction_method,
            'error': 'IRS requires both spouses to use the same deduction method (standard or itemized) when filing separately'
        }

    return {
        'valid': True,
        'spouse1_method': spouse1.deduction_method,
        'spouse2_method': spouse2.deduction_method,
        'error': None
    }
```

### Itemized Deduction Calculation with SALT Cap
```python
# Source: IRS Schedule A Instructions
# https://www.irs.gov/instructions/i1040sca

def calculate_itemized_deductions(client_id, tax_year=2026):
    """
    Calculate total itemized deductions with SALT cap enforcement.

    Returns standard deduction if itemized total is lower.
    """
    client = Client.query.get(client_id)

    # Get raw itemized amounts (from ExtractedData or ItemizedDeduction table)
    medical_expenses = get_itemized_amount(client_id, 'medical_expenses', tax_year)
    state_local_taxes_raw = get_itemized_amount(client_id, 'state_local_taxes', tax_year)
    mortgage_interest = get_itemized_amount(client_id, 'mortgage_interest', tax_year)
    charitable = get_itemized_amount(client_id, 'charitable_contributions', tax_year)

    # Calculate MAGI for phase-out
    magi = calculate_magi(client_id, tax_year)

    # Apply SALT cap with income phase-out
    salt_result = calculate_salt_deduction(
        state_local_taxes=state_local_taxes_raw,
        filing_status=client.filing_status,
        magi=magi,
        tax_year=tax_year
    )

    # Medical expenses: only deductible above 7.5% of AGI
    agi = get_agi(client_id, tax_year)
    medical_threshold = agi * 0.075
    medical_deductible = max(0, medical_expenses - medical_threshold)

    # Sum itemized deductions
    total_itemized = (
        medical_deductible +
        salt_result['deduction_allowed'] +
        mortgage_interest +
        charitable
    )

    # Get standard deduction for comparison
    standard_deduction = TaxCalculator.get_standard_deduction(
        filing_status=client.filing_status,
        tax_type='federal',
        tax_year=tax_year
    )

    # Return higher of standard or itemized
    use_itemized = total_itemized > standard_deduction

    return {
        'use_itemized': use_itemized,
        'itemized_total': total_itemized,
        'standard_deduction': standard_deduction,
        'benefit_vs_standard': total_itemized - standard_deduction,
        'breakdown': {
            'medical_expenses': {
                'raw': medical_expenses,
                'threshold': medical_threshold,
                'deductible': medical_deductible
            },
            'state_local_taxes': {
                'raw': state_local_taxes_raw,
                'cap': salt_result['cap_applied'],
                'deductible': salt_result['deduction_allowed'],
                'capped_amount': salt_result['capped_amount']
            },
            'mortgage_interest': mortgage_interest,
            'charitable_contributions': charitable
        }
    }
```

### MFS Joint Analysis with Itemized Path
```python
# Extension to JointAnalysisService.analyze_joint()

def analyze_joint_with_itemized(spouse1_id, spouse2_id, force_refresh=False):
    """
    Extended joint analysis supporting both standard and itemized deductions.

    Enforces REQ-09: Deduction method coordination for MFS
    Enforces REQ-10: SALT cap by filing status
    Enforces REQ-11: Shared expense allocation
    """
    # ... existing validation and cache check ...

    # Step 4.5: Check deduction method coordination
    coordination = check_mfs_deduction_coordination(spouse1_id, spouse2_id)
    if not coordination['valid']:
        raise ValueError(f"Deduction coordination error: {coordination['error']}")

    # Step 5 (modified): Calculate MFJ scenario with deduction choice
    deduction_method = spouse1.deduction_method  # Same for both (coordination enforced)

    if deduction_method == 'itemized':
        # Calculate itemized deductions for MFJ
        mfj_itemized_result = calculate_itemized_deductions_mfj(
            spouse1_id=spouse1_id,
            spouse2_id=spouse2_id,
            tax_year=tax_year
        )

        mfj_deduction = mfj_itemized_result['itemized_total']
        mfj_use_itemized = mfj_itemized_result['use_itemized']
    else:
        # Use standard deduction
        mfj_deduction = TaxCalculator.get_standard_deduction(
            filing_status='married_joint',
            tax_type='federal',
            tax_year=tax_year
        )
        mfj_use_itemized = False

    # ... rest of MFJ calculation with mfj_deduction ...

    # Step 6 (modified): Calculate MFS scenario with itemized deductions
    if deduction_method == 'itemized':
        # Spouse 1 itemized
        spouse1_itemized_result = calculate_itemized_deductions(spouse1_id, tax_year)
        mfs_spouse1_deduction = spouse1_itemized_result['itemized_total']

        # Spouse 2 itemized (must also itemize per coordination rule)
        spouse2_itemized_result = calculate_itemized_deductions(spouse2_id, tax_year)
        mfs_spouse2_deduction = spouse2_itemized_result['itemized_total']
    else:
        # Both use standard
        mfs_std_deduction = TaxCalculator.get_standard_deduction(
            filing_status='married_separate',
            tax_type='federal',
            tax_year=tax_year
        )
        mfs_spouse1_deduction = mfs_std_deduction
        mfs_spouse2_deduction = mfs_std_deduction

    # ... rest of MFS calculation with per-spouse deductions ...

    # Add coordination notes to comparison
    if deduction_method == 'itemized':
        comparison_notes.append({
            'type': 'deduction_coordination',
            'message': 'Both spouses itemizing (required for MFS)',
            'impact': f'Spouse 1 itemized: ${mfs_spouse1_deduction:,.2f} | Spouse 2 itemized: ${mfs_spouse2_deduction:,.2f}'
        })
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SALT cap $10,000 all statuses | SALT cap $40,400 MFJ/Single, $20,000 MFS (2026) | One Big Beautiful Bill Act (2025) | MFS couples in high-tax states see larger deduction, changes MFJ vs MFS comparison significantly |
| No SALT income phase-out | Phase-out above $505k/$250k MAGI to $10k/$5k floor | OBBBA 2025 | High-income filers lose SALT benefit, must factor into itemization decision |
| Manual allocation of joint expenses | Software-assisted allocation with percentage tracking | Industry trend 2020+ | Reduces errors, provides audit trail for IRS |
| Single deduction method per return | Per-spouse deduction method with coordination | Always required, now enforced in software | Prevents IRS rejection, ensures compliance |

**Deprecated/outdated:**
- **TCJA SALT cap ($10k MFJ, $5k MFS):** Superseded by OBBBA for 2025-2029, reverts to $10k/$5k in 2030. Must use year-based lookup.
- **Ignoring income phase-out:** Pre-OBBBA had no phase-out. Post-OBBBA requires MAGI-based reduction for high earners.
- **Assuming equal ownership for all joint property:** IRS requires actual ownership percentage or payment tracking. Default 50/50 only valid for truly joint accounts.

## Open Questions

Things that couldn't be fully resolved:

1. **Community Property States (9 states: AZ, CA, ID, LA, NV, NM, TX, WA, WI)**
   - What we know: These states require 50/50 income splitting for MFS, Form 8958 filing
   - What's unclear: Does ATSA serve clients in community property states? Should Phase 2 include Form 8958 logic?
   - Recommendation: Add feature flag `community_property_state` to Client model, defer Form 8958 to Phase 4 if needed. UI warning if client.address shows community property state.

2. **Medical Expense Allocation for MFS**
   - What we know: Medical expenses deductible above 7.5% AGI threshold
   - What's unclear: IRS rules for allocating joint medical expenses (family health insurance) between MFS spouses
   - Recommendation: Research IRS Publication 502 for medical expense allocation, likely defaults to "who paid" rule like mortgage interest. Phase 2 can use simple allocation, Phase 3+ refine based on payment tracking.

3. **Dependent Allocation Enforcement**
   - What we know: Each child claimed by one parent only on MFS (no splitting)
   - What's unclear: How to model dependent-client relationship for allocation (currently no Dependent model)
   - Recommendation: Add Dependent model in Phase 2 with `claimed_by_client_id` FK, validation prevents same dependent claimed by both spouses. Phase 1 didn't implement dependents at all.

4. **Itemized Deduction Comparison UI**
   - What we know: Need to show standard vs itemized for each filing status (MFJ, MFS spouse 1, MFS spouse 2)
   - What's unclear: Best UI pattern for displaying 6 scenarios (MFJ standard, MFJ itemized, MFS1 standard, MFS1 itemized, MFS2 standard, MFS2 itemized)
   - Recommendation: Display actual deduction method used, show "alternative" in tooltip. Phase 3 (UI phase) handles detailed comparison view.

5. **SALT Cap Reversion in 2030**
   - What we know: OBBBA caps expire 12/31/2029, revert to $10k/$5k
   - What's unclear: Whether ATSA will still be in use in 2030, how to handle multi-year planning
   - Recommendation: Tax year lookup table with caps by year. Add reminder in 2029 to review code for 2030 reversion.

## Sources

### Primary (HIGH confidence)
- [IRS FAQ - Other Deduction Questions](https://www.irs.gov/faqs/itemized-deductions-standard-deduction/other-deduction-questions/other-deduction-questions) - Deduction coordination rule verified
- [IRS Schedule A Instructions](https://www.irs.gov/instructions/i1040sca) - SALT cap, allocation rules
- [IRS 2026 Tax Adjustments Announcement](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill) - Standard deduction amounts
- [IRS FAQ - Real Estate Taxes, Mortgage Interest](https://www.irs.gov/faqs/itemized-deductions-standard-deduction/real-estate-taxes-mortgage-interest-points-other-property-expenses) - Joint expense allocation

### Secondary (MEDIUM confidence)
- [Bipartisan Policy Center - SALT Deduction Changes](https://bipartisanpolicy.org/explainer/salt-deduction-changes-in-the-one-big-beautiful-bill-act/) - OBBBA SALT caps verified with official source
- [TaxAct Blog - SALT Deduction Explained](https://blog.taxact.com/what-is-the-salt-tax-deduction/) - 2026 caps and phase-out thresholds
- [H&R Block - MFS and Itemized Deductions](https://www.hrblock.com/tax-center/filing/adjustments-and-deductions/mortgage-interest-deduction-and-unmarried-couples/) - Allocation examples

### Tertiary (LOW confidence - flagged for validation)
- WebSearch results on tax software validation patterns (no specific implementation guidance found)
- General database design patterns (not tax-domain-specific)

## Metadata

**Confidence breakdown:**
- IRS compliance rules (deduction coordination, SALT caps, allocation): HIGH - Verified with official IRS sources (FAQ, Schedule A instructions)
- OBBBA 2026 SALT cap amounts: HIGH - Multiple sources agree ($40,400 MFJ, $20,000 MFS), cross-referenced with IRS announcement
- Implementation patterns (database schema, service validation): MEDIUM - Based on existing codebase patterns from Phase 1, industry best practices
- Community property state rules: LOW - Mentioned in learnings but not researched in detail for this phase
- UI patterns for itemized vs standard comparison: LOW - Deferred to Phase 3 (UI phase)

**Research date:** 2026-02-04
**Valid until:** 30 days (stable tax rules, but OBBBA implementation details may clarify)

**Critical findings requiring immediate action:**
1. SALT cap for MFS is $20,000 per spouse (2026), NOT $40,400 — this must be enforced to avoid over-stating MFS benefit
2. Deduction method coordination is mandatory, not optional — must block invalid configurations
3. Expense allocation requires tracking (JSON metadata recommended for flexibility)
4. Phase 1 only implemented standard deduction path — itemized path is net-new work

**Gaps to address in planning:**
- No Dependent model exists (needed for REQ-11 if dependent allocation included)
- No ItemizedDeduction model (can use ExtractedData with naming convention for MVP)
- No deduction_method field on Client model (must add)
- JointAnalysisService.analyze_joint() only uses standard deductions (must extend)
