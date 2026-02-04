# ATSA - Advanced Tax Strategy Analyzer

## What This Is

A Flask-based tax analysis tool for tax professionals that handles client management, document upload with OCR extraction, tax form parsing, and strategy recommendations. The next milestone adds dual-filer support for married couples — allowing both spouses' tax situations to be entered, viewed side-by-side, and analyzed as a joint return with MFJ vs MFS comparison.

## Core Value

A tax professional can see both spouses' individual tax pictures side-by-side and instantly understand their combined joint liability — one screen, complete picture.

## Requirements

### Validated

- ✓ Client CRUD with SSN encryption — existing
- ✓ Document upload (PDF, JPG, PNG) with OCR extraction — existing
- ✓ Tax form detection and field parsing (W-2, 1099, 1040, Schedules) — existing
- ✓ Federal tax calculation with bracket-based computation — existing
- ✓ State tax calculation with state-specific brackets — existing
- ✓ Tax strategy recommendations (retirement, business, deductions, education) — existing
- ✓ Analysis caching with data version hashing — existing
- ✓ Spouse linking between client records (Client.spouse_id) — existing
- ✓ Tax calculator with bracket/deduction lookups — existing
- ✓ Analysis summary with income source breakdown — existing

### Active

- [ ] Dual-filer data entry: enter income/deductions for each spouse via upload or manual entry
- [ ] Split-screen analysis view: husband left, wife right, showing individual tax pictures
- [ ] Consolidated joint return calculation: combined income through joint brackets
- [ ] MFJ vs MFS comparison: show which filing status saves more with dollar difference
- [ ] Per-filer tax strategies: individual recommendations for each spouse
- [ ] Joint optimization strategies: combined strategies that optimize the joint return
- [ ] Enhanced spouse linking workflow: create both clients, link, then analyze together

### Out of Scope

- Dependent filing / trust returns — complexity beyond current scope, MFJ/MFS only
- Real-time collaboration — single-operator tool, no multi-user needed
- Authentication system — single trusted operator, no login required
- Mobile app — desktop browser is the workflow for tax professionals

## Context

- Existing codebase has a `spouse_id` field on Client model with bidirectional linking
- Analysis engine currently analyzes one client at a time — needs to support joint analysis
- Tax calculator already handles all filing statuses including married_joint and married_separate
- Frontend is vanilla HTML/CSS/JS with Jinja2 templates — no framework
- Real use case: husband with LLC ($250k) + wife with W-2 ($100k) — different income types, different strategies
- Tax brackets for MFJ are already seeded in the database
- The split-view UI is the centerpiece — this is what the tax professional looks at with the client

## Constraints

- **Tech stack**: Flask + vanilla JS + SQLite — no framework changes, build on existing patterns
- **Data model**: Build on existing spouse_id linking — don't redesign the client model
- **Analysis engine**: Extend existing AnalysisEngine — don't rewrite, add joint analysis capability
- **UI pattern**: Split-screen layout must work in existing template structure (Jinja2 + vanilla CSS/JS)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build on existing spouse_id linking | Already works, avoid migration risk | — Pending |
| Both upload and manual data entry | Flexibility for different client situations | — Pending |
| MFJ + MFS support (not just MFJ) | Comparison is critical for tax planning value | — Pending |
| Split-screen: husband left, wife right | Matches how tax pros think about joint returns | — Pending |

---
*Last updated: 2026-02-04 after initialization*
