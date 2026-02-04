---
phase: 03-split-screen-ui
plan: 01
subsystem: frontend
tags: [html, css, flask, split-screen, responsive]

dependency-graph:
  requires:
    - Phase 1: Client model, TaxCalculator
    - Phase 2: JointAnalysisService API
  provides:
    - Split-screen HTML template with spouse panels
    - CSS styles for joint analysis page
    - Flask route /joint-analysis.html
    - Navbar link across all pages
  affects:
    - Plan 03-02: JavaScript will populate DOM elements created here

tech-stack:
  added:
    - Split.js 1.6.5 (CDN)
  patterns:
    - CSS Grid for page layout
    - Flexbox for split-screen container (Split.js requirement)
    - Responsive stacking at 768px

key-files:
  created:
    - templates/joint_analysis.html
    - static/js/joint_analysis.js
  modified:
    - static/css/style.css
    - app.py
    - templates/index.html
    - templates/clients.html
    - templates/upload.html
    - templates/analysis.html
    - templates/calculator.html

decisions:
  - decision: Use Split.js CDN instead of npm
    rationale: No build step required, 2kb library, matches existing vanilla JS architecture

metrics:
  duration: ~10 minutes
  completed: 2026-02-04
---

# Phase 3 Plan 01: Split-Screen Page Foundation Summary

Split-screen template with CSS styles and Flask route for dual-filer joint analysis page.

## What Was Built

### Task 1: HTML Template (commit f7a5e79)
Created `templates/joint_analysis.html` with:
- DOCTYPE, head with Split.js CDN script tag
- Navbar with "Joint Analysis" link (active state)
- Page header with spouse selector dropdowns
- Split-screen container with two spouse panels
- Comparison section below panels
- Link to joint_analysis.js at bottom

DOM IDs for JavaScript binding:
- `spouse1-select`, `spouse2-select` (client dropdowns)
- `load-analysis-btn` (trigger button)
- `spouse1-panel`, `spouse2-panel` (Split.js targets)
- `spouse1-name`, `spouse2-name` (name headers)
- `spouse1-content`, `spouse2-content` (content areas)
- `comparison-content` (comparison section)

Updated navbar in all 5 existing templates to include Joint Analysis link.

### Task 2: CSS Styles (commit 9712c3a)
Appended ~250 lines to `static/css/style.css`:
- `.joint-analysis-page` - Grid layout (header/panels/comparison)
- `.split-screen-container` - Flexbox for Split.js compatibility
- `.spouse-panel` - Individual panel styling
- `.gutter` - Split.js divider styling with hover effect (#3498db)
- `.income-breakdown` - Income items with border-left accent (REQ-19)
- `.comparison-section` - Cards layout below panels
- `.comparison-table` - Three-column table for MFJ/MFS comparison (REQ-20)
- Responsive rules at 768px - vertical stacking, gutter hidden

### Task 3: Flask Route (commit 39ad325)
Added to `app.py`:
```python
@app.route('/joint-analysis.html')
def joint_analysis():
    return render_template('joint_analysis.html')
```

Created `static/js/joint_analysis.js` placeholder with Split.js initialization.

## Verification Results

All success criteria passed:

| Check | Result |
|-------|--------|
| /joint-analysis.html returns 200 | PASS |
| Title "Joint Analysis - ATSA" | PASS |
| Split.js CDN in head | PASS |
| Navbar link active | PASS |
| split-container ID | PASS |
| spouse1-panel ID | PASS |
| spouse2-panel ID | PASS |
| comparison-content ID | PASS |
| spouse selectors | PASS |
| load-analysis-btn | PASS |
| Joint Analysis in all navbars | PASS |

## Deviations from Plan

**1. [Rule 3 - Blocking] Created placeholder joint_analysis.js**
- **Found during:** Task 3
- **Issue:** Template references `joint_analysis.js` but Plan 02 creates the full implementation
- **Fix:** Created minimal placeholder with Split.js initialization to prevent 404
- **Files created:** `static/js/joint_analysis.js`
- **Commit:** 39ad325

## Commits

| Hash | Type | Description |
|------|------|-------------|
| f7a5e79 | feat | Create joint_analysis.html template with split-screen structure |
| 9712c3a | feat | Add split-screen CSS styles for joint analysis page |
| 39ad325 | feat | Register /joint-analysis.html route and add placeholder JS |

## Next Phase Readiness

**Ready for Plan 03-02:** All DOM elements and CSS styles are in place. JavaScript can:
1. Populate spouse dropdowns from /api/clients
2. Load joint analysis data from /api/joint-analysis/{id1}/{id2}
3. Render income breakdown in spouse panels
4. Render MFJ vs MFS comparison in comparison section
5. Split.js already initialized in placeholder

**No blockers identified.**
