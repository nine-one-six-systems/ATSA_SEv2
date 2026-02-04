# Stack Research

**Domain:** Dual-filer tax analysis with split-screen comparison views
**Researched:** 2026-02-04
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies (Keep Existing)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Flask | 3.0.0 | Web framework | Already in use, mature ecosystem, sufficient for adding dual-filer features without migration |
| SQLAlchemy | 2.0.35+ | ORM and database queries | Already in use, excellent support for complex joins (spouse data), relationship loading optimization |
| SQLite | (system) | Database | Already in use, sufficient for dual-record storage and comparison queries |
| Vanilla JavaScript | ES6+ | Frontend interactivity | Already in use, modern browser support for Proxy-based state management, no framework needed |

### NEW: Split-Screen UI

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Split.js | 1.6.5 | Resizable split panes | For husband/wife side-by-side view with draggable divider (2kb, vanilla JS, no dependencies) |
| CSS Grid | Native | Two-column layout base | For responsive split-screen structure (husband column, wife column) with mobile stacking |
| CSS Flexbox | Native | Internal component alignment | For aligning form fields, comparison tables within each pane |

**Rationale for Split.js:**
- Lightweight (2kb minified), no dependencies
- Works with existing vanilla JS architecture
- Supports horizontal/vertical splits, configurable gutters
- Installation: `<script src="https://unpkg.com/split.js/dist/split.min.js"></script>` or npm
- Source: [Split.js npm](https://www.npmjs.com/package/split.js/v/1.6.5), [jQuery Script review](https://www.jqueryscript.net/blog/best-splitter-view.html)

**CSS Grid + Flexbox pattern (2026 best practice):**
- Use Grid for macro layout (page structure: split husband/wife columns)
- Use Flexbox for micro layout (component alignment within each column)
- Modern browsers have universal support, production-ready
- Source: [Modern CSS Layout Techniques 2026](https://www.frontendtools.tech/blog/modern-css-layout-techniques-flexbox-grid-subgrid-2025), [CSS Grid vs Flexbox patterns](https://thelinuxcode.com/css-grid-vs-flexbox-in-2026-practical-differences-mental-models-and-real-layout-patterns/)

### NEW: Dual Data Entry and Validation

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None (use existing patterns) | - | Form validation | Extend existing vanilla JS validation for dual forms |
| Flask-Pydantic (optional) | 0.12.0+ | Request validation | If API payload complexity increases (nested spouse data), provides type-based validation |

**Rationale:**
- Current app uses vanilla JS form validation, works well
- Adding Flask-Pydantic is optional but useful for validating complex dual-filer payloads
- Pydantic validates using Python type annotations, integrates with Flask via `@validate()` decorator
- Alternative: Continue with manual validation in Flask routes (simpler, less overhead)
- Source: [Flask-Pydantic PyPI](https://pypi.org/project/Flask-Pydantic/), [Pydantic Flask integration guide](https://medium.com/@gabrielaugusto753/validating-requests-in-a-python-api-with-flask-and-pydantic-07dce5a07e9d)

### NEW: State Management for Dual Forms

| Pattern | Implementation | Purpose | Why |
|---------|----------------|---------|-----|
| Vanilla JS Proxy Pattern | Custom | Reactive state for husband/wife forms | Modern ES6+ Proxy enables reactive state without libraries (80% smaller than Redux) |
| Observer/Pub-Sub Pattern | Custom | Sync husband/wife data changes | Notify comparison view when either spouse's data updates |
| Local Storage Persistence | Native API | Save draft dual-filer entries | Prevent data loss on page refresh during data entry |

**Rationale for Vanilla JS State Management:**
- 2026 trend: Vanilla JS Proxies, WeakRefs, and ES2022+ features enable reactive state without frameworks
- Observer pattern promotes loose coupling between husband form, wife form, and comparison view
- No external dependencies, consistent with existing architecture
- Source: [State Management in Vanilla JS 2026 Trends](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de), [Modern State Management in Vanilla JS 2026](https://medium.com/@orami98/modern-state-management-in-vanilla-javascript-2026-patterns-and-beyond-ce00425f7ac5)

### NEW: Joint Tax Calculation Logic

| Component | Implementation | Purpose | Why |
|-----------|----------------|---------|-----|
| Joint calculator service | Python class | Calculate MFJ combined tax | Extend existing `TaxCalculator` class with joint methods |
| Comparison engine | Python function | Generate MFJ vs MFS comparison | New service to compute both scenarios and return diff |
| JSON serialization | Native `json` module | Serialize comparison results | Current approach works, complex nested objects handled manually |

**Alternative: dataclasses-json for serialization (optional):**
- If comparison response structure becomes deeply nested, consider `dataclasses-json`
- Handles recursive nested dataclasses, 40-50x faster than manual serialization
- Not needed initially, add if JSON serialization becomes bottleneck
- Source: [dataclasses-json PyPI](https://pypi.org/project/dataclasses-json/), [orjson fast serialization](https://github.com/ijl/orjson)

### Supporting Libraries (Existing)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pdfplumber | 0.10.3 | PDF parsing | Already in use for document upload |
| pytesseract | 0.3.13+ | OCR | Already in use for extracting tax form data |
| Pillow | 10.2.0+ | Image processing | Already in use for OCR preprocessing |
| python-dotenv | 1.0.0 | Environment variables | Already in use for config management |
| cryptography | 41.0.7 | SSN encryption | Already in use for spouse SSN encryption |

## Installation

### Python (Backend)
```bash
# No new Python packages required for MVP
# Existing requirements.txt already has everything needed

# Optional: If complex API validation is needed later
pip install flask-pydantic==0.12.0
```

### JavaScript (Frontend)
```bash
# Option 1: CDN (recommended for MVP)
# Add to HTML template:
# <script src="https://unpkg.com/split.js@1.6.5/dist/split.min.js"></script>

# Option 2: NPM (if transitioning to build system later)
npm install split.js@1.6.5
```

### CSS (Already native, no installation needed)
- CSS Grid: Native browser support (all modern browsers 2026)
- CSS Flexbox: Native browser support (all modern browsers 2026)

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Split.js | Native CSS Grid only | If resizable panes are not needed, pure CSS Grid is simpler (no JS dependency) |
| Vanilla JS Proxy state | Redux/Zustand | If app grows to 20+ forms with complex shared state, consider lightweight state library |
| Flask-Pydantic (optional) | WTForms | If rendering HTML forms server-side (current approach is API-driven, so Pydantic fits better) |
| Continue with SQLite | PostgreSQL | If concurrent dual-filer edits become bottleneck, upgrade to PostgreSQL (better locking) |
| Native JSON serialization | dataclasses-json | If deeply nested comparison objects cause performance issues or serialization bugs |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| jQuery | Outdated, unnecessary overhead (2026), Split.js is vanilla JS | Vanilla JavaScript with ES6+ features |
| React/Vue for split screen | Too heavy for this feature, adds build complexity to Flask app | Split.js + vanilla JS (2kb vs 100kb+) |
| Flask-WTF for API validation | Designed for server-rendered forms, not API-driven dual-filer data entry | Flask-Pydantic or manual validation |
| Heavy state management libraries (Redux, MobX) | Overkill for 2-3 forms, adds 50kb+ bundle size | Vanilla JS Proxy pattern (native, no dependencies) |
| Complex ORM query builders | SQLAlchemy 2.0+ handles spouse joins elegantly with `relationship()` | Use SQLAlchemy's built-in relationship loading |

## Stack Patterns by Feature

### Pattern 1: Split-Screen Layout
**Implementation:**
```html
<!-- CSS Grid for base structure -->
<div class="dual-filer-container">
  <div id="husband-pane" class="filer-pane"><!-- Husband form --></div>
  <div id="wife-pane" class="filer-pane"><!-- Wife form --></div>
</div>

<!-- Split.js for resizable divider -->
<script>
Split(['#husband-pane', '#wife-pane'], {
  sizes: [50, 50],
  minSize: 300,
  gutterSize: 10
});
</script>
```
**Why:** CSS Grid provides responsive base, Split.js adds resizability without complexity

### Pattern 2: Dual Data Entry State
**Implementation:**
```javascript
// Proxy-based reactive state
const dualFilerState = new Proxy({
  husband: { income: 0, filing_status: 'married_joint' },
  wife: { income: 0, filing_status: 'married_joint' },
  comparison: null
}, {
  set(target, key, value) {
    target[key] = value;
    // Notify observers (comparison view)
    notifyObservers(key, value);
    return true;
  }
});
```
**Why:** Modern ES6 Proxy enables reactive updates without library overhead

### Pattern 3: MFJ vs MFS Comparison API
**Endpoint:** `/api/calculator/compare-filing-status`
**Request:**
```json
{
  "husband": { "income": 250000, "income_source": "llc", ... },
  "wife": { "income": 100000, "income_source": "w2", ... },
  "tax_year": 2026
}
```
**Response:**
```json
{
  "married_filing_jointly": { "total_tax": 75000, ... },
  "married_filing_separately": {
    "husband_tax": 50000,
    "wife_tax": 18000,
    "total_tax": 68000
  },
  "savings_with_mfs": 7000,
  "recommendation": "married_filing_separately"
}
```
**Why:** Single endpoint returns both scenarios for side-by-side comparison

### Pattern 4: Spouse Data Query
**SQLAlchemy Query:**
```python
# Already supported by existing Client.spouse relationship
client = Client.query.filter_by(id=client_id).first()
spouse = client.spouse  # SQLAlchemy lazy loads spouse via relationship
```
**Why:** Existing schema already supports spouse_id foreign key, relationship is defined

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Flask 3.0.0 | SQLAlchemy 2.0.35+ | Requires SQLAlchemy 2.0+, not compatible with 1.x |
| Split.js 1.6.5 | All modern browsers | IE11 not supported, Chrome/Firefox/Safari/Edge all compatible |
| Flask-Pydantic 0.12.0+ | Flask 2.0+ | Requires Python 3.7+, Pydantic 1.8+ |
| CSS Grid/Flexbox | Native | Universal browser support 2026 (IE11 dead, Edge uses Chromium) |

## Database Schema Considerations

**Existing schema already supports dual-filer:**
- `Client.spouse_id` foreign key exists
- `Client.filing_status` supports 'married_joint' and 'married_separate'
- No schema changes needed for dual-filer feature

**Query optimization for dual loads:**
```python
# Use joinedload to avoid N+1 queries
from sqlalchemy.orm import joinedload
client = Client.query.options(joinedload(Client.spouse)).filter_by(id=client_id).first()
```
**Why:** Loads both client and spouse in single query, prevents N+1 problem
**Source:** [SQLAlchemy join optimization guide](https://copyprogramming.com/howto/join-multiple-tables-in-sqlalchemy-flask)

## Tax Calculation Considerations

**2026 Tax Rules:**
- Standard deduction (MFJ): $32,200
- Standard deduction (MFS): $16,100 each
- Tax brackets differ for MFJ vs MFS
- Child Tax Credit: $2,200 per child (can only be claimed by one spouse if MFS)
**Source:** [2026 Tax Brackets Tax Foundation](https://taxfoundation.org/data/all/federal/2026-tax-brackets/), [NerdWallet 2026 brackets](https://www.nerdwallet.com/taxes/learn/federal-income-tax-brackets)

**Implementation note:** Existing `TaxCalculator` already handles both MFJ and MFS filing statuses correctly.

## Sources

### Verified with Official Documentation (HIGH confidence):
- [Flask 3.0 documentation](https://flask.palletsprojects.com/) - Version compatibility, API patterns
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/) - Relationship queries, join patterns
- [MDN CSS Grid documentation](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout) - Grid layout patterns
- [2026 Tax Brackets Tax Foundation](https://taxfoundation.org/data/all/federal/2026-tax-brackets/) - MFJ vs MFS bracket differences

### Verified with Multiple Sources (MEDIUM confidence):
- [Split.js npm package](https://www.npmjs.com/package/split.js/v/1.6.5) - Version 1.6.5, installation methods
- [Modern CSS Layout 2026](https://www.frontendtools.tech/blog/modern-css-layout-techniques-flexbox-grid-subgrid-2025) - Grid vs Flexbox patterns
- [CSS Grid vs Flexbox 2026](https://thelinuxcode.com/css-grid-vs-flexbox-in-2026-practical-differences-mental-models-and-real-layout-patterns/) - Layout decision framework
- [State Management Vanilla JS 2026](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de) - Proxy pattern trends
- [Flask-Pydantic PyPI](https://pypi.org/project/Flask-Pydantic/) - Pydantic integration patterns

### Community Patterns (LOW confidence, verify during implementation):
- [Vanilla JS Proxy patterns](https://medium.com/@orami98/modern-state-management-in-vanilla-javascript-2026-patterns-and-beyond-ce00425f7ac5) - State management architecture
- [SQLAlchemy complex joins](https://copyprogramming.com/howto/join-multiple-tables-in-sqlalchemy-flask) - Query optimization patterns
- [Flask API best practices](https://auth0.com/blog/best-practices-for-flask-api-development/) - Response format conventions

---
*Stack research for: Dual-filer tax analysis with split-screen comparison*
*Researched: 2026-02-04*
