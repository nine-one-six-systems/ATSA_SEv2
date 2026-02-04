# Project Learnings

Document discoveries, patterns, and anti-patterns encountered during development. This is a living document updated throughout the project lifecycle.

## Technical Discoveries

### Stack Decisions

**Using Vanilla JavaScript + Proxy Pattern for State Management**
- **Discovery:** Modern ES6+ Proxy enables reactive state without libraries (80% smaller than Redux)
- **Context:** Dual-filer feature needs state synchronization between husband form, wife form, and comparison view
- **Pattern:** Proxy-based reactive state with observer/pub-sub for loose coupling
- **Why it works:** No external dependencies, consistent with existing architecture, production-ready in 2026
- **Source:** [State Management in Vanilla JS 2026 Trends](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de)

**Split.js for Resizable Split Panes**
- **Discovery:** Lightweight (2kb) vanilla JS library provides resizable split-screen without framework overhead
- **Context:** Need side-by-side spouse view with draggable divider
- **Alternative considered:** React/Vue components (100kb+ bundle, adds build complexity)
- **Why Split.js wins:** Works with existing vanilla JS, no dependencies, 50x smaller than framework approach
- **Installation:** CDN or npm, supports horizontal/vertical splits, configurable gutters

**CSS Grid for Macro Layout + Flexbox for Micro Layout**
- **Discovery:** 2026 best practice is Grid for page structure, Flexbox for component alignment
- **Context:** Split-screen layout needs responsive column structure with internal component alignment
- **Mental model:** Grid = skeleton (husband column, wife column), Flexbox = muscles (align elements within columns)
- **Browser support:** Universal in 2026 (IE11 dead, Edge uses Chromium)

### Architecture Insights

**Service Layer Orchestration Pattern for Joint Analysis**
- **Discovery:** New `JointAnalysisService` orchestrates existing components without modifying them
- **Context:** Need to combine two individual analyses + joint calculations without rewriting tax engine
- **Pattern:** Service coordinates `AnalysisEngine` (2 calls) + `TaxCalculator` (MFJ/MFS scenarios) + caching
- **Why it works:** Preserves existing code, clear separation of concerns, testable in isolation
- **Anti-pattern avoided:** Inline joint calculation in routes (violates MVC, untestable)

**Bidirectional Cache Invalidation for Linked Data**
- **Discovery:** When spouse data changes, both individual AND joint analyses must refresh
- **Context:** Joint analysis hash must combine both spouses' data version hashes
- **Implementation:** `sha256(spouse1_hash + '|' + spouse2_hash + '|' + filing_status)`
- **Critical insight:** Changing either spouse invalidates joint analysis, prevents stale data
- **Pattern:** Extend existing `_calculate_data_version_hash()` to include spouse when `spouse_id` exists

**SQLite WAL Mode for Dual-Writer Concurrency**
- **Discovery:** SQLite WAL (Write-Ahead Logging) enables concurrent reads + writes, prevents "database locked" errors
- **Context:** Dual-filer analysis = 2x write frequency, single-writer bottleneck
- **Solution:** `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=30000` (30 seconds)
- **Result:** Unlimited readers, multiple writers with short transactions work without blocking
- **When to migrate to PostgreSQL:** If WAL + short transactions still show lock contention

### Tax Compliance Insights

**SALT Cap Varies by Filing Status AND Year**
- **Discovery:** One Big Beautiful Bill Act (OBBBA) changes SALT cap for 2025-2029, then reverts in 2030
- **Context:** Phase 2 research for MFS compliance revealed complex year-based + status-based cap rules
- **2026 caps:** MFJ/Single $40,400, MFS $20,000 per spouse (with income phase-out)
- **Critical error avoided:** Applying full $40,400 to each MFS spouse (doubles deduction incorrectly)
- **Implementation:** Year-based lookup table, filing-status-specific caps, MAGI phase-out calculation
- **Source:** [IRS Schedule A Instructions](https://www.irs.gov/instructions/i1040sca)

**Deduction Method Coordination is Mandatory for MFS**
- **Discovery:** IRS rule requires both MFS spouses to use the same deduction method (both standard OR both itemized)
- **Context:** Phase 2 compliance requirement — software must enforce, not just warn
- **Impact:** Cannot allow Spouse A to itemize while Spouse B takes standard deduction
- **Enforcement strategy:** Service-layer validation on deduction_method change, cascade to spouse or block change
- **UI pattern:** Display coordination status, require confirmation if change affects spouse
- **Source:** [IRS FAQ - Other Deduction Questions](https://www.irs.gov/faqs/itemized-deductions-standard-deduction/other-deduction-questions)

**Expense Allocation Requires Tracking Payment Source**
- **Discovery:** IRS allocates joint expenses based on who paid, not just equal split assumption
- **Context:** Mortgage interest, property taxes can be 100% taxpayer, 100% spouse, or custom % split
- **Default rule:** Joint payment from joint account = 50/50 split
- **Exception:** If one spouse paid from separate account, that spouse claims 100%
- **Implementation:** JSON allocation metadata per expense type (flexible schema without 10+ columns)
- **Source:** [IRS FAQ - Real Estate Taxes, Mortgage Interest](https://www.irs.gov/faqs/itemized-deductions-standard-deduction/real-estate-taxes-mortgage-interest-points-other-property-expenses)

**Phase 1 Only Implemented Standard Deduction Path**
- **Discovery:** JointAnalysisService.analyze_joint() hardcodes standard deduction, no itemized path
- **Context:** Phase 2 must add entire itemized deduction calculation flow
- **Net-new work:** Itemized deduction model/storage, SALT cap calculation, medical expense threshold, coordination validation
- **Build order:** Add deduction_method to Client → itemized calculation service → extend JointAnalysisService

**MFJ-Only Tax Strategies Require Explicit Flagging**
- **Discovery:** Spousal IRA, EITC, education credits, student loan interest are completely unavailable for MFS
- **Context:** Phase 4 per-spouse strategy personalization
- **Pattern:** `STRATEGY_FILING_REQUIREMENTS` dictionary with requires/warning per strategy
- **Implementation:** Filter strategies by filing status, show warning badge for incompatible status
- **Source:** [IRS EITC Qualification](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc), [IRS Education Credits](https://www.irs.gov/credits-deductions/individuals/education-credits-aotc-and-llc)

**Income Type Determines Strategy Relevance**
- **Discovery:** Different income types have different applicable strategies (LLC→SEP-IRA/QBI, W-2→401k/HSA)
- **Context:** Phase 4 per-spouse strategy personalization
- **Detection method:** Form presence in ExtractedData (W-2 present = W-2 employee, Schedule C = self-employed)
- **Pattern:** `INCOME_TYPE_STRATEGIES` mapping income types to relevant strategy IDs
- **Application:** Prioritize relevant strategies in display order, show "recommended for your income" badge

## What Doesn't Work

### Dual-Filer Tax Domain Anti-Patterns

**Treating MFS Filers as Completely Independent**
- **What fails:** Allowing one spouse to itemize while the other takes standard deduction on MFS
- **Why it fails:** IRS rule violation — if one itemizes, both must itemize. Software allowing mismatch causes automatic rejection
- **Correct approach:** Database constraint + UI validation locking both spouses to same `deduction_type` when filing separately

**Using MFJ Thresholds for MFS Calculations**
- **What fails:** Applying QBI threshold $383,900 (MFJ) to MFS filers
- **Why it fails:** MFS uses single filer thresholds ($191,950), doubles QBI deduction incorrectly
- **Real impact:** Husband with $250k LLC would show full QBI when it should be phased out
- **Correct approach:** Threshold lookup by exact filing status, not "married" keyword

**Copying MFJ Credit Logic to MFS Without Adjustments**
- **What fails:** Calculating EITC, student loan interest deduction, education credits for MFS
- **Why it fails:** These credits are completely unavailable (not phased out) on MFS
- **Example:** Student loan interest = $0 for MFS, not a gradual phase-out
- **Correct approach:** Filing status eligibility matrix for each credit, block ineligible credits early

**Client-Side Tax Calculation for Joint Analysis**
- **What fails:** Calculating MFJ/MFS tax amounts in JavaScript from individual summaries
- **Why it fails:** Tax bracket logic is complex, error-prone, already exists in `TaxCalculator`
- **Maintenance problem:** Duplicates logic in two languages (Python + JS), diverges over time
- **Correct approach:** Server-side calculation in `JointAnalysisService` using `TaxCalculator`, frontend only displays

**Denormalizing Spouse Data Across Records**
- **What fails:** Storing spouse1's data redundantly in spouse2's record
- **Why it fails:** Data duplication leads to inconsistency when one spouse's data updates
- **Example:** Husband's income stored in wife's record → update husband's W-2 → wife's record shows stale income
- **Correct approach:** Foreign key relationship (`spouse_id`), query both records at runtime

**SALT Cap Not Halved for MFS**
- **What fails:** Applying $40,000 SALT cap (2026 OBBBA change) to each MFS spouse
- **Why it fails:** MFS cap is $20,000 per spouse (exactly half), not full $40k
- **Impact:** Overstates MFS itemized deductions by up to $20,000, recommends MFS when MFJ is better
- **Correct approach:** SALT cap by filing status (MFJ: $40k, MFS: $20k each)

**Assuming 50/50 Split for All Joint Expenses**
- **What fails:** Defaulting to equal split for all joint expenses without checking payment source
- **Why it fails:** IRS requires allocation based on who paid, not assumption
- **Real impact:** Spouse deducts mortgage interest they didn't pay, violates IRS rules
- **Correct approach:** Track allocation method (taxpayer/spouse/both/joint) with percentage split
- **Source:** Phase 2 research finding

**Ignoring SALT Income Phase-Out**
- **What fails:** High-income MFS filer claims full $20,000 SALT deduction at $400k MAGI
- **Why it fails:** OBBBA includes income phase-out: $0.30 reduction per $1 over threshold
- **Impact:** Phase-out reduces $20k cap to $5k floor for high earners (MFS threshold $250k MAGI)
- **Correct approach:** Include MAGI in SALT cap calculation, apply phase-out formula
- **Source:** Phase 2 research finding

**Showing Joint-Only Strategies Without Filing Status Context**
- **What fails:** Displaying Spousal IRA recommendation when viewing MFS analysis
- **Why it fails:** Strategy is unavailable for MFS, misleads user
- **Correct approach:** Add filing_status_requirements to each strategy, show warning or hide for incompatible status
- **Source:** Phase 4 research finding

**Document Attribution Without Spouse Link Validation**
- **What fails:** Allowing "Spouse" attribution on upload when client has no spouse_id
- **Why it fails:** Data goes to wrong client or causes error
- **Correct approach:** Only show attribution selector when client.spouse_id exists
- **Source:** Phase 4 research finding

## Phase Learnings

### Project Research: Dual-Filer Tax Analysis with MFJ vs MFS Comparison

**Phase:** Initial research (4 parallel agents: STACK, FEATURES, ARCHITECTURE, PITFALLS)
**Domain:** Tax professional software (Flask MVC)
**Date:** 2026-02-04

**Key Research Findings:**

1. **Stack Decision:** Keep existing Flask + SQLAlchemy + vanilla JS — no migration needed
   - **Rationale:** Current stack handles dual-filer requirements, industry standard (Drake Tax, TaxSlayer Pro use similar)
   - **Critical addition:** Split.js (2kb) for resizable split panes, CSS Grid for layout
   - **Avoided:** React/Vue migration (100kb+ overhead, build complexity for Flask app)

2. **Architecture Pattern:** Service layer orchestration (JointAnalysisService coordinates existing components)
   - **Why it works:** No changes to working `TaxCalculator` or `AnalysisEngine`, clear separation of concerns
   - **Build order:** Service → API → UI → Workflows (dependencies drive phase structure)
   - **Caching strategy:** Bidirectional hash invalidation when either spouse's data changes

3. **Critical Pitfall:** Itemized deduction coordination (IRS rule: both must use same method on MFS)
   - **Impact:** Violation causes automatic IRS rejection
   - **Prevention:** Database constraint + UI validation enforcing matching `deduction_type`
   - **Phase timing:** Address in Phase 1 (Core Calculation), not later

4. **Critical Pitfall:** Credit disqualification for MFS (EITC, student loan interest completely unavailable)
   - **Impact:** Phantom tax savings, wrong filing status recommendation
   - **Prevention:** Filing status eligibility matrix, block ineligible credits with UI explanation
   - **Example:** Student loan interest = $0 for MFS (not phased out, just ineligible)

5. **Critical Pitfall:** QBI threshold confusion (MFS uses $191k threshold, not $383k MFJ threshold)
   - **Impact:** Doubles QBI deduction incorrectly for real use case (husband $250k LLC)
   - **Prevention:** Threshold lookup by exact filing status in QBI calculation

6. **Critical Pitfall:** SQLite concurrency (single-writer bottleneck with dual-filer writes)
   - **Impact:** "Database is locked" errors hurt UX
   - **Solution:** Enable WAL mode immediately (`PRAGMA journal_mode=WAL` + 30s busy timeout)
   - **Migration path:** If concurrency persists, upgrade to PostgreSQL

7. **Confidence Level:** HIGH overall
   - **High confidence areas:** Stack (verified with industry standards), Architecture (extends existing patterns), Pitfalls (IRS official guidance)
   - **Medium confidence areas:** Community property states (needs Form 8958 research), ACA subsidy repayment (2026 rule change)
   - **Flagged for deeper research:** Community property income attribution (Phase 2), ACA premium tax credit repayment (if client has Form 1095-A)

**Research Gaps to Address:**

- **Community property states:** Form 8958 logic for 9 states (AZ, CA, ID, LA, NV, NM, TX, WA, WI) requires 50/50 income splitting
  - **Scoping decision:** Out of scope for MVP if clients not in these states
  - **Validation strategy:** Check client address during onboarding, surface requirement if applicable

- **ACA premium tax credit repayment:** 2026 rule change (full repayment for MFS, no cap)
  - **Scoping decision:** Add warning in UI, flag for manual review
  - **Feature scope:** Form 1095-A parsing if needed, allocate separate feature

- **Dependent allocation:** Each child claimed by one spouse only on MFS, requires Form 8332 validation
  - **Phase 2 deliverable:** Add `Dependent` model with `claimed_by_client_id` FK, allocation UI

**Recommended Phase Structure (4 phases):**

1. **Phase 1: Core MFJ/MFS Calculation Engine** — Tax accuracy first, address critical pitfalls
2. **Phase 2: MFS-Specific Compliance Logic** — Deduction coordination, dependent allocation, special rules
3. **Phase 3: Split-Screen UI and Comparison View** — Side-by-side display, comparison report
4. **Phase 4: Joint Optimization and Advanced Features** — Differentiators, visual enhancements

**Key Takeaway:** Tax calculation accuracy is foundational. All 7 critical pitfalls must be addressed before building UI. Service layer orchestration preserves existing code while adding joint analysis. Bidirectional cache invalidation prevents stale data. SQLite WAL mode must be enabled immediately.

### Phase 1 Research: Core Dual-Filer Calculation Engine

**Phase:** Phase 1 Research
**Domain:** Dual-filer MFJ/MFS calculation engine
**Date:** 2026-02-04

**Key Discoveries:**

1. **TaxCalculator Already Handles All Filing Statuses**
   - **Discovery:** Existing `TaxCalculator` (lines 304-312) already has correct QBI thresholds for MFS
   - **Verification:** `married_separate` uses $197,300 threshold (same as single), not half of MFJ
   - **Impact:** No modifications needed to TaxCalculator — use as-is for MFJ/MFS calculations
   - **Confidence:** HIGH — Verified in existing code

2. **ExtractedData Fields Are Form-Agnostic**
   - **Discovery:** `ExtractedData` stores `form_type`, `field_name`, `field_value` generically
   - **Impact:** No schema changes needed for income attribution (T/S/J) — can store as field metadata
   - **Pattern:** `field_name='wages:taxpayer'` or `field_name='wages:spouse'` or `field_name='wages:joint'`
   - **Alternative:** Add `attribution` column to `ExtractedData` (cleaner but requires migration)

3. **Bidirectional Cache Invalidation Has Side Effect**
   - **Discovery:** Extending `_calculate_data_version_hash()` to include spouse means individual analyses refresh when spouse data changes
   - **Trade-off:** More recalculations (wife's change → husband's individual analysis refreshes) vs stale data prevention
   - **Decision:** Accept increased recalculations — correctness over performance
   - **UI requirement:** Phase 3 must explain "Analysis includes both spouses' data"

4. **SQLite WAL Mode Is Non-Negotiable**
   - **Discovery:** Default SQLite mode = single writer, dual-filer = 2x write frequency
   - **Evidence:** Pitfall #6 documents "database locked" errors with concurrent analysis + upload
   - **Solution:** `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=30000` in `init_db.py`
   - **Timing:** Must enable in Phase 1 before any dual-writer testing
   - **Fallback:** If WAL insufficient, migrate to PostgreSQL (unlikely for single tax pro use case)

5. **Blueprint Pattern Already Established**
   - **Discovery:** `routes/api.py` shows clean blueprint registration pattern (lines 1-13)
   - **Pattern:** Each feature domain gets own blueprint file, registered in `api_bp`
   - **Application:** Create `routes/joint_analysis.py` with `joint_analysis_bp`, register in `api.py`
   - **Consistency:** Follow existing route structure from `routes/analysis.py` (lines 7-21)

6. **Model Registration Pattern Documented**
   - **Discovery:** `models/__init__.py` imports all models, exports in `__all__` list
   - **Pattern:** Add `JointAnalysisSummary` to imports and `__all__` list
   - **Database:** `db.create_all()` in `init_db.py` handles table creation automatically

7. **Credit Eligibility Matrix Required**
   - **Discovery:** No existing credit eligibility validation by filing status
   - **Gap:** `TaxStrategiesService` doesn't filter strategies by filing status
   - **Solution:** Create `CREDIT_ELIGIBILITY` dict in `JointAnalysisService`, filter MFS strategies
   - **Example:** EITC, student loan interest, education credits all unavailable for MFS
   - **Phase 1 scope:** Filter strategies in joint analysis, don't modify TaxStrategiesService yet

**Technical Patterns Verified:**

- **Hash-based caching:** Lines 14-35, 56-72 in `analysis_engine.py` — pattern extends to joint hash
- **Filing status bracket lookup:** Lines 83-108 in `tax_calculator.py` — already supports 'married_separate'
- **Blueprint registration:** Lines 1-13 in `routes/api.py` — add joint_analysis_bp following this pattern
- **Model to_dict() serialization:** Lines 27-54 in `models/analysis.py` — JointAnalysisSummary follows same pattern

**Open Questions Resolved:**

1. **Q: Does TaxCalculator need modification for MFS?**
   - **A:** No — lines 304-312 show correct thresholds already implemented

2. **Q: How to store income attribution (T/S/J)?**
   - **A:** Phase 1 can defer this (no T/S/J needed for basic MFJ/MFS comparison)
   - **Phase 2:** Add `attribution` column to `ExtractedData` or use field name convention

3. **Q: Should individual analyses auto-refresh when spouse changes?**
   - **A:** Yes — bidirectional invalidation prevents stale data (correctness > performance)

**Recommendations for Phase 1 Implementation:**

1. **Build Order:** Service layer → Model → API routes → Database init (WAL mode)
2. **No Modifications:** Don't change TaxCalculator, AnalysisEngine, TaxStrategiesService
3. **Credit Filtering:** Implement in JointAnalysisService, not in existing services
4. **Testing Priority:** Test cache invalidation, concurrent analysis, MFS credit exclusion
5. **Documentation:** Add docstrings explaining bidirectional cache behavior

**Phase 1 Success Criteria Validated:**

- TaxCalculator supports all filing statuses (verified: lines 304-312, 96-108)
- Caching pattern extends to joint analysis (verified: lines 14-35 pattern)
- Blueprint registration pattern documented (verified: api.py lines 1-13)
- Model pattern established (verified: AnalysisSummary lines 6-54)
- Pitfall solutions documented (7 critical pitfalls with prevention strategies)

**Confidence Assessment:** HIGH — All implementation questions answered, patterns verified in codebase, no blocking unknowns.

### Phase 2 Research: MFS-Specific Compliance Logic

**Phase:** Phase 2 Research
**Domain:** MFS compliance rules (deduction coordination, SALT caps, expense allocation)
**Date:** 2026-02-04

**Key Discoveries:**

1. **Deduction Method Coordination is Mandatory IRS Rule**
   - **Discovery:** Both MFS spouses MUST use same deduction method (both standard OR both itemized)
   - **Source:** IRS FAQ verified — not optional, enforcement required
   - **Implementation:** Service-layer validation on deduction_method change, block or cascade
   - **Database:** Add `deduction_method` column to Client model ('standard' or 'itemized')
   - **Confidence:** HIGH — Official IRS source

2. **SALT Cap Doubles for MFJ, Halves for MFS (2026 OBBBA)**
   - **Discovery:** 2026 caps are $40,400 MFJ/Single, $20,000 per MFS spouse (NOT $40,400 each)
   - **Phase-out:** Reduces $0.30 per $1 over MAGI threshold ($505k MFJ, $250k MFS) to floor ($10k/$5k)
   - **Critical error avoided:** Applying full cap to each MFS spouse doubles deduction incorrectly
   - **Implementation:** Filing-status-aware SALT cap calculation with MAGI phase-out
   - **Confidence:** HIGH — Multiple authoritative sources agree

3. **Expense Allocation Based on Payment Source**
   - **Discovery:** IRS allocates joint expenses by who paid, not automatic 50/50
   - **Default:** Joint payment from joint account = 50/50 split
   - **Exception:** Separate payment from separate account = 100% to payer
   - **Custom:** Can allocate by percentage (60/40, 70/30, etc.) based on actual ownership/payment
   - **Implementation:** JSON metadata field storing allocation_method + percentages
   - **Confidence:** MEDIUM — IRS guidance clear, implementation pattern inferred

4. **Phase 1 Only Has Standard Deduction Path**
   - **Discovery:** JointAnalysisService.analyze_joint() hardcodes standard deduction, no itemized logic
   - **Impact:** Phase 2 is net-new work, not just adding validation to existing itemized path
   - **Build requirements:** Itemized deduction calculation, SALT cap enforcement, medical expense threshold (7.5% AGI), coordination validation
   - **Model additions:** Client.deduction_method, ItemizedDeduction table (or ExtractedData naming convention)
   - **Confidence:** HIGH — Verified in existing codebase

5. **No External Dependencies Needed**
   - **Discovery:** All compliance logic can build on existing stack (Flask-SQLAlchemy, TaxCalculator)
   - **JSON storage:** Use built-in JSON fields for allocation metadata (no new libraries)
   - **Service layer:** Extend JointAnalysisService, no architectural changes
   - **Confidence:** HIGH — Implementation patterns verified in Phase 1 codebase

**Pitfalls Identified:**

1. **Not enforcing deduction coordination on data change** — Spouses get out of sync, IRS rejection
2. **Applying full SALT cap to each MFS spouse** — Overstates itemized deductions by up to $20k
3. **Assuming 50/50 split for all joint expenses** — Violates IRS allocation rules
4. **Allowing itemized deductions without SALT cap enforcement** — Inflates tax benefit unrealistically
5. **Missing income phase-out for high-income SALT filers** — OBBBA phase-out ignored

**Open Questions:**

1. **Community property states (9 states)** — Does ATSA serve these? Need Form 8958? → Defer to Phase 4
2. **Medical expense allocation for MFS** — IRS rules unclear, likely "who paid" → Research IRS Pub 502
3. **Dependent allocation enforcement** — No Dependent model exists → Add in Phase 2 if needed
4. **Itemized vs standard comparison UI** — How to display 6 scenarios cleanly? → Phase 3 UI design
5. **SALT cap reversion in 2030** — Prepare year-based lookup table → Add reminder for 2029 review

**Recommendations for Phase 2 Implementation:**

1. **Model Changes:** Add Client.deduction_method, use ExtractedData with naming convention for itemized amounts (MVP), defer ItemizedDeduction table to Phase 3+
2. **Service Layer:** Create validation methods (deduction coordination, SALT cap by status, expense allocation), extend JointAnalysisService.analyze_joint() with itemized path
3. **No External Deps:** Use existing stack, JSON for allocation metadata
4. **Testing Priority:** Deduction coordination enforcement, SALT cap by filing status + income phase-out, expense allocation scenarios
5. **Documentation:** Code examples for 3 compliance patterns (coordination, SALT cap, allocation)

**Confidence Assessment:** HIGH — IRS rules verified with official sources, implementation patterns clear from existing codebase, gaps identified for planning.

### Phase 4 Research: Dual-Filer Strategies and Workflow

**Phase:** Phase 4 Research
**Domain:** Per-spouse strategy personalization, joint optimization strategies, workflow enhancement
**Date:** 2026-02-04

**Key Discoveries:**

1. **TaxStrategiesService Lacks Income-Type Awareness**
   - **Discovery:** Existing 10 strategies analyzed generically, not tailored to income type
   - **Gap:** LLC owner sees same strategies as W-2 employee
   - **Solution:** Detect income types from form presence (W-2, Schedule C, K-1, etc.)
   - **Pattern:** `INCOME_TYPE_STRATEGIES` mapping income types to relevant strategy IDs
   - **Confidence:** HIGH — Verified in services/tax_strategies.py analysis

2. **Joint-Only Strategies Not Generated**
   - **Discovery:** No Spousal IRA, bracket utilization, or other MFJ-only strategies exist
   - **Gap:** JointAnalysisService compares taxes but doesn't recommend joint optimization strategies
   - **Solution:** Create `JointStrategyService` to generate MFJ-only recommendations
   - **Key strategies:** Spousal IRA ($7,500 limit 2026), Bracket utilization, EITC eligibility
   - **Confidence:** HIGH — IRS rules verified, implementation patterns clear

3. **Credit Filtering Exists But Lacks "Why"**
   - **Discovery:** JointAnalysisService._filter_strategies_by_filing_status() removes MFS-ineligible credits
   - **Gap:** Removed silently, no warning shown when viewing individual analysis for MFS
   - **Solution:** Add feasibility warnings with STRATEGY_FILING_REQUIREMENTS dictionary
   - **UI pattern:** Warning badge on strategy card: "Requires MFJ filing status"
   - **Confidence:** HIGH — Verified in services/joint_analysis_service.py lines 120-147

4. **Spouse Linking Workflow Is Manual**
   - **Discovery:** /clients/<id>/link-spouse endpoint exists but UI flow is manual
   - **Gap:** User must create clients separately, manually enter spouse_id in edit form
   - **Solution:** "Create Married Couple" button with two-column form, auto-link + redirect
   - **Implementation:** POST /api/clients/create-couple endpoint, joint_analysis_url in response
   - **Confidence:** HIGH — UI pattern straightforward, follows existing modal pattern

5. **Document Attribution Not Supported**
   - **Discovery:** Document model has client_id but no attribution field
   - **Gap:** Cannot tag W-2 as belonging to spouse during upload
   - **Solution:** Add `attribution` column to Document ('taxpayer', 'spouse', 'joint')
   - **Data flow:** If attribution='spouse', route extracted data to client.spouse_id
   - **Confidence:** HIGH — Model change is simple, upload UI enhancement follows existing patterns

6. **Manual Entry Not Available**
   - **Discovery:** All income data requires document upload + OCR
   - **Gap:** No alternative for manual income entry
   - **Solution:** Add manual entry form alongside upload (tab or accordion UI)
   - **Implementation:** Create ExtractedData records with form_type='MANUAL_ENTRY'
   - **Confidence:** MEDIUM — UI design decision, backend straightforward

**Recommended Build Order:**

1. **Wave 1:** Spouse linking workflow (REQ-24) — Enables testing of other features
2. **Wave 2:** Document attribution (REQ-25) + Manual entry (REQ-26) — Data entry improvements
3. **Wave 3:** Per-spouse strategies (REQ-21), Joint strategies (REQ-22), Feasibility flags (REQ-23)

**Pitfalls Identified:**

1. Showing MFJ-only strategies to MFS filers without warning
2. Attribution selector without spouse link validation
3. Joint strategies generated before both spouses have data
4. Income type detection fails when no documents uploaded
5. Duplicate strategy recommendations in individual + joint sections

**Confidence Assessment:** HIGH — Existing codebase patterns clear, IRS rules verified, no architectural changes needed.

---

## Pattern Library

### Successful Patterns

**Pattern: Service Layer Orchestration**
- **Use case:** Combining multiple existing components without modifying them
- **Implementation:** New service class coordinates calls to existing services + models
- **Example:** `JointAnalysisService` coordinates `AnalysisEngine` (2x) + `TaxCalculator` + caching
- **When to use:** Need to add complex workflow without changing working code

**Pattern: Bidirectional Cache Invalidation**
- **Use case:** Linked data where either side changing should invalidate derived calculations
- **Implementation:** Combined hash from both entities' version hashes
- **Example:** Joint analysis hash = `sha256(spouse1_hash + '|' + spouse2_hash)`
- **When to use:** Cached results depend on multiple data sources that change independently

**Pattern: Filing-Status-Aware Threshold Lookup**
- **Use case:** Tax thresholds differ by filing status (brackets, phase-outs, exemptions)
- **Implementation:** Dictionary keyed by filing status, not "single" vs "married" boolean
- **Example:** QBI thresholds: `{'single': 191950, 'married_joint': 383900, 'married_separate': 191950}`
- **When to use:** Any tax calculation involving thresholds (QBI, IRA, AMT, SALT cap)

**Pattern: JSON Metadata for Flexible Allocation**
- **Use case:** Track expense allocation between multiple parties with varying rules
- **Implementation:** JSON field storing allocation_method + percentages per expense type
- **Example:** `{"mortgage_interest": {"allocation": "both", "taxpayer_pct": 60, "spouse_pct": 40}}`
- **When to use:** Allocation rules are complex, vary by item, may evolve over time
- **Source:** Phase 2 research finding

**Pattern: Service-Layer Validation with Cascading**
- **Use case:** Business rule requires coordination between linked entities (e.g., spouses)
- **Implementation:** Validation method returns allow/block/confirm_cascade decision
- **Example:** Spouse A itemizes → validation checks Spouse B → returns cascade requirement
- **When to use:** Rule affects multiple entities, needs user confirmation, complex logic
- **Source:** Phase 2 research finding

**Pattern: Income-Type Strategy Relevance**
- **Use case:** Tailor strategy recommendations to user's income profile
- **Implementation:** Detect income types from form presence, map to relevant strategies
- **Example:** W-2 present → prioritize 401(k), HSA; Schedule C present → prioritize SEP-IRA, QBI
- **When to use:** Personalized recommendations based on user characteristics
- **Source:** Phase 4 research finding

**Pattern: Strategy Filing Requirements Dictionary**
- **Use case:** Show warnings when strategy requires different filing status
- **Implementation:** Dictionary with requires/warning per strategy, check at display time
- **Example:** `{'spousal_ira': {'requires': 'married_joint', 'warning': 'Requires MFJ'}}`
- **When to use:** Filing-status-dependent feature eligibility
- **Source:** Phase 4 research finding

### Anti-Patterns to Avoid

**Anti-Pattern: Inline Business Logic in Routes**
- **What it looks like:** Route handler calculates MFJ/MFS tax directly
- **Why it's bad:** Violates separation of concerns, untestable, not reusable
- **Correct approach:** Routes delegate to service layer, services contain business logic

**Anti-Pattern: Global Filing Status on Shared Model**
- **What it looks like:** Adding `joint_filing_status` field to `Client` model applying to both spouses
- **Why it's bad:** Ambiguity (which spouse's record is source of truth?), violates single responsibility
- **Correct approach:** Filing status determined per-analysis, stored in `JointAnalysisSummary` per run

**Anti-Pattern: Eager Loading All Joint Analyses**
- **What it looks like:** Pre-calculating joint analyses for all spouse pairs on every data change
- **Why it's bad:** Expensive computation for data that may never be viewed
- **Correct approach:** Lazy evaluation — calculate on-demand when user navigates to joint analysis page, cache with hash

**Anti-Pattern: Hard-Coding Year-Specific Tax Rules**
- **What it looks like:** `SALT_CAP = 40400` as constant without year context
- **Why it's bad:** Tax rules change by year (TCJA → OBBBA → 2030 reversion), hard to maintain
- **Correct approach:** Year-based lookup table or dictionary, explicit tax_year parameter
- **Source:** Phase 2 research finding (SALT caps vary 2024 → 2026 → 2030)

**Anti-Pattern: Database Constraints for Complex Business Rules**
- **What it looks like:** Foreign key constraint enforcing "both spouses must itemize"
- **Why it's bad:** Database can't express complex logic, poor error messages, inflexible
- **Correct approach:** Service-layer validation with clear messages and cascade options
- **Source:** Phase 2 research finding

---

## Iteration Log Entry

**Iteration:** 10
**Phase:** 3 Plan: 02
**Action:** EXECUTE
**Outcome:** Success
**Duration:** ~3 minutes

### Learnings from This Execution

**What Worked:**
- Writing full JavaScript file in one pass rather than incremental edits - faster, fewer potential merge issues
- Following existing analysis.js patterns closely - consistent code style, proven API patterns
- Testing API endpoints independently before full UI test - isolated bugs faster

**What Didn't Work:**
- N/A - execution was smooth

**Codebase Discovery:**
- API response structure for joint analysis: `{ result: { spouse1, spouse2, mfj, mfs_spouse1, mfs_spouse2, comparison } }`
- Client API returns flat array, need to filter for `spouse_id` to get linked clients
- existing analysis.js `formatCurrency()` uses `!amount` check which fails for 0 - improved to explicit null/undefined check

**Prompt Tuning:**
- N/A

---

### Phase 3 Summary

**Phase:** Split-Screen UI
**Plans:** 2/2 complete
**Requirements Implemented:** REQ-18, REQ-19, REQ-20

**Key Implementation Details:**
- Split.js CDN integration (no npm build required)
- localStorage persistence for panel sizes
- Responsive destroy/recreate at 768px breakpoint
- Async/await pattern for all API calls
- Dual dropdown filtering for linked spouses only

**Files Created/Modified:**
- templates/joint_analysis.html (created)
- static/css/style.css (~280 lines added)
- static/js/joint_analysis.js (~490 lines)
- app.py (route added)

---

*Last updated: 2026-02-04*
*Next update: After Phase 4 planning*
