# Roadmap: ATSA v1.1 Tax Calculator Dual-Entry Mode

## Overview

Transform the Tax Calculator into a dual-pane tool when filing status involves two spouses (MFJ/MFS), enabling tax professionals to see both spouses' individual tax pictures side-by-side with combined totals. Optional persistence to client records enables quick what-if calculations that can become permanent client data.

## Milestones

- v1.0 Dual-Filer MFJ/MFS Support (Phases 1-4) - shipped 2026-02-04
- v1.1 Tax Calculator Dual-Entry Mode (Phases 5-6) - in progress

## Phases

- [ ] **Phase 5: Calculator Dual-Pane Mode** - Split-screen calculator UI with per-spouse inputs and combined results
- [ ] **Phase 6: Apply to Client** - Persist calculator data to new or existing client records

## Phase Details

### Phase 5: Calculator Dual-Pane Mode
**Goal**: Tax professionals can perform married-couple calculations with both spouses' data visible simultaneously
**Depends on**: Phase 4 (v1.0 complete)
**Requirements**: CALC-01, CALC-02, CALC-03, CALC-04, CALC-05, CALC-06, RSLT-01, RSLT-02, RSLT-03
**Success Criteria** (what must be TRUE):
  1. Selecting MFJ or MFS filing status transforms calculator to dual-pane view with husband (left) and wife (right) input areas
  2. Each spouse pane accepts income fields with amount, frequency toggle, and source dropdown (including S-Corp salary/distributions)
  3. Each spouse pane allows independent state selection for state tax calculation
  4. Single/HoH/QSS filing statuses display existing single-pane calculator (no regression)
  5. Results display per-spouse breakdown (federal, state, effective rate) and joint totals (combined federal, combined state, total tax)
  6. When both MFJ and MFS can be calculated, results show comparison between the two filing methods
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md -- Backend /calculate-dual endpoint + HTML template restructure + CSS styles
- [ ] 05-02-PLAN.md -- Full calculator.js rewrite with dual-pane logic, results display, and MFJ vs MFS comparison

### Phase 6: Apply to Client
**Goal**: Calculator results can be persisted to client records for permanent storage
**Depends on**: Phase 5
**Requirements**: SAVE-01, SAVE-02, SAVE-03
**Success Criteria** (what must be TRUE):
  1. After a dual-pane calculation, an "Apply to Client" button is visible
  2. User can create new client records (husband and wife) from calculator data with one action
  3. User can link calculator data to existing unlinked clients in the system
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 5. Calculator Dual-Pane Mode | v1.1 | 1/2 | In progress | - |
| 6. Apply to Client | v1.1 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-04*
*Continues from v1.0 (Phases 1-4 shipped 2026-02-04)*
