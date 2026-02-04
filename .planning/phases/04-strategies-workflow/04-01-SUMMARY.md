---
phase: 04-strategies-workflow
plan: 01
subsystem: client-workflow
tags: [spouse-linking, workflow, ui, api]

dependency-graph:
  requires: [03-split-screen-ui]
  provides: [create-couple-endpoint, couple-modal, spouse-workflow]
  affects: [04-02-strategy-cards, 04-03-export]

tech-stack:
  added: []
  patterns: [bidirectional-linking, form-to-redirect-workflow]

key-files:
  created: []
  modified:
    - routes/clients.py
    - templates/clients.html
    - static/js/clients.js

decisions:
  - Shared filing status for both spouses (simpler UX, can be changed later)
  - Two-column modal layout for visual spouse pairing
  - Immediate redirect to joint analysis after creation

metrics:
  duration: 2m 39s
  completed: 2026-02-04
---

# Phase 4 Plan 01: Spouse Linking Workflow Summary

**One-liner:** Create Married Couple workflow with two-column modal form, bidirectional spouse linking, and automatic redirect to joint analysis.

## What Was Built

### 1. POST /api/clients/create-couple Endpoint (routes/clients.py)

New endpoint that creates both spouse records in a single atomic operation:
- Validates required fields (first_name, last_name)
- Validates filing status is married_joint or married_separate
- Creates spouse1 first, flushes to get ID
- Creates spouse2 with spouse_id pointing to spouse1
- Updates spouse1.spouse_id to point to spouse2 (bidirectional)
- Returns both spouse objects and joint_analysis_url

```python
@clients_bp.route('/clients/create-couple', methods=['POST'])
def create_couple():
    # Creates two linked Client records atomically
    # Returns: { spouse1, spouse2, joint_analysis_url }
```

### 2. Create Married Couple Button and Modal (templates/clients.html)

- Added "Create Married Couple" button next to "Add New Client"
- Two-column modal form with:
  - Spouse 1 column: first name, last name, email, phone
  - Spouse 2 column: first name, last name, email, phone
  - Shared filing status dropdown (MFJ/MFS)
  - Submit button: "Create Couple & View Analysis"

### 3. JavaScript Handlers (static/js/clients.js)

- `showCoupleModal()` - Opens modal and resets form
- `closeCoupleModal()` - Closes modal
- `createCouple(event)` - Async function that:
  - Collects form data for both spouses
  - POSTs to /api/clients/create-couple
  - Redirects to joint_analysis_url on success
- Updated window.onclick to close both modals when clicking outside

## Workflow Flow

```
[Clients Page]
     |
     v
[Click "Create Married Couple"]
     |
     v
[Two-Column Modal Form]
     |
     v
[Fill Spouse 1 + Spouse 2 Details]
     |
     v
[Select Filing Status (MFJ/MFS)]
     |
     v
[Click "Create Couple & View Analysis"]
     |
     v
[POST /api/clients/create-couple]
     |
     v
[Both clients created with bidirectional spouse_id]
     |
     v
[Redirect to /joint-analysis.html?spouse1_id=X&spouse2_id=Y]
     |
     v
[Joint Analysis Page with spouses pre-selected]
```

## Verification Results

| Test | Result |
|------|--------|
| Endpoint creates two clients | PASS |
| Clients have bidirectional spouse_id | PASS |
| Returns joint_analysis_url with both IDs | PASS |
| Modal renders with two-column layout | PASS |
| JavaScript syntax valid | PASS |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Commit | Description |
|--------|-------------|
| e955598 | feat(04-01): add POST /api/clients/create-couple endpoint |
| 0eee0cb | feat(04-01): add Create Married Couple button and modal to clients page |
| aafc557 | feat(04-01): add JavaScript handlers for couple creation workflow |

## Requirements Addressed

- **REQ-24:** Spouse linking workflow - UI flow to create both clients, link, navigate to joint analysis

## Next Phase Readiness

Plan 04-02 (Strategy Cards) can proceed. No blockers.
