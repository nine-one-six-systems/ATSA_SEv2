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

- ✅ TaxCalculator supports all filing statuses (verified: lines 304-312, 96-108)
- ✅ Caching pattern extends to joint analysis (verified: lines 14-35 pattern)
- ✅ Blueprint registration pattern documented (verified: api.py lines 1-13)
- ✅ Model pattern established (verified: AnalysisSummary lines 6-54)
- ✅ Pitfall solutions documented (7 critical pitfalls with prevention strategies)

**Confidence Assessment:** HIGH — All implementation questions answered, patterns verified in codebase, no blocking unknowns.

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

---

*Last updated: 2026-02-04*
*Next update: After Phase 1 implementation*
