# ATSA - Advanced Tax Strategy Analyzer

## What This Is

A Flask-based tax analysis tool for tax professionals that handles client management, document upload with OCR extraction, tax form parsing, and strategy recommendations. Now includes full dual-filer support for married couples — allowing both spouses' tax situations to be entered, viewed side-by-side, and analyzed with MFJ vs MFS comparison and personalized strategies.

## Core Value

A tax professional can see both spouses' individual tax pictures side-by-side and instantly understand their combined joint liability — one screen, complete picture.

## Current Milestone: v1.1 Tax Calculator Dual-Entry Mode

**Goal:** Transform the Tax Calculator into a dual-pane tool when filing status involves two spouses — quick calculations with option to persist to clients.

**Target features:**
- Filing status triggers split view (MFJ/MFS → dual pane, Single/HoH → single pane)
- Per-spouse breakdown + joint totals display
- Apply to Client functionality (save quick calculations to client records)

## Previous: v1.0 (Shipped 2026-02-04)

**v1.0 Dual-Filer MFJ/MFS Support** delivered:
- Joint MFJ/MFS tax calculation with accurate bracket computations
- MFS compliance: deduction coordination, SALT cap halving, expense allocation
- Split-screen UI with resizable panels and responsive mobile layout
- Income-type-aware strategies per spouse (LLC→SEP-IRA, W-2→401k)
- Joint optimization strategies (Spousal IRA, Bracket Utilization) with feasibility warnings
- Streamlined workflow: Create Married Couple, document attribution, manual entry

**Tech Stack:** Flask + SQLAlchemy + vanilla JS + SQLite (WAL mode)
**LOC:** ~12,000 Python/JS/HTML/CSS

## Requirements

### Validated

- ✓ Client CRUD with SSN encryption — existing
- ✓ Document upload (PDF, JPG, PNG) with OCR extraction — existing
- ✓ Tax form detection and field parsing — existing
- ✓ Federal tax calculation with bracket-based computation — existing
- ✓ State tax calculation with state-specific brackets — existing
- ✓ Tax strategy recommendations — existing
- ✓ Analysis caching with data version hashing — existing
- ✓ Spouse linking between client records — existing
- ✓ Joint tax calculation (MFJ) — v1.0
- ✓ Separate tax calculation (MFS) — v1.0
- ✓ MFJ vs MFS comparison with recommendation — v1.0
- ✓ Income source attribution (T/S/J) — v1.0
- ✓ Credit availability by filing status — v1.0
- ✓ QBI threshold by filing status — v1.0
- ✓ Bidirectional cache invalidation — v1.0
- ✓ SQLite WAL mode — v1.0
- ✓ JointAnalysisSummary model — v1.0
- ✓ JointAnalysisService — v1.0
- ✓ Joint analysis API endpoints — v1.0
- ✓ Deduction method enforcement (MFS) — v1.0
- ✓ SALT cap by filing status — v1.0
- ✓ Shared expense allocation — v1.0
- ✓ Split-screen layout — v1.0
- ✓ Resizable split panes (Split.js) — v1.0
- ✓ Joint comparison section — v1.0
- ✓ Income source breakdown — v1.0
- ✓ Filing status comparison report — v1.0
- ✓ Per-spouse tax strategies — v1.0
- ✓ Joint optimization strategies — v1.0
- ✓ Strategy feasibility flags — v1.0
- ✓ Spouse linking workflow — v1.0
- ✓ Document upload attribution — v1.0
- ✓ Dual data entry support — v1.0

### Active

- [ ] Tax Calculator split view on MFJ/MFS selection
- [ ] Per-spouse tax breakdown in calculator
- [ ] Joint totals display in calculator
- [ ] Apply to Client functionality

### Out of Scope

- Dependent filing / trust returns — complexity beyond current scope
- Real-time collaboration — single-operator tool
- Authentication system — single trusted operator
- Mobile app — desktop browser workflow for tax professionals
- What-if scenario modeling — deferred to v2
- Community property state handling — deferred to v2

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build on existing spouse_id linking | Already works, avoid migration risk | ✓ Good |
| Both upload and manual data entry | Flexibility for different client situations | ✓ Good |
| MFJ + MFS support (not just MFJ) | Comparison is critical for tax planning | ✓ Good |
| Split-screen: husband left, wife right | Matches how tax pros think about joint returns | ✓ Good |
| 4-phase structure (Calc→Compliance→UI→Strategies) | Tax accuracy before display | ✓ Good |
| Split.js CDN instead of npm | No build step, 2kb library | ✓ Good |
| Service layer orchestration | Preserves existing code, clear separation | ✓ Good |
| Bidirectional cache invalidation | Prevents stale data | ✓ Good |
| Income type detection from form types | Personalizes strategies | ✓ Good |

## Constraints

- **Tech stack**: Flask + vanilla JS + SQLite — no framework changes
- **Data model**: Build on existing spouse_id linking
- **Analysis engine**: Extend existing AnalysisEngine
- **UI pattern**: Split-screen in Jinja2 + vanilla CSS/JS

---
*Last updated: 2026-02-04 after v1.1 milestone start*
