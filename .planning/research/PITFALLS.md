# Domain Pitfalls: Dual-Filer Tax Analysis

**Domain:** Tax analysis software with MFJ vs MFS comparison
**Researched:** 2026-02-04
**Confidence:** HIGH (verified with IRS guidance and tax software documentation)

## Critical Pitfalls

Mistakes that cause rewrites, incorrect tax calculations, or IRS compliance issues.

### Pitfall 1: Itemized Deduction Coordination Violation

**What goes wrong:** Software allows one spouse to itemize deductions while the other claims the standard deduction when filing separately. This violates IRS rules and causes automatic rejection.

**Why it happens:**
- Treating MFS filers as completely independent returns
- No validation logic checking spouse's deduction choice
- UI allows selecting itemized/standard per spouse without coordination

**Consequences:**
- IRS rejection of tax return
- Incorrect tax liability calculations
- Client loses trust in analysis accuracy
- Manual recalculation of both returns required

**Prevention:**
- Add database constraint: when filing_status='married_separate' AND spouse_id IS NOT NULL, both must use same deduction_type
- UI validation: if spouse selects itemized, lock the other spouse to itemized (show warning message)
- Analysis engine: check deduction coordination before any calculation

**Detection (warning signs):**
- MFS comparison shows dramatically different deduction types
- One spouse showing standard deduction, other showing itemized
- Total deductions seem too high when summing both MFS returns

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

---

### Pitfall 2: Income Attribution in Community Property States

**What goes wrong:** Software treats all income as earned by the spouse who received the W-2/1099, ignoring community property state rules that require 50/50 income splitting for MFS filers.

**Why it happens:**
- Assuming W-2 recipient owns 100% of wages
- Not implementing Form 8958 allocation logic
- No state-specific conditional logic for community property rules
- Nine community property states (AZ, CA, ID, LA, NV, NM, TX, WA, WI) have special rules

**Consequences:**
- Incorrect taxable income calculations for both spouses
- Missed tax savings opportunities (different marginal rates)
- IRS notices for misreported income
- Non-compliance with state-specific allocation requirements

**Prevention:**
- Add `community_property_state` boolean field to Client model or derive from address
- Implement Form 8958 allocation logic: split community income 50/50 for MFS
- Create separate income attribution service that applies state-specific rules
- Show allocation breakdown in UI: "Husband's income: $X (includes $Y of wife's community income)"

**Detection (warning signs):**
- Client address is in AZ, CA, ID, LA, NV, NM, TX, WA, or WI
- MFS analysis shows vastly different income levels when both spouses work
- One spouse showing zero income despite both working

**Phase to address:** Phase 2 (MFS-Specific Logic) or flag as "needs deeper research"

**Sources:**
- [TurboTax: Five Tax Tips for Community Property States](https://turbotax.intuit.com/tax-tips/marriage/five-tax-tips-for-community-property-states/L4jG7cq7Z)
- [IRS Publication 555: Community Property](https://www.irs.gov/publications/p555)
- [TurboTax: Form 8958 Allocation](https://turbotax.intuit.com/tax-tips/marriage/what-is-form-8958-allocation-of-tax-amounts-between-certain-individuals-in-community-property-state/L2281euHh)

---

### Pitfall 3: Credit Disqualification for MFS Not Enforced

**What goes wrong:** Software calculates credits (EITC, student loan interest deduction, adoption credit, education credits) for MFS filers when they're completely ineligible, creating phantom tax savings.

**Why it happens:**
- Credit calculation logic doesn't check filing status
- Assuming all credits are available to all filing statuses
- Copy-paste from MFJ logic without adjusting for MFS restrictions

**Consequences:**
- Overstated tax savings in MFS scenario
- Recommendation to file separately when joint is actually better
- IRS rejection when return is filed
- Loss of legitimate credits when chosen filing status makes them unavailable

**Prevention:**
- Create filing status eligibility matrix for each credit:
  - EITC: MFS = ineligible (exception: living apart 6+ months with qualifying child)
  - Student loan interest: MFS = completely ineligible (no phase-out, just $0)
  - Adoption credit: MFS = uses different phase-out ranges
  - Education credits (AOTC, LLC): MFS = ineligible
  - Child and Dependent Care Credit: MFS = ineligible (with exceptions)
  - Premium Tax Credit (ACA): MFS = ineligible, must repay full subsidy
- Add `filing_status_eligible` check before applying any credit
- UI: show grayed-out/disabled credits for MFS with tooltip explaining why unavailable

**Detection (warning signs):**
- MFS scenario showing EITC or student loan deduction
- MFS total credits appear similar to MFJ credits
- Education credits appearing for married filing separately taxpayers

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Credit-specific thresholds for 2026:**
- Student loan interest: MFS = $0 (not phased out, just ineligible)
- EITC: MFS = ineligible unless living apart 6+ months
- Adoption credit phase-out: $265,080-$305,080 (adjust for MFS if different)
- Premium Tax Credit: MFS = ineligible, full repayment required

**Sources:**
- [IRS: Student Loan Interest Deduction](https://www.irs.gov/taxtopics/tc456)
- [SmartAsset: Student Loan Interest Deduction 2026](https://smartasset.com/taxes/student-loan-interest-deduction)
- [IRS: Who Qualifies for EITC](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc)
- [IRS: Premium Tax Credit](https://www.irs.gov/affordable-care-act/individuals-and-families/premium-tax-credit-claiming-the-credit-and-reconciling-advance-credit-payments)

---

### Pitfall 4: QBI Deduction Threshold Confusion Between MFJ and MFS

**What goes wrong:** Using married joint QBI thresholds ($383,900-$533,900) for married filing separately returns. MFS uses single filer thresholds ($191,950-$266,950), causing incorrect QBI deduction calculations.

**Why it happens:**
- Copying QBI logic without adjusting thresholds by filing status
- Assuming "married" means using married thresholds regardless of joint/separate
- QBI phase-in logic hardcoded to one set of thresholds

**Consequences:**
- MFS taxpayers get double the QBI deduction they should (using $383k threshold instead of $191k)
- Overstated tax savings in MFS comparison
- Recommending MFS when it's actually worse
- For real use case (husband LLC $250k): would incorrectly show full QBI deduction when it should be phased out

**Prevention:**
- Threshold lookup by filing status in QBI calculation:
  ```python
  QBI_THRESHOLDS = {
      'single': {'phase_in_start': 191950, 'phase_in_end': 266950},
      'married_joint': {'phase_in_start': 383900, 'phase_in_end': 533900},
      'married_separate': {'phase_in_start': 191950, 'phase_in_end': 266950},  # SAME as single
      'head_of_household': {'phase_in_start': 191950, 'phase_in_end': 266950}
  }
  ```
- Test case: husband with $250k LLC income filing separately should show reduced QBI deduction
- Show QBI phase-out status in analysis: "QBI limited due to income above $191,950 threshold (MFS)"

**Detection (warning signs):**
- MFS QBI deduction seems too high for income level
- Phase-out not triggering between $191k-$266k for MFS filers
- Comparison shows MFS with same QBI as MFJ despite different thresholds

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Sources:**
- [Millan CPA: 2026 Business & Pass-Through Tax Rules](https://millancpa.com/insights/2026-irs-tax-rules-for-llcs-s-corps-partnerships)
- Existing codebase: services/tax_strategies.py lines 29-35 (already has correct thresholds, just ensure they're used)

---

### Pitfall 5: Analysis Cache Invalidation for Dual-Filer Scenarios

**What goes wrong:** Husband's analysis is cached with data_version_hash. Wife's data changes. System doesn't know joint analysis is now stale. Displays outdated joint tax liability.

**Why it happens:**
- Cache invalidation only checks current client's ExtractedData timestamps
- Doesn't include spouse's data in hash calculation
- Joint analysis cached separately but not invalidated when either spouse's data changes

**Consequences:**
- Tax professional sees stale joint analysis after updating one spouse's W-2
- MFJ vs MFS comparison uses old data
- Client decisions based on outdated calculations
- "Why did the number change when I refreshed?" support questions

**Prevention:**
- Modify `_calculate_data_version_hash()` to include spouse data when spouse_id exists:
  ```python
  def _calculate_data_version_hash(client_id):
      extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()

      # CRITICAL: Include spouse data if spouse linked
      client = Client.query.get(client_id)
      if client.spouse_id:
          spouse_data = ExtractedData.query.filter_by(client_id=client.spouse_id).all()
          extracted_data.extend(spouse_data)

      # ... rest of hash calculation
  ```
- Bidirectional invalidation: changing either spouse invalidates both individual AND joint analyses
- UI: show "last analyzed" timestamp on joint view, warning if stale

**Detection (warning signs):**
- Joint analysis timestamp older than individual spouse data updates
- Refreshing page shows different numbers without data changes
- One spouse's data updated but joint analysis unchanged

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Technical note:** Already uses hash-based caching (analysis_engine.py lines 14-35), just extend to include spouse data.

---

### Pitfall 6: SQLite Concurrency Issues During Joint Analysis

**What goes wrong:** User triggers joint analysis for husband. System reads husband's data, calculates, starts writing. Meanwhile, user updates wife's W-2 in another tab. SQLite locks database. First analysis write blocks second update, causing "database is locked" error.

**Why it happens:**
- SQLite allows unlimited readers but only one writer at a time
- Joint analysis = long-running calculation + database writes
- Dual-filer scenario doubles the likelihood of concurrent writes
- Flask with multiple workers can spawn concurrent requests

**Consequences:**
- `sqlite3.OperationalError: database is locked`
- Analysis request fails, user sees error page
- Data corruption if transaction partially commits
- User forced to retry, creating poor UX

**Prevention:**
- Enable SQLite WAL (Write-Ahead Logging) mode:
  ```python
  # In database/init_db.py or app.py
  db.session.execute(text("PRAGMA journal_mode=WAL"))
  db.session.execute(text("PRAGMA busy_timeout=30000"))  # 30 second timeout
  ```
- Keep analysis transactions as short as possible: read data first, calculate outside transaction, write results in single commit
- Use optimistic locking: check data version before writing analysis results
- UI: disable "analyze" button while analysis in progress (client-side)
- Consider PostgreSQL migration if concurrency becomes persistent issue

**Detection (warning signs):**
- Intermittent "database is locked" errors in logs
- Errors increase with simultaneous analysis of both spouses
- Errors disappear when using single-threaded Flask mode
- Lock timeouts during document upload + analysis

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic) - add WAL mode immediately

**Sources:**
- [Stack Overflow: Flask SQLite Threading Issues](https://sqlpey.com/python/solved-how-to-handle-sqlite-threading-issues-in-flask/)
- [GitHub: SQLAlchemy Concurrent Sessions](https://gist.github.com/dittos/6396622)
- [SkyPilot: SQLite Concurrency](https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/)

---

### Pitfall 7: Retirement Contribution Phase-Out Calculation Errors for MFS

**What goes wrong:** Software applies incorrect phase-out ranges for IRA deductibility and Roth IRA contributions when filing separately. MFS has extremely narrow phase-out range ($0-$10,000 MAGI), not the broader ranges for other statuses.

**Why it happens:**
- Assuming MFS phase-out is half of MFJ (it's not)
- Using same calculation logic for all filing statuses
- Not implementing special MFS rules (essentially designed to discourage MFS)

**Consequences:**
- MFS filers shown as eligible for traditional IRA deduction when they're not
- Roth IRA contribution shown as allowed when above $10k MAGI (should be $0)
- Tax strategy recommendations suggest IRAs when they're not viable for MFS
- Real use case: wife with $100k W-2 filing separately would be completely ineligible for Roth IRA

**Prevention:**
- Implement filing-status-specific phase-out ranges:
  ```
  Traditional IRA deductibility (2026, if covered by workplace plan):
  - Single: $81,000 - $91,000
  - MFJ: $129,000 - $149,000
  - MFS: $0 - $10,000 (WARNING: essentially zero tolerance)

  Roth IRA contribution (2026):
  - Single: $153,000 - $168,000
  - MFJ: $242,000 - $252,000
  - MFS: $0 - $10,000 (ineligible above $10k)
  ```
- Add warning in UI: "Married filing separately has very limited retirement contribution options"
- Show why MFJ is better: "Filing jointly would restore $242k-$252k Roth IRA eligibility"

**Detection (warning signs):**
- MFS scenario shows IRA/Roth contributions when MAGI > $10,000
- Retirement strategy recommendations identical for MFJ and MFS
- No warnings about MFS retirement contribution limitations

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Sources:**
- [IRS: 401(k) and IRA Limits for 2026](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500)
- [Henssler Financial: 2026 IRA and Retirement Plan Limits](https://www.henssler.com/2026-ira-and-retirement-plan-limits/)
- [Fidelity: IRA Contribution Limits 2026](https://www.fidelity.com/learning-center/smart-money/ira-contribution-limits)

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or require rework but don't break core functionality.

### Pitfall 8: AMT Exemption Halving Not Applied for MFS

**What goes wrong:** Using full MFJ AMT exemption amount ($140,200) for married filing separately instead of exactly half ($70,100).

**Why it happens:**
- Looking up AMT exemption by "married" keyword without checking joint vs separate
- Assuming exemption amounts scale proportionally (they do for AMT, but not for everything)

**Consequences:**
- MFS taxpayers shown with double the AMT exemption they're entitled to
- Incorrect AMT calculations showing lower alternative tax than reality
- Missing AMT liability when it should apply
- For high-income MFS filers: significantly underestimated tax liability

**Prevention:**
- AMT exemption lookup by exact filing status:
  ```
  2026 AMT Exemption:
  - Single: $70,100
  - MFJ: $140,200
  - MFS: $70,100 (exactly half of MFJ)

  2026 AMT Phase-out:
  - Single: $500,000 - $680,200
  - MFJ: $1,000,000 - $1,360,400
  - MFS: $500,000 - $680,200 (same as single)
  ```
- Test case: high-income MFS filer should trigger AMT at half the joint threshold
- Note OBBBA changes: exemption phase-out thresholds returned to lower 2018 levels in 2026

**Detection (warning signs):**
- MFS AMT exemption showing $140k instead of $70k
- AMT not triggering for high-income MFS when it should
- Phase-out range incorrect for MFS filers

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic) or Phase 2 (MFS-Specific Logic)

**Sources:**
- [IRS: 2026 Tax Inflation Adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill)
- [SmartAsset: AMT Rules for 2026](https://smartasset.com/taxes/amt-tax-brackets)
- [Millan CPA: 2026 IRS Tax Brackets with AMT](https://millancpa.com/insights/2026-irs-tax-brackets-standard-deductions-capital-gains-amt)

---

### Pitfall 9: Premium Tax Credit (ACA) Not Handled for MFS

**What goes wrong:** Software doesn't flag that MFS filers with advance premium tax credits must repay the ENTIRE subsidy, not just the excess. This is a 2026-specific change (no repayment cap after 2025).

**Why it happens:**
- Not tracking ACA subsidies in extracted data
- No Form 1095-A parsing or premium tax credit reconciliation
- Unaware of 2026 rule change (full repayment, no cap)

**Consequences:**
- MFS comparison shows savings, but doesn't account for $X,000 ACA repayment
- Client chooses MFS, gets massive surprise tax bill from subsidy repayment
- Recommendation is financially devastating instead of helpful

**Prevention:**
- Add ACA subsidy tracking: parse Form 1095-A if uploaded
- Calculate Premium Tax Credit repayment for MFS scenarios:
  - MFS = ineligible for PTC
  - Must repay full advance payment (2026+: no cap)
- Show warning in UI: "⚠️ Filing separately requires repaying $X,XXX in ACA subsidies"
- Include repayment in MFS total tax calculation
- Flag in comparison: "MFJ saves $X,XXX by avoiding ACA subsidy repayment"

**Detection (warning signs):**
- Client has health insurance through marketplace (Form 1095-A)
- MFS tax liability seems too low given income level
- No mention of premium tax credit in analysis

**Phase to address:** Phase 2 (MFS-Specific Logic) or flag as "out of scope for MVP"

**Sources:**
- [IRS: Premium Tax Credit FAQ](https://www.irs.gov/affordable-care-act/individuals-and-families/questions-and-answers-on-the-premium-tax-credit)
- [HealthCare.gov: How to Reconcile Premium Tax Credit](https://www.healthcare.gov/taxes-reconciling/)
- [Western CPE: IRS Premium Tax Credit FAQ Update 2026](https://www.westerncpe.com/taxbyte/irs-premium-tax-credit-faq-update-what-to-know-for-2026/)

---

### Pitfall 10: Dependent Allocation Without Form 8332 Validation

**What goes wrong:** Software allows splitting dependents between spouses when filing separately without enforcing that only one parent can claim each child. IRS rule: "An individual may be a dependent of only one taxpayer."

**Why it happens:**
- Treating dependents as independently claimable by each spouse
- No validation that dependents don't overlap
- Missing custodial parent determination logic

**Consequences:**
- Both spouses claim same child on MFS returns
- IRS rejects one or both returns
- Processing delays while IRS determines which parent has priority
- Missed Child Tax Credit optimization (could give all to higher-income spouse if beneficial)

**Prevention:**
- Dependent model: add `claimed_by_client_id` field (nullable, FK to clients)
- UI: when selecting MFS, show dependent allocation screen
  - "Assign each dependent to husband OR wife (cannot split)"
- Validation: each dependent can only be claimed_by one spouse when filing separately
- Support Form 8332: allow custodial parent to release exemption to noncustodial parent
  - Add `form_8332_signed` boolean to dependent record
- Show impact: "Assigning both children to husband increases his Child Tax Credit by $X,XXX"

**Detection (warning signs):**
- Same dependent appearing in both spouses' MFS returns
- Total dependents in MFS > total dependents in MFJ
- Child Tax Credit appears for both spouses for same child

**Phase to address:** Phase 2 (MFS-Specific Logic) - requires dependent tracking feature

**Sources:**
- [IRS: Claiming a Child as Dependent When Parents Are Divorced, Separated or Live Apart](https://www.irs.gov/newsroom/claiming-a-child-as-a-dependent-when-parents-are-divorced-separated-or-live-apart)
- [IRS: Divorced and Separated Parents](https://www.irs.gov/tax-professionals/eitc-central/divorced-and-separated-parents)
- [IRS Publication 504: Divorced or Separated Individuals](https://www.irs.gov/publications/p504)

---

### Pitfall 11: SALT Cap Halving for MFS Not Applied

**What goes wrong:** Applying the $40,000 SALT cap (State and Local Tax deduction) to each MFS spouse instead of $20,000 per spouse. This is a special MFS rule where the cap is exactly half.

**Why it happens:**
- SALT cap increased from $10,000 to $40,000 under OBBBA for 2026
- Not aware that MFS cap is $20,000 (half of joint cap)
- Assuming each spouse gets full standard cap

**Consequences:**
- MFS itemized deductions overstated by up to $20,000 per spouse
- Total MFS tax liability appears lower than it actually is
- Recommending MFS when MFJ is actually better
- For high-tax states (CA, NY, NJ): this error is material

**Prevention:**
- SALT cap by filing status:
  ```
  2026 SALT Cap:
  - Single: $40,000
  - MFJ: $40,000
  - MFS: $20,000 (half of joint, not full)
  - HOH: $40,000
  ```
- Cap enforcement in itemized deduction calculation
- Show SALT breakdown in analysis: "State income tax: $X, Property tax: $Y, Capped at: $20,000 (MFS)"

**Detection (warning signs):**
- MFS itemized deductions showing $40k SALT deduction per spouse
- Total MFS SALT deductions > $40k (combined)
- No warning about MFS SALT cap reduction

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Sources:**
- [Millan CPA: 2026 Business & Pass-Through Tax Rules](https://millancpa.com/insights/2026-irs-tax-rules-for-llcs-s-corps-partnerships)
- [SmartAsset: Married Filing Separately 2026](https://smartasset.com/taxes/married-filing-jointly-vs-separately)

---

### Pitfall 12: HSA Contribution Limit Not Split for MFS with Family Coverage

**What goes wrong:** Allowing each MFS spouse with family HDHP coverage to contribute the full $8,750 family limit ($17,500 combined) instead of splitting one $8,750 limit between them.

**Why it happens:**
- Assuming MFS = completely separate tax treatment
- Not recognizing IRS treats married couples as single tax unit for HSA purposes
- No validation of combined HSA contributions across spouses

**Consequences:**
- Overstated HSA deduction for MFS scenario
- Excess contribution penalties if actually implemented
- MFS appears more favorable than it is

**Prevention:**
- HSA contribution rules by coverage and filing status:
  ```
  2026 HSA Limits:
  - Self-only coverage: $4,400 per person
  - Family coverage (MFJ): $8,750 total
  - Family coverage (MFS): $8,750 total (SPLIT between spouses, not each)
  - Catch-up (55+): +$1,000
  ```
- Track combined HSA contributions when spouse_id exists and either has family coverage
- UI warning: "You and your spouse must share the $8,750 family HSA limit when filing separately"
- Show allocation: "Husband contributes: $5,000, Wife contributes: $3,750, Combined: $8,750 (limit)"

**Detection (warning signs):**
- Both MFS spouses showing $8,750 HSA contribution with family coverage
- Combined HSA deduction > $8,750 for married couple
- No HSA contribution coordination check

**Phase to address:** Phase 2 (MFS-Specific Logic) or flag as "needs research"

**Sources:**
- [Ascensus: How HSA Contributions Can Be Split Between Family Members](https://thelink.ascensus.com/articles/2025/5/12/how-can-hsa-contributions-be-split-between-family-members)
- [Fidelity: HSA Contribution Limits 2026](https://www.fidelity.com/learning-center/smart-money/hsa-contribution-limits)
- [SHRM: IRS Announces 2026 HSA Limits](https://www.shrm.org/topics-tools/news/benefits-compensation/irs-announces-2026-hsa-hdhp-limits)

---

## Minor Pitfalls

Mistakes that cause annoyance, confusion, or cosmetic issues but are easily fixable.

### Pitfall 13: Rounding Discrepancies Between Individual and Joint Calculations

**What goes wrong:** Calculating husband's tax: $X.47 → rounds to $X. Wife's tax: $Y.52 → rounds to $Y+1. Individual sum: $X + $Y + 1. But joint calculation: combines income first, then calculates, rounds differently. Off by $1-3.

**Why it happens:**
- Rounding at different stages of calculation
- IRS rule: "Round off cents to whole dollars" but "include cents when adding amounts and round off only the total"
- Premature rounding in individual calculations

**Consequences:**
- Penny discrepancies between sum(individual) and joint calculation
- "Why don't the numbers add up?" questions from users
- Looks like calculation error even though both are correct
- Minor confusion, but doesn't affect IRS acceptance (IRS allows minor rounding differences)

**Prevention:**
- Use `Decimal` type throughout calculations (already using in tax_calculator.py)
- Round only at final display step, never mid-calculation
- For comparisons: calculate MFJ fresh (don't sum two MFS calculations)
- Show rounding note: "* Amounts rounded to nearest dollar per IRS guidelines"
- Test case: verify sum(MFS) ≈ MFJ within $5 (acceptable variance)

**Detection (warning signs):**
- MFS total tax = $45,237, MFJ total tax = $45,240 (should be much larger difference)
- Penny differences in displayed amounts
- Inconsistent rounding between related calculations

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic)

**Sources:**
- [IRS: Rounding to Nearest Dollar on Returns](https://claimyr.com/government-services/irs/How-does-the-IRS-view-rounding-to-the-nearest-dollar-when-filing-tax-returns/2025-04-11)
- [Bogleheads: Whole Dollar Rounding on Tax Forms](https://www.bogleheads.org/forum/viewtopic.php?t=111262)

---

### Pitfall 14: Filing Status Display Confusion (married_joint vs married_separate vs single)

**What goes wrong:** Database stores `filing_status='married_joint'` but UI displays "Married" without clarifying joint vs separate. User selects "Married" dropdown thinking it means their marital status, not their filing status choice.

**Why it happens:**
- Conflating marital status (married/single) with filing status (MFJ/MFS/Single/HOH)
- UI labels not clear about filing status vs marital status
- dropdown shows "Married" instead of "Married Filing Jointly"

**Consequences:**
- User confusion about what they're selecting
- Client model stores `filing_status='married_joint'` when they meant to explore separate
- UI must support changing filing status for comparison, but terminology is unclear

**Prevention:**
- Clear UI labels:
  - NOT: "Filing Status: Married"
  - YES: "Filing Status: Married Filing Jointly (MFJ)"
  - YES: "Filing Status: Married Filing Separately (MFS)"
- Add help text: "Choose how you want to file your taxes (this affects tax brackets and credits)"
- For dual-filer view: show both options side-by-side with clear comparison
- Consistent terminology in code:
  ```python
  FILING_STATUS_CHOICES = {
      'single': 'Single',
      'married_joint': 'Married Filing Jointly (MFJ)',
      'married_separate': 'Married Filing Separately (MFS)',
      'head_of_household': 'Head of Household',
      'qualifying_widow': 'Qualifying Surviving Spouse'
  }
  ```

**Detection (warning signs):**
- User asks "Why can't I just select 'married'?"
- UI shows ambiguous labels like "Married" without qualifier
- Client model has `filing_status='married_joint'` but no conscious selection was made

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic) - UI clarity

---

### Pitfall 15: Standard Deduction Display Not Showing MFS Reduction

**What goes wrong:** UI shows standard deduction without explaining that MFS gets exactly half of MFJ ($16,100 vs $32,200 for 2026).

**Why it happens:**
- Displaying deduction amount without context
- Not highlighting the MFS "penalty" (each spouse gets half, not full)
- Missing comparison to show cost of filing separately

**Consequences:**
- User doesn't understand why MFS standard deduction seems "low"
- Doesn't see the immediate cost of MFS vs MFJ
- Misses key insight: "Filing separately cuts your standard deduction in half"

**Prevention:**
- Show standard deduction with filing status context:
  ```
  Standard Deduction:
  - MFJ: $32,200
  - MFS: $16,100 each (⚠️ Half of joint amount)
  - Single: $16,100
  ```
- In comparison view, highlight:
  - "MFJ Standard Deduction: $32,200"
  - "MFS Standard Deduction (combined): $32,200 ($16,100 each)"
  - "Impact: $0 difference if both take standard"
- Tooltip: "Married filing separately receives half the standard deduction of joint filers"

**Detection (warning signs):**
- UI shows "$16,100" for MFS without explanation
- No comparison to MFJ standard deduction
- User confused why deduction is "only" $16k

**Phase to address:** Phase 1 (Core MFJ/MFS Calculation Logic) - UI improvement

---

## Phase-Specific Warnings

Phases that need special attention based on pitfall clustering.

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Phase 1: Core MFJ/MFS Calculation | Pitfalls 1, 3, 4, 5, 6, 7, 11, 13, 14, 15 | Build filing-status-aware calculation engine from the start. Test with real 2026 tax scenarios (LLC + W-2). Enable SQLite WAL immediately. Create comprehensive test cases for all credits/thresholds. |
| Phase 2: MFS-Specific Logic | Pitfalls 2, 8, 9, 10, 12 | Flag these as "needs deeper research" during planning. Community property states require Form 8958 logic. ACA subsidy repayment is 2026-specific. HSA and dependent allocation are complex edge cases. |
| Phase 3: Split-Screen UI | Pitfall 14, 15 | Focus on clarity over brevity. Show filing status implications explicitly. Use tooltips and help text liberally. |
| Phase 4: Joint Analysis Engine | Pitfall 5 | Cache invalidation must be bidirectional. Hash calculation includes both spouses' data. Test concurrent updates extensively. |

---

## Technology-Specific Warnings

### Flask + SQLite Stack

**Concurrency Risk (Pitfall 6):** SQLite is single-writer. Dual-filer analysis doubles write contention. Enable WAL mode immediately:

```python
# In database/init_db.py or app.py
from sqlalchemy import text
db.session.execute(text("PRAGMA journal_mode=WAL"))
db.session.execute(text("PRAGMA busy_timeout=30000"))
```

**Migration Path:** If concurrency issues persist, consider PostgreSQL. But WAL mode + short transactions should handle single tax professional use case.

### Existing Analysis Caching

**Cache Invalidation (Pitfall 5):** Current implementation hashes timestamps of ExtractedData for one client. Must extend to include spouse:

```python
# In services/analysis_engine.py, modify _calculate_data_version_hash()
def _calculate_data_version_hash(client_id):
    extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()

    # Include spouse data if linked
    client = Client.query.get(client_id)
    if client.spouse_id:
        spouse_data = ExtractedData.query.filter_by(client_id=client.spouse_id).all()
        extracted_data.extend(spouse_data)

    # Continue with existing hash logic
    # ...
```

### Existing Tax Calculator

**Good News:** `services/tax_calculator.py` already handles all filing statuses and bracket lookups. QBI thresholds in `services/tax_strategies.py` already correct.

**Action Items:**
- Verify credit eligibility checks use filing_status (Pitfall 3)
- Verify retirement phase-out uses correct MFS ranges (Pitfall 7)
- Add SALT cap enforcement for MFS (Pitfall 11)
- Add AMT exemption lookup for MFS (Pitfall 8)

---

## Testing Strategy to Catch Pitfalls

### Test Scenario 1: Real Use Case (LLC + W-2)

**Setup:**
- Husband: LLC with $250k QBI, self-employment tax, retirement contributions
- Wife: W-2 with $100k, standard withholding
- State: California (high SALT, test cap)
- Filing statuses: MFJ and MFS

**Expected Results:**
- MFJ: Combined income $350k, joint brackets, full QBI deduction (below $383k threshold)
- MFS: Each calculates separately
  - Husband: QBI reduced (above $191k threshold) ← Pitfall 4
  - Wife: No special deductions
  - Combined tax significantly higher than MFJ
  - SALT capped at $20k each ← Pitfall 11
  - Student loan interest deduction: $0 (ineligible) ← Pitfall 3
- MFJ should save $X,XXX vs MFS (quantify the marriage penalty/bonus)

**Pitfalls This Catches:** 1, 3, 4, 7, 11, 13

### Test Scenario 2: Community Property State (Texas)

**Setup:**
- Husband: W-2 $150k
- Wife: W-2 $80k
- State: Texas (community property)
- Filing status: MFS

**Expected Results:**
- Income attribution: Each reports 50% of combined income ($115k each)
- NOT: Husband reports $150k, wife reports $80k
- Form 8958 allocation shown in analysis

**Pitfalls This Catches:** 2

### Test Scenario 3: Credit Eligibility

**Setup:**
- Husband: $60k income, student loans
- Wife: $40k income, dependent child
- Filing status: MFS

**Expected Results:**
- Student loan interest deduction: $0 (ineligible for MFS) ← Pitfall 3
- EITC: $0 (ineligible for MFS unless living apart) ← Pitfall 3
- Child tax credit: Only one spouse can claim ← Pitfall 10
- Comparison shows MFJ makes these credits available

**Pitfalls This Catches:** 3, 10

### Test Scenario 4: Concurrent Updates

**Setup:**
- Open analysis for husband in browser tab 1
- Open analysis for wife in browser tab 2
- Tab 1: Upload new W-2 for husband
- Tab 2: Simultaneously trigger analysis for wife
- Tab 1: Trigger joint analysis

**Expected Results:**
- No "database is locked" errors ← Pitfall 6
- Joint analysis reflects husband's new W-2 ← Pitfall 5
- All writes complete successfully

**Pitfalls This Catches:** 5, 6

---

## Summary: Top 5 Critical Pitfalls to Address First

1. **Itemized Deduction Coordination (Pitfall 1):** Will cause IRS rejection if not enforced
2. **Credit Disqualification (Pitfall 3):** Creates phantom tax savings, wrong recommendations
3. **QBI Threshold Confusion (Pitfall 4):** Directly affects real use case (husband with $250k LLC)
4. **Cache Invalidation (Pitfall 5):** Stale data in joint analysis breaks trust
5. **SQLite Concurrency (Pitfall 6):** Blocking errors hurt UX, enable WAL immediately

Address these in Phase 1. Flag community property (Pitfall 2) and ACA subsidies (Pitfall 9) for Phase 2 or "needs deeper research."

---

## Confidence Assessment

| Pitfall Category | Confidence | Source Quality |
|------------------|------------|----------------|
| Credit eligibility rules | HIGH | IRS official guidance |
| Phase-out thresholds (2026) | HIGH | IRS published adjustments |
| Filing status restrictions | HIGH | IRS publications, tax software docs |
| Community property rules | MEDIUM | TurboTax/IRS guidance, needs state-specific validation |
| Technical (SQLite, caching) | HIGH | Flask/SQLAlchemy documentation, developer forums |
| Rounding rules | MEDIUM | IRS guidance exists, but implementation varies |

**Overall confidence: HIGH** for tax calculation pitfalls, **MEDIUM-HIGH** for technical implementation pitfalls.

---

## Sources Summary

**IRS Official:**
- [IRS: 2026 Tax Inflation Adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill)
- [IRS: 401(k) and IRA Limits 2026](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500)
- [IRS: Who Qualifies for EITC](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc)
- [IRS: Student Loan Interest Deduction](https://www.irs.gov/taxtopics/tc456)
- [IRS: Premium Tax Credit](https://www.irs.gov/affordable-care-act/individuals-and-families/premium-tax-credit-claiming-the-credit-and-reconciling-advance-credit-payments)
- [IRS Publication 555: Community Property](https://www.irs.gov/publications/p555)
- [IRS: Claiming a Child When Divorced/Separated](https://www.irs.gov/newsroom/claiming-a-child-as-a-dependent-when-parents-are-divorced-separated-or-live-apart)

**Tax Professional Resources:**
- [Millan CPA: 2026 Tax Rules](https://millancpa.com/insights/2026-irs-tax-brackets-standard-deductions-capital-gains-amt)
- [SmartAsset: MFJ vs MFS](https://smartasset.com/taxes/married-filing-jointly-vs-separately)
- [Fidelity: HSA Limits 2026](https://www.fidelity.com/learning-center/smart-money/hsa-contribution-limits)
- [TurboTax: Community Property States](https://turbotax.intuit.com/tax-tips/marriage/five-tax-tips-for-community-property-states/L4jG7cq7Z)

**Technical Implementation:**
- [Flask SQLAlchemy + SQLite Threading](https://sqlpey.com/python/solved-how-to-handle-sqlite-threading-issues-in-flask/)
- [SQLite Concurrency Best Practices](https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/)

---

**Research complete. Ready for roadmap creation.**
