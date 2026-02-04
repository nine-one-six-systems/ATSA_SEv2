---
phase: 04-strategies-workflow
plan: 02
subsystem: ui
tags: [attribution, document-upload, manual-entry, dual-filer, form-data]

# Dependency graph
requires:
  - phase: 04-01
    provides: spouse linking workflow, bidirectional spouse_id
provides:
  - Document attribution column (taxpayer/spouse/joint)
  - Manual entry endpoint for income data without documents
  - Attribution selector UI for dual-filer document management
  - Tabbed interface for Document Upload vs Manual Entry
affects: [04-03, 04-04, joint-analysis, document-processing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Attribution routing pattern for spouse data entry
    - Tab-based UI for alternative data entry methods

key-files:
  created: []
  modified:
    - models/document.py
    - models/extracted_data.py
    - routes/documents.py
    - templates/upload.html
    - static/js/upload.js

key-decisions:
  - "ExtractedData.document_id made nullable to support manual entries without uploaded documents"
  - "Attribution routes data to spouse's client_id when 'spouse' is selected"
  - "Attribution selector only visible when selected client has spouse_id linked"

patterns-established:
  - "Attribution pattern: Document stores attribution, extracted data routes to target client"
  - "Manual entry creates ExtractedData records with document_id=NULL"

# Metrics
duration: 12min
completed: 2026-02-04
---

# Phase 4 Plan 02: Document Attribution and Manual Entry Summary

**Document upload attribution for dual-filer support with taxpayer/spouse/joint tagging and alternative manual income entry form**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-04T21:57:44Z
- **Completed:** 2026-02-04T22:09:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Document model has attribution column to tag documents as taxpayer, spouse, or joint
- Manual entry endpoint creates ExtractedData records without requiring document upload
- Attribution selector appears automatically when client has linked spouse
- Both document upload and manual entry trigger analysis after save
- Tab-based UI lets users choose between document upload or manual income entry

## Task Commits

Each task was committed atomically:

1. **Task 1: Add attribution column to Document model** - `14f3b1f` (feat)
2. **Task 2: Add attribution handling and manual entry endpoint** - `5936311` (feat)
3. **Task 3: Add attribution selector and manual entry UI** - `e817e20` (feat)

## Files Created/Modified
- `models/document.py` - Added attribution column with default 'taxpayer'
- `models/extracted_data.py` - Made document_id nullable, added tax_year column
- `routes/documents.py` - Attribution validation in upload, new /manual-entry endpoint
- `templates/upload.html` - Attribution selector, tab interface, manual entry form
- `static/js/upload.js` - checkClientHasSpouse(), tab switching, saveManualEntry()

## Decisions Made
- **ExtractedData.document_id nullable:** Required for manual entries that have no associated document. Database migration handled via SQLite table recreation.
- **Attribution stored on Document:** The document itself carries the attribution tag, while extracted data routes to the target client based on attribution value at processing time.
- **Client-side spouse check:** Cache spouse_id in select option data attribute for instant attribution visibility toggle without API call.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SQLite schema modification for nullable document_id**
- **Found during:** Task 2 (manual entry endpoint testing)
- **Issue:** ExtractedData.document_id had NOT NULL constraint in database, preventing manual entries
- **Fix:** Recreated extracted_data table with nullable document_id and added tax_year column
- **Files modified:** database.db (schema), models/extracted_data.py
- **Verification:** Manual entry POST returns 201 with records_created
- **Committed in:** 14f3b1f (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Schema modification was necessary for manual entry feature to work. No scope creep.

## Issues Encountered
None - all tasks executed as planned after schema fix.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Document attribution ready for use in OCR processing pipeline
- Manual entry data flows into existing analysis engine
- Ready for Phase 4 Plan 03 (strategy comparison cards)

---
*Phase: 04-strategies-workflow*
*Completed: 2026-02-04*
