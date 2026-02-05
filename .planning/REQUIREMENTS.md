# Requirements: ATSA v1.1 Tax Calculator Dual-Entry Mode

**Defined:** 2026-02-04
**Core Value:** A tax professional can see both spouses' individual tax pictures side-by-side and instantly understand their combined joint liability — one screen, complete picture.

## v1.1 Requirements

Requirements for Tax Calculator dual-entry mode. Each maps to roadmap phases.

### Calculator UI

- [ ] **CALC-01**: When MFJ selected, calculator shows split-screen with husband (left) and wife (right) input panes
- [ ] **CALC-02**: When MFS selected, calculator shows split-screen with husband (left) and wife (right) input panes
- [ ] **CALC-03**: Each spouse pane has income fields (amount, frequency toggle, source dropdown)
- [ ] **CALC-04**: Each spouse pane has salary/distributions fields when S-Corp income source selected
- [ ] **CALC-05**: Each spouse pane has independent state selection
- [ ] **CALC-06**: Single/HoH/QSS filing statuses retain single-pane behavior (current)

### Calculator Results

- [ ] **RSLT-01**: Results show per-spouse tax breakdown (federal, state, effective rate per spouse)
- [ ] **RSLT-02**: Results show joint totals (combined federal, combined state, total tax)
- [ ] **RSLT-03**: Results show MFJ vs MFS comparison when both can be calculated

### Apply to Client

- [ ] **SAVE-01**: Apply to Client button visible after dual-pane calculation
- [ ] **SAVE-02**: Apply to Client can create new client records from calculator data
- [ ] **SAVE-03**: Apply to Client can link to existing unlinked clients

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dependent allocation per spouse | Complexity — deferred to future milestone |
| Community property state handling | Requires Form 8958 logic — deferred |
| What-if scenario modeling | High complexity — deferred to v2 |
| Calculator history/save slots | Not requested — quick calculation tool |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CALC-01 | TBD | Pending |
| CALC-02 | TBD | Pending |
| CALC-03 | TBD | Pending |
| CALC-04 | TBD | Pending |
| CALC-05 | TBD | Pending |
| CALC-06 | TBD | Pending |
| RSLT-01 | TBD | Pending |
| RSLT-02 | TBD | Pending |
| RSLT-03 | TBD | Pending |
| SAVE-01 | TBD | Pending |
| SAVE-02 | TBD | Pending |
| SAVE-03 | TBD | Pending |

**Coverage:**
- v1.1 requirements: 12 total
- Mapped to phases: 0
- Unmapped: 12

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 after initial definition*
