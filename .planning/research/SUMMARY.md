# Project Research Summary

**Project:** Dual-Filer Tax Analysis with MFJ vs MFS Comparison
**Domain:** Tax Professional Software (Flask-based)
**Researched:** 2026-02-04
**Confidence:** HIGH

## Executive Summary

This project extends an existing Flask-based tax analysis platform to support dual-filer scenarios for married couples, enabling side-by-side comparison of Married Filing Jointly (MFJ) versus Married Filing Separately (MFS). The core value proposition is showing tax professionals which filing status minimizes tax liability for specific client scenarios.

The recommended approach preserves the existing vanilla JavaScript + Flask + SQLAlchemy stack, avoiding framework migrations. The architecture extends current patterns with a new `JointAnalysisService` that orchestrates parallel individual analyses and combines them into MFJ/MFS comparisons. Split-screen UI uses lightweight Split.js (2kb) with CSS Grid, maintaining the existing vanilla JS architecture. The existing `TaxCalculator` already supports both filing statuses—no engine rewrite needed.

Key risks center on tax calculation accuracy (15+ critical pitfalls identified) rather than technical complexity. The most dangerous pitfall is violating IRS deduction coordination rules (one spouse itemizes → other must itemize on MFS). Credit disqualification for MFS (EITC, student loan interest completely unavailable) must be enforced or phantom savings corrupt recommendations. SQLite concurrency becomes an issue with dual-filer writes; enabling WAL mode immediately prevents "database locked" errors. Cache invalidation must be bidirectional—when either spouse's data changes, joint analysis must refresh.

## Key Findings

### Recommended Stack

**Keep existing technologies—no migration needed.** The current Flask + SQLAlchemy + vanilla JS stack handles dual-filer requirements without framework additions. Research confirms this is the standard approach for professional tax software (Drake Tax, TaxSlayer Pro use similar architectures).

**Core technologies:**
- **Flask 3.0.0** (existing): Web framework — mature, sufficient for dual-filer API extensions
- **SQLAlchemy 2.0.35+** (existing): ORM — excellent support for spouse relationship joins, already configured
- **SQLite** (existing): Database — adequate for single-user tax professional use, enable WAL mode for concurrency
- **Vanilla JavaScript ES6+** (existing): Frontend — Proxy pattern for state management, no framework bloat
- **Split.js 1.6.5** (new, 2kb): Split-screen panes — lightweight, vanilla JS, resizable divider for husband/wife view
- **CSS Grid + Flexbox** (native): Layout — Grid for split-screen macro layout, Flexbox for component alignment

**Optional additions:**
- **Flask-Pydantic 0.12.0**: Type-based API validation for complex dual-filer payloads (defer until needed)
- **dataclasses-json**: Fast nested object serialization if comparison JSON becomes complex (defer)

**Critical version notes:**
- MFS QBI thresholds ($191,950-$266,950) differ from MFJ ($383,900-$533,900) — existing code has correct thresholds
- 2026 tax rules: SALT cap increased to $40k (MFJ/Single) but only $20k for MFS
- 2026 OBBBA changes: AMT exemption phase-out lowered, premium tax credit repayment cap removed

### Expected Features

Research across Drake Tax, TaxSlayer Pro, and Lacerte reveals professional dual-filer tools have consistent feature sets.

**Must have (table stakes):**
- **Side-by-side income entry** — Split-screen view showing both spouses' tax pictures simultaneously (industry standard)
- **MFJ vs MFS comparison report** — Three-column comparison: MFJ outcome, MFS spouse 1, MFS spouse 2, net difference in dollars
- **Automatic tax calculation for both statuses** — Calculate 3 returns from single data entry (1 joint + 2 separate)
- **Income source attribution (T/S/J)** — Taxpayer, Spouse, or Joint designation for all income (required for accurate MFS)
- **Deduction method enforcement** — IRS rule: if one spouse itemizes on MFS, both must itemize (blocking validation)
- **Credit availability by status** — Different rules per credit (EITC unavailable on MFS, student loan interest unavailable, education credits unavailable)
- **Standard deduction amounts** — 2026: MFJ $32,200, MFS $16,100 each
- **Tax bracket application** — MFJ uses wider brackets, MFS mirrors single filer brackets
- **Shared expense allocation** — Mortgage interest, property taxes split T/S/Both for MFS accuracy

**Should have (competitive differentiators):**
- **Per-spouse tax strategies** — Individual recommendations based on income type (LLC → SEP-IRA, W-2 → 401k max)
- **Joint optimization strategies** — Strategies only available when filing jointly (spousal IRA, bracket utilization)
- **Income source breakdown tooltip** — At-a-glance view: "Husband: $250k LLC + $0 W-2, Wife: $0 LLC + $100k W-2"
- **Visual bracket utilization** — Chart showing which income falls into which brackets for MFJ vs MFS
- **Strategy feasibility flags** — Warnings like "SEP-IRA only available if filing jointly"

**Defer (v2+):**
- **What-if scenario modeling** — Real-time recalculation when changing income amounts (high complexity, nice-to-have)
- **Community property state handling** — Form 8958 generation for AZ, CA, ID, LA, NV, NM, TX, WA, WI (adds significant complexity)
- **Deduction allocation optimizer** — Suggest optimal splits of shared expenses (advanced, rare in consumer tools)
- **Prior year comparison** — Historical trend analysis (requires data structure changes)

### Architecture Approach

The architecture extends existing Flask MVC patterns with a **service layer orchestration** approach. A new `JointAnalysisService` coordinates two individual `AnalysisEngine` runs and combines results into MFJ/MFS scenarios. This preserves working code (no changes to `TaxCalculator` or `AnalysisEngine`) while adding joint analysis capabilities.

**Major components:**

1. **JointAnalysisService** (new) — Orchestrates dual-filer analysis
   - Fetches both spouse records via existing `spouse_id` foreign key
   - Triggers individual analyses using existing `AnalysisEngine.analyze_client()`
   - Calculates MFJ scenario (combined income through `TaxCalculator`)
   - Calculates MFS scenario (separate incomes through `TaxCalculator`)
   - Generates comparison with recommendation and savings
   - Caches results in new `JointAnalysisSummary` model with bidirectional hash invalidation

2. **Split-Screen UI Component** (new) — Side-by-side spouse display
   - Left panel: Spouse 1 individual analysis (reuses existing summary/strategy components)
   - Right panel: Spouse 2 individual analysis (reuses existing components)
   - Bottom section: Joint comparison (new component showing MFJ vs MFS side-by-side)
   - Uses Split.js for resizable divider, CSS Grid for responsive layout
   - Stacks vertically on mobile (<768px breakpoint)

3. **Cache Invalidation Extension** (modify existing) — Bidirectional freshness
   - Existing: `data_version_hash` from one client's ExtractedData timestamps
   - Enhanced: Hash includes spouse's data when `spouse_id` exists
   - When either spouse's data changes → both individual AND joint analyses invalidate
   - Prevents stale joint analysis when one spouse's W-2 updates

**Build order (dependency chain):**
- Phase 1: Service layer (JointAnalysisService + JointAnalysisSummary model) — must exist before API/UI
- Phase 2: API layer (routes/joint_analysis.py blueprint) — needs service layer to consume
- Phase 3: UI layer (split-screen template + JavaScript) — needs API to fetch data
- Phase 4: Workflows (spouse linking UX, data entry improvements) — polish after core works

**Technology compatibility:**
All components use existing stack. No new Python packages required for MVP (Split.js loads via CDN). Flask service class pattern matches existing `AnalysisEngine`. SQLAlchemy relationships already support spouse linkage. Vanilla JS Proxy pattern for state management (modern alternative to Redux).

### Critical Pitfalls

Research identified 15 domain-specific pitfalls, with 7 classified as critical (cause IRS rejection or incorrect tax liability). Top 5 to address in Phase 1:

1. **Itemized deduction coordination violation** — IRS rule: if one spouse itemizes on MFS, both must itemize. Software allowing mismatched deduction types causes automatic rejection. Prevention: Database constraint + UI validation locking both spouses to same deduction_type when filing separately. Show warning: "Your spouse itemized, so you must itemize too."

2. **Credit disqualification for MFS not enforced** — EITC, student loan interest deduction, adoption credit, education credits either completely unavailable or use different thresholds on MFS. Phantom savings if calculated incorrectly. Prevention: Filing status eligibility matrix for each credit. Student loan interest = $0 for MFS (not phased out, just ineligible). EITC = ineligible unless living apart 6+ months. UI shows grayed-out credits with tooltip explaining MFS restriction.

3. **QBI deduction threshold confusion** — MFS uses single filer thresholds ($191,950-$266,950), NOT married joint thresholds ($383,900-$533,900). Using wrong threshold doubles QBI deduction incorrectly. For real use case (husband $250k LLC), MFS should show reduced QBI due to phase-out. Prevention: Threshold lookup by filing status in QBI calculation (existing code has correct thresholds, verify usage).

4. **Analysis cache invalidation for dual-filer scenarios** — Current hash only includes one client's data. Spouse's W-2 changes → joint analysis shows stale numbers. Prevention: Extend `_calculate_data_version_hash()` to include spouse's ExtractedData when `spouse_id` exists. Bidirectional invalidation ensures either spouse's change refreshes joint analysis.

5. **SQLite concurrency issues during joint analysis** — SQLite = single writer. Joint analysis = long calculation + database writes. Dual-filer doubles concurrent write likelihood. Results in "database is locked" errors. Prevention: Enable SQLite WAL mode immediately (`PRAGMA journal_mode=WAL`), set 30-second busy timeout. Keep transactions short: read data, calculate outside transaction, write results in single commit.

**Moderate pitfalls (address in Phase 2 or flag for research):**
- **Community property state income attribution** — 9 states (AZ, CA, ID, LA, NV, NM, TX, WA, WI) require 50/50 income splitting for MFS, not W-2 recipient gets 100%. Requires Form 8958 logic. Flag as "needs deeper research."
- **Premium Tax Credit (ACA) repayment for MFS** — 2026 rule change: MFS filers repay ENTIRE subsidy, no cap. If client has Form 1095-A, MFS comparison must include repayment in total tax. Flag as "ACA handling out of scope for MVP."
- **Dependent allocation without Form 8332 validation** — Each child can only be claimed by one spouse on MFS. Need allocation UI showing which spouse claims which child. Flag as "dependent tracking feature required."

**Minor pitfalls (cosmetic, easily fixed):**
- Rounding discrepancies (use Decimal throughout, round only at display)
- Filing status display confusion (label "Married Filing Jointly (MFJ)" not just "Married")
- Standard deduction display not showing MFS reduction ($16,100 is half of $32,200)

## Implications for Roadmap

Based on research, I recommend a **4-phase structure** that builds from core calculation accuracy → MFS-specific compliance → user experience → advanced features.

### Phase 1: Core MFJ/MFS Calculation Engine
**Rationale:** Tax calculation accuracy is foundational. All other features depend on correct MFJ vs MFS comparison. Address critical pitfalls first (itemized deduction coordination, credit disqualification, QBI thresholds, cache invalidation, SQLite concurrency).

**Delivers:**
- `JointAnalysisService` with MFJ and MFS calculation methods
- `JointAnalysisSummary` model with bidirectional cache invalidation
- Filing-status-aware credit eligibility (EITC, student loan interest, education credits)
- QBI threshold lookup by filing status (existing code, verify usage)
- SQLite WAL mode enabled + optimistic locking for concurrent writes
- Extended `_calculate_data_version_hash()` to include spouse data
- Unit tests for all 2026 tax rules (brackets, deductions, credits, thresholds)

**Addresses features:**
- Automatic tax calculation for both statuses
- Credit availability by status
- Standard deduction amounts
- Tax bracket application

**Avoids pitfalls:**
- Pitfall 1 (itemized deduction coordination)
- Pitfall 3 (credit disqualification)
- Pitfall 4 (QBI thresholds)
- Pitfall 5 (cache invalidation)
- Pitfall 6 (SQLite concurrency)
- Pitfall 7 (retirement contribution phase-outs)
- Pitfall 11 (SALT cap halving)
- Pitfall 13 (rounding discrepancies)

**Research flag:** Standard patterns. No additional research needed (existing tax calculator handles filing statuses).

### Phase 2: MFS-Specific Compliance Logic
**Rationale:** MFS has special IRS rules beyond basic bracket differences. Deduction coordination, dependent allocation, credit restrictions. These are compliance requirements, not optional enhancements.

**Delivers:**
- Deduction method enforcement (both spouses must use same method on MFS)
- SALT cap enforcement ($20k for MFS, $40k for MFJ/Single)
- AMT exemption halving for MFS ($70,100 vs $140,200)
- Dependent allocation UI (each child claimed by one spouse only)
- HSA contribution limit coordination (family coverage = $8,750 shared, not each)
- Retirement contribution phase-out validation (MFS $0-$10k range, extremely narrow)

**Addresses features:**
- Deduction method enforcement
- Shared expense allocation (who paid this: T/S/Both)
- Income source attribution (T/S/J designation)

**Avoids pitfalls:**
- Pitfall 1 (deduction coordination — blocking validation)
- Pitfall 8 (AMT exemption halving)
- Pitfall 10 (dependent allocation)
- Pitfall 11 (SALT cap)
- Pitfall 12 (HSA contribution limits)
- Pitfall 14 (filing status display clarity)
- Pitfall 15 (standard deduction context)

**Research flag:**
- **Community property states (Pitfall 2)** — Needs deeper research. Form 8958 allocation logic is complex, state-specific. Flag as "out of scope for MVP" or allocate dedicated research phase.
- **ACA premium tax credit repayment (Pitfall 9)** — 2026-specific rule change. Flag as "needs research if client has Form 1095-A."

### Phase 3: Split-Screen UI and Comparison View
**Rationale:** Core calculations work. Now build the interface tax professionals interact with. Side-by-side view is table stakes (Drake Tax, TaxSlayer Pro standard). Comparison report delivers the "aha moment" showing which filing status saves money.

**Delivers:**
- Split-screen template (husband left, wife right)
- Split.js integration for resizable divider
- CSS Grid layout with responsive mobile stacking (<768px)
- Reuse existing summary-grid and strategy-card components
- Joint comparison section (MFJ vs MFS cards with recommendation)
- Income source breakdown tooltip (at-a-glance: "Husband: $250k LLC, Wife: $100k W-2")
- Filing status comparison report (three columns: MFJ, MFS spouse 1, MFS spouse 2)
- Visual indicators (savings amount, recommended status, reasons)

**Addresses features:**
- Side-by-side income entry
- MFJ vs MFS comparison report
- Income source breakdown by spouse
- Per-spouse tax strategies (individual recommendations)

**Avoids pitfalls:**
- Pitfall 14 (filing status display confusion — clear labels)
- Pitfall 15 (standard deduction context — show MFS is half of MFJ)

**Research flag:** Standard web UI patterns. No additional research needed (Split.js well-documented).

### Phase 4: Joint Optimization and Advanced Features
**Rationale:** Core functionality complete. Now add differentiators that set this tool apart from basic MFJ/MFS calculators.

**Delivers:**
- Joint optimization strategies (strategies only available when filing jointly)
- Visual bracket utilization (chart showing income distribution across brackets)
- Strategy feasibility flags ("SEP-IRA only available if filing jointly")
- Spouse linking workflow improvements (prevent self-linking, enforce bidirectional consistency)
- Document upload attribution (tag W-2/1099 to Taxpayer vs Spouse)
- Bulk upload support (handle documents for both spouses in one session)
- Joint analysis refresh UX (auto-refresh indicator, "last analyzed" timestamp)
- Prior year comparison (requires historical data — defer if time-constrained)

**Addresses features:**
- Joint optimization strategies
- Strategy feasibility flags
- Document upload for each spouse
- Spouse linking workflow

**Research flag:** No additional research needed (extends existing strategy engine patterns).

### Phase Ordering Rationale

**Calculation → Compliance → UI → Enhancements** progression prevents rework and ensures tax accuracy first.

- **Phase 1 before Phase 2:** Can't enforce MFS-specific rules without core calculation engine working.
- **Phase 2 before Phase 3:** UI displays comparison results. Results must be accurate before building UI.
- **Phase 3 before Phase 4:** Joint optimization strategies depend on having comparison view to display them.

**Dependency chain from ARCHITECTURE.md:**
```
Spouse Linking (existing)
    ↓
Income Source Attribution (Phase 2)
    ↓
Dual Tax Calculation (Phase 1)
    ↓
MFJ vs MFS Comparison Report (Phase 3)
    ↓
Filing Status-Specific Strategies (Phase 4)
```

**Parallel opportunities:**
- Document upload attribution (Phase 4) can be built alongside Phase 3 (independent)
- Visual bracket utilization (Phase 4) can be added after Phase 3 without blocking other features

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 2 (Community Property States):** Form 8958 allocation logic is state-specific and complex. Nine states have different rules (AZ, CA, ID, LA, NV, NM, TX, WA, WI). Recommend dedicated `/gsd:research-phase` for community property handling if serving clients in these states.
- **Phase 2 (ACA Premium Tax Credit):** 2026 rule changes (full repayment, no cap) affect MFS filers with marketplace health insurance. If client data includes Form 1095-A, needs research on reconciliation logic.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Core Calculation):** Existing `TaxCalculator` already handles filing statuses. 2026 tax brackets, deductions, thresholds are published IRS data. Implementation is straightforward extension.
- **Phase 3 (Split-Screen UI):** Split.js is well-documented. CSS Grid layouts are standard web patterns. No novel techniques required.
- **Phase 4 (Joint Optimization):** Extends existing strategy engine (`TaxStrategiesService`). Same patterns, filtering by filing status.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Flask + SQLAlchemy + vanilla JS matches industry standard (Drake Tax, TaxSlayer Pro). No migrations needed. Split.js is proven lightweight library. |
| Features | HIGH | Verified against Drake Tax, TaxSlayer Pro documentation. T/S/J attribution and MFJ vs MFS comparison are universal in professional tax software. |
| Architecture | HIGH | Service layer orchestration pattern verified with Flask best practices. Existing `TaxCalculator` supports both filing statuses (verified in codebase). Caching pattern already implemented, just extending to dual-filer. |
| Pitfalls | HIGH | Critical pitfalls sourced from IRS official guidance (Publication 555, 504, Topic 456). Tax professional resources (Millan CPA, SmartAsset) confirm phase-out thresholds and credit restrictions. SQLite concurrency solutions verified with Flask + SQLAlchemy documentation. |

**Overall confidence:** HIGH

### Gaps to Address

**Community property state income attribution (Pitfall 2):**
- Research identified the requirement (9 states mandate 50/50 income splitting for MFS)
- Form 8958 generation logic not fully detailed
- **How to handle:** Flag as "needs deeper research" in Phase 2 planning. Can be scoped out of MVP if clients not in community property states. Validate client address during onboarding to surface this requirement.

**ACA premium tax credit repayment (Pitfall 9):**
- 2026 rule change: no repayment cap for MFS (full subsidy repayment)
- Form 1095-A parsing not in current scope
- **How to handle:** Add warning in UI if filing separately: "⚠️ If you received ACA subsidies, filing separately may require full repayment." Flag for manual review. If Form 1095-A parsing is needed, allocate separate feature for health insurance data extraction.

**HSA contribution limit coordination (Pitfall 12):**
- IRS treats married couples as single tax unit for HSA (family coverage = $8,750 shared)
- Current system doesn't track combined HSA contributions across spouses
- **How to handle:** Add validation in Phase 2: when both spouses have family coverage, sum contributions and enforce $8,750 limit. Show UI: "Husband contributes: $5,000, Wife contributes: $3,750, Combined: $8,750 (limit)."

**Dependent allocation without Form 8332 (Pitfall 10):**
- Requires dependent tracking feature (which child claimed by which spouse)
- Current system may not have dependent model with `claimed_by_client_id` field
- **How to handle:** Phase 2 deliverable. Add `Dependent` model if doesn't exist, add `claimed_by_client_id` FK. UI shows allocation screen when selecting MFS: "Assign each dependent to husband OR wife."

**What-if scenario modeling (deferred feature):**
- High value for tax planning ("what if wife earns $120k instead of $100k?")
- High complexity (state management, recalculation performance)
- **How to handle:** Defer to v2+. MVP provides static comparison (one set of inputs → one set of results). What-if scenarios require interactive recalculation, which adds significant complexity. Can validate demand with tax professionals before building.

**2026 tax rule volatility:**
- OBBBA (One Big Beautiful Bill Act) changed many thresholds for 2026
- AMT exemption phase-out lowered, SALT cap increased to $40k, premium tax credit repayment cap removed
- **How to handle:** Use 2026 published thresholds (IRS inflation adjustments released). Store thresholds in database by tax year, not hardcoded. Allows updating for 2027 without code changes.

## Sources

### Primary (HIGH confidence)

**IRS Official Guidance:**
- [IRS: 2026 Tax Inflation Adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill) — Brackets, standard deductions, AMT exemptions, phase-out thresholds
- [IRS: 401(k) and IRA Limits 2026](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500) — Retirement contribution limits and phase-outs
- [IRS: Student Loan Interest Deduction](https://www.irs.gov/taxtopics/tc456) — MFS ineligibility (no phase-out, just $0)
- [IRS: EITC Eligibility](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc) — MFS restrictions
- [IRS Publication 555: Community Property](https://www.irs.gov/publications/p555) — Income splitting rules for 9 states
- [IRS Publication 504: Divorced or Separated Individuals](https://www.irs.gov/publications/p504) — Dependent allocation, Form 8332

**Tax Software Documentation:**
- [Drake Tax: Split Return Features](https://kb.drakesoftware.com/kb/Drake-Tax/10648.htm) — T/S/J attribution, MFJ vs MFS comparison
- [TaxSlayer Pro: MFJ vs MFS Comparison](https://support.taxslayerpro.com/hc/en-us/articles/360009305513-Desktop-MFJ-vs-MFS-Comparison) — Industry standard features
- [Drake Tax: Net Effect of Filing Separately](https://kb.drakesoftware.com/kb/Drake-Tax/13359.htm) — Comparison report format

**Technical Documentation:**
- [Flask 3.0 Documentation](https://flask.palletsprojects.com/) — Version compatibility, blueprint patterns
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/) — Relationship queries, join optimization
- [Split.js npm](https://www.npmjs.com/package/split.js/v/1.6.5) — Version 1.6.5 installation, API

### Secondary (MEDIUM confidence)

**Tax Professional Resources:**
- [Millan CPA: 2026 IRS Tax Brackets with AMT](https://millancpa.com/insights/2026-irs-tax-brackets-standard-deductions-capital-gains-amt) — Comprehensive 2026 thresholds
- [SmartAsset: Married Filing Separately 2026](https://smartasset.com/taxes/married-filing-jointly-vs-separately) — MFJ vs MFS comparison framework
- [Tax Foundation: 2026 Tax Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) — MFJ vs MFS bracket differences
- [Fidelity: HSA Contribution Limits 2026](https://www.fidelity.com/learning-center/smart-money/hsa-contribution-limits) — Family coverage limit coordination
- [TurboTax: Community Property States](https://turbotax.intuit.com/tax-tips/marriage/five-tax-tips-for-community-property-states/L4jG7cq7Z) — 50/50 income splitting rules

**Implementation Patterns:**
- [Cosmic Python: Service Layer Pattern](https://www.cosmicpython.com/book/chapter_04_service_layer.html) — Flask service layer architecture
- [Modern CSS Layout 2026](https://www.frontendtools.tech/blog/modern-css-layout-techniques-flexbox-grid-subgrid-2025) — Grid vs Flexbox patterns
- [State Management Vanilla JS 2026](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de) — Proxy pattern for reactive state
- [Flask SQLite Threading](https://sqlpey.com/python/solved-how-to-handle-sqlite-threading-issues-in-flask/) — WAL mode, busy timeout configuration

### Tertiary (LOW confidence, validate during implementation)

**Tax Planning Strategies:**
- [Harness: Dual-Income Tax Strategies](https://www.harness.co/articles/dual-income-tax-strategies-married-couples/) — Joint optimization examples
- [Method CPA: High-Income Dual-Income Households](https://methodcpa.com/married-successful-and-overpaying-tax-planning-strategies-for-high-income-dual-income-households/) — Planning scenarios
- [Doctored Money: MFJ vs MFS Implications](https://www.doctoredmoney.org/taxes/mfj-vs-mfs) — Strategy comparisons

**Edge Cases:**
- [Ascensus: HSA Contribution Splitting](https://thelink.ascensus.com/articles/2025/5/12/how-can-hsa-contributions-be-split-between-family-members) — Family coverage allocation rules
- [Western CPE: Premium Tax Credit FAQ 2026](https://www.westerncpe.com/taxbyte/irs-premium-tax-credit-faq-update-what-to-know-for-2026/) — ACA repayment rule changes

---

*Research completed: 2026-02-04*
*Ready for roadmap: YES*

**Next steps:** Create roadmap with 4 phases (Core Calculation → MFS Compliance → Split-Screen UI → Joint Optimization). Use this summary as context for phase planning. Flag community property states and ACA handling for deeper research in Phase 2.
