# Roadmap -- Dual-Filer MFJ/MFS Support

**Project:** ATSA - Advanced Tax Strategy Analyzer
**Milestone:** Dual-Filer MFJ/MFS Support
**Phases:** 4
**Depth:** Standard
**Created:** 2026-02-04

---

## Overview

This milestone adds dual-filer support for married couples, enabling a tax professional to enter both spouses' data, see individual tax pictures side-by-side, and compare MFJ vs MFS filing status with dollar-level savings recommendations. The roadmap builds from calculation accuracy outward to UI and workflow polish -- tax numbers must be correct before anything gets displayed.

---

## Phase 1: Core Dual-Filer Calculation Engine

**Goal:** A joint analysis can be triggered for two linked spouses and returns accurate MFJ totals, MFS totals per spouse, and a comparison with dollar difference and recommendation -- all cached and invalidated correctly.

**Dependencies:** None (foundation phase)

**Requirements:**
| ID | Requirement |
|----|-------------|
| REQ-01 | Joint tax calculation (MFJ) -- combined income through MFJ brackets |
| REQ-02 | Separate tax calculation (MFS) -- each spouse through MFS brackets |
| REQ-03 | MFJ vs MFS comparison -- three-column comparison with net dollar difference |
| REQ-04 | Income source attribution (T/S/J) -- tag each income source for accurate MFS |
| REQ-05 | Credit availability by filing status -- enforce MFS credit restrictions |
| REQ-06 | QBI threshold by filing status -- MFS uses $191,950 not $383,900 |
| REQ-07 | Standard deduction amounts -- MFJ $32,200, MFS $16,100 per spouse |
| REQ-08 | Bidirectional cache invalidation -- spouse data change invalidates joint analysis |
| REQ-12 | SQLite WAL mode -- prevent "database locked" errors during joint analysis |
| REQ-13 | JointAnalysisSummary model -- store joint analysis results with combined hash |
| REQ-14 | JointAnalysisService -- service class orchestrating dual analysis |
| REQ-15 | Joint analysis API endpoints -- blueprint with routes for triggering and retrieving |

**Success Criteria:**
1. Tax professional triggers joint analysis for two linked clients and receives a JSON response containing MFJ totals, MFS-spouse-1 totals, MFS-spouse-2 totals, dollar difference, and recommended filing status
2. For the real use case (husband $250k LLC + wife $100k W-2), MFS shows reduced QBI deduction for husband (above $191,950 threshold) and MFJ shows full QBI deduction (below $383,900 threshold) -- dollar amounts differ
3. MFS calculation returns $0 for EITC, student loan interest deduction, and education credits -- these credits appear in MFJ but not MFS
4. Updating either spouse's tax data (uploading a new W-2) causes the next joint analysis request to recalculate fresh results instead of returning stale cached data
5. Two simultaneous requests (analysis in one tab, document upload in another) both complete without "database is locked" errors

**Key Files to Create/Modify:**
- `services/joint_analysis_service.py` (NEW) -- JointAnalysisService with analyze_joint(), calculate_mfj_scenario(), calculate_mfs_scenario()
- `models/joint_analysis.py` (NEW) -- JointAnalysisSummary model
- `routes/joint_analysis.py` (NEW) -- Blueprint with GET/POST endpoints
- `services/analysis_engine.py` (MODIFY) -- extend _calculate_data_version_hash() to include spouse data
- `database/init_db.py` (MODIFY) -- enable WAL mode, register new model
- `app.py` (MODIFY) -- register joint_analysis blueprint

**Pitfalls to Address:**
- Pitfall #3 (Credit disqualification) -- filing status eligibility matrix for each credit
- Pitfall #4 (QBI threshold confusion) -- threshold lookup by exact filing status, not "married" keyword
- Pitfall #5 (Cache invalidation) -- combined hash from both spouses' data version hashes
- Pitfall #6 (SQLite concurrency) -- WAL mode + 30-second busy timeout
- Pitfall #7 (Retirement phase-out) -- MFS uses $0-$10,000 range, not half of MFJ
- Pitfall #13 (Rounding) -- use Decimal throughout, round only at display

---

## Phase 2: MFS-Specific Compliance Logic

**Goal:** MFS calculations enforce all IRS compliance rules -- deduction coordination, SALT cap halving, and shared expense allocation -- so that MFS numbers are legally correct, not just mathematically computed.

**Dependencies:** Phase 1 (MFS calculation engine must exist before compliance rules can be layered on)

**Requirements:**
| ID | Requirement |
|----|-------------|
| REQ-09 | Deduction method enforcement -- if one spouse itemizes on MFS, the other must also itemize |
| REQ-10 | SALT cap by status -- MFS $20,000 per spouse, not $40,000 |
| REQ-11 | Shared expense allocation -- mortgage interest, property taxes attributed T/S/Both with percentage split |

**Success Criteria:**
1. When one spouse selects itemized deductions for MFS, the system blocks the other spouse from using standard deduction and displays a warning explaining the IRS coordination rule
2. A California couple with $60,000 in combined state/local taxes sees SALT capped at $20,000 per spouse on MFS (not $40,000) and $40,000 total on MFJ -- the difference appears in the comparison
3. Mortgage interest of $24,000 can be allocated as 60% husband / 40% wife for MFS, and the split correctly flows through each spouse's itemized deduction calculation

**Key Files to Create/Modify:**
- `services/joint_analysis_service.py` (MODIFY) -- add deduction coordination validation, SALT cap enforcement, expense allocation logic
- `models/joint_analysis.py` (MODIFY) -- add fields for deduction method tracking, expense allocation
- `routes/joint_analysis.py` (MODIFY) -- add validation endpoints for deduction coordination

**Pitfalls to Address:**
- Pitfall #1 (Itemized deduction coordination) -- blocking validation with clear warning message
- Pitfall #11 (SALT cap halving) -- cap enforcement by filing status in itemized deduction calculation
- Pitfall #14 (Filing status display confusion) -- clear labels: "Married Filing Jointly (MFJ)" not just "Married"
- Pitfall #15 (Standard deduction display) -- show MFS $16,100 as "half of joint amount"

---

## Phase 3: Split-Screen UI and Comparison View

**Goal:** A tax professional sees both spouses' individual tax pictures side-by-side on one screen with a consolidated MFJ vs MFS comparison below -- the centerpiece view they use with clients.

**Dependencies:** Phase 1 (API endpoints must return joint analysis data), Phase 2 (compliance rules must be enforced so displayed numbers are correct)

**Requirements:**
| ID | Requirement |
|----|-------------|
| REQ-16 | Split-screen layout -- husband left panel, wife right panel, each showing individual tax picture |
| REQ-17 | Resizable split panes -- Split.js integration for draggable divider |
| REQ-18 | Joint comparison section -- bottom section with MFJ vs MFS cards, recommendation, dollar difference |
| REQ-19 | Income source breakdown -- at-a-glance display per spouse ("Husband: $250k LLC, Wife: $100k W-2") |
| REQ-20 | Filing status comparison report -- three-column layout: MFJ total, MFS Spouse 1, MFS Spouse 2 with line items |

**Success Criteria:**
1. Tax professional navigates to the joint analysis page and sees husband's tax summary on the left and wife's tax summary on the right, each showing income, deductions, and tax liability
2. Dragging the divider between panels resizes them smoothly, and the layout stacks vertically on screens narrower than 768px
3. Below the split panels, a comparison section shows MFJ total tax, MFS combined tax, dollar difference, and a clear recommendation with reasons (e.g., "MFJ saves $4,200 because QBI deduction is fully available")
4. Each spouse panel shows an income source breakdown at the top (e.g., "LLC Income: $250,000" or "W-2 Wages: $100,000") without requiring the user to drill into details
5. The three-column comparison report shows line-by-line breakdown -- gross income, adjustments, AGI, deductions, taxable income, tax liability -- for MFJ and each MFS spouse

**Key Files to Create/Modify:**
- `templates/joint_analysis.html` (NEW) -- split-screen template with Jinja2 structure
- `static/js/joint_analysis.js` (NEW) -- loadJointAnalysis(), renderSpousePanel(), renderFilingComparison()
- `static/css/joint_analysis.css` (NEW) -- split-screen grid layout, responsive stacking, comparison cards
- `app.py` (MODIFY) -- add route for joint analysis template page
- Split.js loaded via CDN in template

**Pitfalls to Address:**
- Pitfall #14 (Filing status display confusion) -- labels say "Married Filing Jointly (MFJ)" not "Married"
- Pitfall #15 (Standard deduction display) -- show "MFS: $16,100 each (half of joint)" with context

---

## Phase 4: Dual-Filer Strategies and Workflow

**Goal:** Each spouse sees personalized strategy recommendations for their income type, the couple sees joint optimization strategies available only when filing together, and the full workflow -- linking spouses, entering data, viewing analysis -- is smooth end-to-end.

**Dependencies:** Phase 1 (calculation engine for strategy inputs), Phase 3 (UI must exist to display strategies and workflow improvements)

**Requirements:**
| ID | Requirement |
|----|-------------|
| REQ-21 | Per-spouse tax strategies -- individual recommendations based on income type (LLC -> SEP-IRA, W-2 -> 401k) |
| REQ-22 | Joint optimization strategies -- strategies only available when filing jointly (spousal IRA, bracket utilization) |
| REQ-23 | Strategy feasibility flags -- warnings when strategy is incompatible with filing status |
| REQ-24 | Spouse linking workflow -- UI flow to create both clients, link, navigate to joint analysis |
| REQ-25 | Document upload attribution -- tag uploaded documents to Taxpayer vs Spouse |
| REQ-26 | Dual data entry support -- both document upload with OCR AND manual income entry per spouse |

**Success Criteria:**
1. Husband with LLC income sees SEP-IRA and QBI optimization recommendations; wife with W-2 income sees 401(k) maximization and HSA recommendations -- each personalized to their income type
2. When MFJ is recommended, a joint strategies section shows strategies like "Spousal IRA: Wife can contribute to IRA using husband's earned income" and "Bracket Utilization: Combined income uses wider MFJ brackets, saving $X"
3. A strategy that requires MFJ (e.g., spousal IRA) shows a warning flag when viewing MFS: "This strategy requires filing jointly"
4. Starting from the client list, a user can create both spouse records, link them, and land on the joint analysis page in a clear linear flow without backtracking
5. When uploading a W-2, the user can tag it as belonging to the taxpayer or spouse, and the extracted data flows to the correct client record

**Key Files to Create/Modify:**
- `services/tax_strategies.py` (MODIFY) -- add per-spouse strategy generation, joint optimization strategies, feasibility flags
- `services/joint_analysis_service.py` (MODIFY) -- integrate strategy generation into joint analysis flow
- `templates/clients.html` (MODIFY) -- spouse linking workflow improvements
- `templates/upload.html` (MODIFY) -- document attribution (taxpayer vs spouse) during upload
- `routes/clients.py` (MODIFY) -- improved spouse linking endpoints
- `routes/documents.py` (MODIFY) -- document attribution during upload
- `static/js/joint_analysis.js` (MODIFY) -- render per-spouse and joint strategy sections

---

## Coverage Map

```
Calculation Engine:
  REQ-01 (MFJ calc)              -> Phase 1
  REQ-02 (MFS calc)              -> Phase 1
  REQ-03 (MFJ vs MFS comparison) -> Phase 1
  REQ-04 (Income attribution)    -> Phase 1
  REQ-05 (Credit availability)   -> Phase 1
  REQ-06 (QBI thresholds)        -> Phase 1
  REQ-07 (Standard deduction)    -> Phase 1
  REQ-08 (Cache invalidation)    -> Phase 1

MFS Compliance:
  REQ-09 (Deduction enforcement) -> Phase 2
  REQ-10 (SALT cap)              -> Phase 2
  REQ-11 (Shared expenses)       -> Phase 2

Infrastructure:
  REQ-12 (WAL mode)              -> Phase 1
  REQ-13 (JointAnalysisSummary)  -> Phase 1
  REQ-14 (JointAnalysisService)  -> Phase 1
  REQ-15 (API endpoints)         -> Phase 1

Split-Screen UI:
  REQ-16 (Split layout)          -> Phase 3
  REQ-17 (Resizable panes)       -> Phase 3
  REQ-18 (Comparison section)    -> Phase 3
  REQ-19 (Income breakdown)      -> Phase 3
  REQ-20 (Comparison report)     -> Phase 3

Strategies:
  REQ-21 (Per-spouse strategies)  -> Phase 4
  REQ-22 (Joint strategies)       -> Phase 4
  REQ-23 (Feasibility flags)      -> Phase 4

Workflow:
  REQ-24 (Spouse linking)         -> Phase 4
  REQ-25 (Document attribution)   -> Phase 4
  REQ-26 (Dual data entry)        -> Phase 4

Mapped: 26/26
Orphaned: 0
```

---

## Progress

| Phase | Name | Requirements | Status |
|-------|------|:------------:|--------|
| 1 | Core Dual-Filer Calculation Engine | 12 | Not Started |
| 2 | MFS-Specific Compliance Logic | 3 | Not Started |
| 3 | Split-Screen UI and Comparison View | 5 | Not Started |
| 4 | Dual-Filer Strategies and Workflow | 6 | Not Started |

---

*Roadmap created: 2026-02-04*
*Next: Plan Phase 1*
