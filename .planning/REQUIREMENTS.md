# Requirements — Dual-Filer Tax Analysis

**Project:** ATSA - Advanced Tax Strategy Analyzer
**Milestone:** Dual-Filer MFJ/MFS Support
**Generated:** 2026-02-04
**Source:** Research synthesis + user scoping decisions

---

## v1 — Core Dual-Filer (This Milestone)

### Calculation Engine

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-01 | **Joint tax calculation (MFJ)**: Calculate combined income through MFJ brackets, deductions, and credits from two linked clients' data | Must | Table Stakes |
| REQ-02 | **Separate tax calculation (MFS)**: Calculate each spouse's income through MFS brackets (mirrors single filer) with correct thresholds | Must | Table Stakes |
| REQ-03 | **MFJ vs MFS comparison**: Show three-column comparison — MFJ outcome, MFS spouse 1, MFS spouse 2 — with net dollar difference and recommendation | Must | Table Stakes |
| REQ-04 | **Income source attribution (T/S/J)**: Tag each income source as Taxpayer, Spouse, or Joint (split 50/50) for accurate MFS calculation | Must | Table Stakes |
| REQ-05 | **Credit availability by filing status**: Enforce MFS credit restrictions — EITC unavailable, student loan interest $0, education credits unavailable, adoption credit unavailable | Must | Table Stakes |
| REQ-06 | **QBI threshold by filing status**: Use MFS thresholds ($191,950-$266,950) not MFJ thresholds ($383,900-$533,900) when calculating QBI deduction for MFS | Must | Pitfall #3 |
| REQ-07 | **Standard deduction amounts**: MFJ $32,200, MFS $16,100 per spouse for 2026 | Must | Table Stakes |
| REQ-08 | **Bidirectional cache invalidation**: Extend data_version_hash to include spouse's ExtractedData when spouse_id exists; either spouse's data change invalidates joint analysis | Must | Pitfall #4 |

### MFS Compliance

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-09 | **Deduction method enforcement**: If one spouse itemizes on MFS, the other must also itemize — blocking validation with warning message | Must | Table Stakes / IRS Rule |
| REQ-10 | **SALT cap by status**: MFJ/Single $40,000 cap, MFS $20,000 per spouse for 2026 | Must | Pitfall #11 |
| REQ-11 | **Shared expense allocation**: Allow mortgage interest, property taxes to be attributed to T/S/Both with percentage split for MFS accuracy | Should | Table Stakes |

### Infrastructure

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-12 | **SQLite WAL mode**: Enable WAL journal mode and 30-second busy timeout to prevent "database locked" errors during joint analysis | Must | Pitfall #5 |
| REQ-13 | **JointAnalysisSummary model**: New model to store joint analysis results with combined hash, MFJ totals, MFS totals, comparison data | Must | Architecture |
| REQ-14 | **JointAnalysisService**: Service class orchestrating dual analysis — fetch both spouses, run individual analyses, calculate MFJ, calculate MFS, generate comparison | Must | Architecture |
| REQ-15 | **Joint analysis API endpoints**: Blueprint with routes for triggering joint analysis, retrieving results, and refreshing stale analyses | Must | Architecture |

### Split-Screen UI

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-16 | **Split-screen layout**: Husband left panel, wife right panel, each showing individual tax picture (income, deductions, tax liability) | Must | User Decision |
| REQ-17 | **Resizable split panes**: Split.js integration for draggable divider between spouse panels | Should | Research |
| REQ-18 | **Joint comparison section**: Bottom section showing MFJ vs MFS cards with recommendation, dollar difference, and reasons | Must | User Decision |
| REQ-19 | **Income source breakdown**: At-a-glance display per spouse — "Husband: $250k LLC, Wife: $100k W-2" | Should | Differentiator |
| REQ-20 | **Filing status comparison report**: Formatted three-column layout — MFJ total, MFS Spouse 1, MFS Spouse 2 — with line items for income, deductions, credits, tax liability | Must | Table Stakes |

### Strategies

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-21 | **Per-spouse tax strategies**: Individual recommendations based on each spouse's income type (LLC → SEP-IRA/QBI, W-2 → 401k/HSA) | Must | User Decision |
| REQ-22 | **Joint optimization strategies**: Strategies only available when filing jointly — spousal IRA, bracket utilization, income averaging benefits | Must | User Decision |
| REQ-23 | **Strategy feasibility flags**: Warnings when strategy is incompatible with filing status — "SEP-IRA only available if filing jointly" | Should | Differentiator |

### Workflow

| ID | Requirement | Priority | Source |
|----|------------|----------|--------|
| REQ-24 | **Spouse linking workflow**: UI flow to create both clients, link via spouse_id, then navigate to joint analysis | Must | User Decision |
| REQ-25 | **Document upload attribution**: Tag uploaded documents to Taxpayer vs Spouse during upload flow | Should | Table Stakes |
| REQ-26 | **Dual data entry support**: Both document upload with OCR AND manual income entry for each spouse | Must | User Decision |

---

## v2 — Advanced Features (Future Milestone)

| ID | Feature | Rationale for Deferral |
|----|---------|----------------------|
| REQ-V2-01 | **What-if scenario modeling** | High complexity — real-time recalculation, state management, hypothetical editing UI |
| REQ-V2-02 | **Community property state handling** | 9 states with different rules, Form 8958 generation, significant complexity |
| REQ-V2-03 | **Deduction allocation optimizer** | Suggest optimal expense splits — advanced feature, tax pros can manually optimize |
| REQ-V2-04 | **Prior year comparison** | Requires historical data structure, year-over-year trend analysis |
| REQ-V2-05 | **Visual bracket utilization chart** | Chart showing income distribution across brackets — enhancement over text comparison |
| REQ-V2-06 | **Dependent allocation UI** | Each child claimed by one spouse on MFS — requires Dependent model, Form 8332 |
| REQ-V2-07 | **ACA premium tax credit handling** | 2026 MFS full repayment rule — needs Form 1095-A parsing |
| REQ-V2-08 | **AMT exemption halving for MFS** | $70,100 vs $140,200 — moderate complexity, affects fewer clients |
| REQ-V2-09 | **HSA contribution limit coordination** | Family coverage $8,750 shared — requires cross-spouse validation |
| REQ-V2-10 | **Retirement phase-out validation** | MFS $0-$10k Roth IRA range — extremely narrow, needs careful implementation |

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-select best filing status | Removes tax professional judgment — show comparison, let pro decide |
| Quick MFS without income attribution | Creates inaccurate returns — T/S/J attribution is required |
| Combined MFJ/MFS strategy list | Confusing — must be separated by filing status |
| Allow mismatched deduction methods on MFS | IRS violation — must enforce matching |
| Real-time multi-user collaboration | Single-operator tool, no multi-user needed |
| Mobile-first interface | Desktop-first for tax professionals with large monitors |
| Automated strategy execution | Strategies are recommendations, not automated actions |
| Dependent filing / trust returns | Beyond current scope, MFJ/MFS only |
| Authentication system | Single trusted operator |

---

## Anti-Patterns to Avoid

1. **Never auto-select filing status** — Always show comparison, let tax professional decide
2. **Never skip income attribution for MFS** — Every income source must be tagged T/S/J
3. **Never allow mismatched deduction methods on MFS** — IRS rule, not optional
4. **Never mix MFJ and MFS strategies in one list** — Separate sections with clear context
5. **Never allocate 100% of joint income to one spouse** — Require realistic attribution

---

## Requirement Dependencies

```
REQ-12 (WAL mode) ─── no dependencies, do first
REQ-13 (Model) ──┐
REQ-14 (Service) ─┤── REQ-04 (T/S/J attribution)
REQ-15 (API) ─────┘       │
                           ▼
REQ-01 (MFJ calc) ◄── REQ-07 (Standard deductions)
REQ-02 (MFS calc) ◄── REQ-06 (QBI thresholds), REQ-05 (Credit restrictions)
                           │
                           ▼
REQ-03 (Comparison) ◄── REQ-01 + REQ-02
REQ-09 (Deduction enforcement) ◄── REQ-02
REQ-10 (SALT cap) ◄── REQ-02
                           │
                           ▼
REQ-16-20 (UI) ◄── REQ-15 (API endpoints)
REQ-21-23 (Strategies) ◄── REQ-03 (Comparison results)
REQ-24-26 (Workflow) ── parallel with UI
```

---

## Success Criteria

The milestone is complete when a tax professional can:

1. Create two client records (husband + wife), link as spouses
2. Enter/upload tax data for each spouse (husband: $250k LLC, wife: $100k W-2)
3. See a split-screen view with husband's tax picture on left, wife's on right
4. See a consolidated MFJ vs MFS comparison showing which status saves money with dollar difference
5. See individual strategy recommendations per spouse
6. See joint optimization strategies for the couple
7. Have the comparison automatically refresh when either spouse's data changes

---

*Generated: 2026-02-04 from research synthesis*
*26 v1 requirements | 10 v2 deferred | 9 out of scope*
