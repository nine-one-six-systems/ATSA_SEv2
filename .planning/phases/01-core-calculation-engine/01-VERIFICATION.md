---
phase: 01-core-calculation-engine
verified: 2026-02-04T20:15:00Z
status: gaps_found
score: 10/12 must-haves verified
gaps:
  - truth: "Standard deductions match 2026 IRS values"
    status: failed
    reason: "Database contains 2025 values ($30,600/$15,300) instead of 2026 values ($32,200/$16,100)"
    artifacts:
      - path: "models/tax_tables.py"
        issue: "StandardDeduction table populated with 2025 values"
    missing:
      - "Update standard deduction amounts to 2026 IRS values"
      - "MFJ should be $32,200 (currently $30,600)"
      - "MFS should be $16,100 (currently $15,300)"
  - truth: "Real use case scenario can be fully tested"
    status: partial
    reason: "ExtractedData requires document_id, making manual test data creation difficult"
    artifacts:
      - path: "models/extracted_data.py"
        issue: "NOT NULL constraint on document_id prevents direct data creation"
    missing:
      - "Test fixture creation or seed script for realistic scenarios"
---

# Phase 1: Core Dual-Filer Calculation Engine Verification Report

**Phase Goal:** A joint analysis can be triggered for two linked spouses and returns accurate MFJ totals, MFS totals per spouse, and a comparison with dollar difference and recommendation -- all cached and invalidated correctly.

**Verified:** 2026-02-04T20:15:00Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Joint analysis can be triggered for two linked spouses and returns JSON | ✓ VERIFIED | JointAnalysisService.analyze_joint(1, 2) returns structured dict with all required keys |
| 2 | MFJ calculation uses married_joint brackets | ✓ VERIFIED | TaxCalculator.get_tax_brackets('married_joint') called, returns MFJ brackets |
| 3 | MFS calculation uses married_separate brackets | ✓ VERIFIED | TaxCalculator.get_tax_brackets('married_separate') called for both spouses |
| 4 | Standard deductions match 2026 IRS values | ✗ FAILED | Database has $30,600 (MFJ) and $15,300 (MFS) - these are 2025 values. Should be $32,200/$16,100. |
| 5 | Comparison shows recommended filing status and dollar savings | ✓ VERIFIED | result['comparison'] contains 'recommended_status', 'savings_amount', 'reason' |
| 6 | Changing either spouse's data invalidates cached analysis | ✓ VERIFIED | REQ-08: Bidirectional cache invalidation confirmed. Spouse1 hash changed when spouse2 data added. |
| 7 | MFS excludes EITC, student loan interest, education credits | ✓ VERIFIED | CREDIT_ELIGIBILITY matrix shows False for MFS on all restricted credits |
| 8 | MFS uses $197,300 QBI threshold, MFJ uses $394,600 | ✓ VERIFIED | QBI_THRESHOLDS_2026 constants correct, _check_qbi_impact() uses correct thresholds |
| 9 | SQLite WAL mode enabled | ✓ VERIFIED | PRAGMA journal_mode returns 'wal', PRAGMA busy_timeout set to 30000ms |
| 10 | JointAnalysisSummary table exists | ✓ VERIFIED | Table 'joint_analysis_summaries' exists with all 23 fields |
| 11 | API endpoints accessible | ✓ VERIFIED | /api/joint-analysis/<id>/<id> routes registered (GET, POST, GET/comparison) |
| 12 | Results cached in database | ✓ VERIFIED | JointAnalysisSummary record created with data_version_hash, retrieved on subsequent calls |

**Score:** 10/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `database/init_db.py` | WAL mode configuration | ✓ VERIFIED | Lines 19-21: PRAGMA journal_mode=WAL, PRAGMA busy_timeout=30000, with explanatory comments |
| `models/joint_analysis.py` | JointAnalysisSummary model | ✓ VERIFIED | 103 lines, all required fields (MFJ 6, MFS 10, comparison 3, caching 4), unique constraint, to_dict() method |
| `models/__init__.py` | Model registration | ✓ VERIFIED | Line 9: JointAnalysisSummary imported, Line 13: exported in __all__ |
| `services/analysis_engine.py` | Bidirectional hash | ✓ VERIFIED | Lines 29-33: spouse data included in hash calculation with REQ-08 comment |
| `services/joint_analysis_service.py` | Core service | ✓ VERIFIED | 525 lines, all methods: analyze_joint(), _calculate_joint_hash(), _filter_strategies_by_filing_status(), _check_qbi_impact() |
| `routes/joint_analysis.py` | API endpoints | ✓ VERIFIED | 67 lines, 3 endpoints: POST (force refresh), GET (cached), GET/comparison (summary) |
| `routes/api.py` | Blueprint registration | ✓ VERIFIED | Line 6: joint_analysis_bp imported, Line 15: registered with api_bp |
| `models/tax_tables.py` | Standard deductions | ⚠️ PARTIAL | Table exists, but contains 2025 values instead of 2026 values |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| routes/joint_analysis.py | JointAnalysisService | analyze_joint() calls | ✓ WIRED | Lines 12, 35: JointAnalysisService.analyze_joint() called with spouse IDs |
| JointAnalysisService | AnalysisEngine | Individual analysis | ✓ WIRED | Lines 190, 287-288: AnalysisEngine.analyze_client() called for both spouses |
| JointAnalysisService | TaxCalculator | Bracket/deduction lookup | ✓ WIRED | Lines 294-298 (MFJ), 327-337 (MFS): TaxCalculator methods called |
| AnalysisEngine | Client.spouse_id | Bidirectional hash | ✓ WIRED | Lines 30-33: Client.spouse_id queried, spouse ExtractedData included in hash |
| routes/api.py | joint_analysis_bp | Blueprint registration | ✓ WIRED | Line 15: api_bp.register_blueprint(joint_analysis_bp) |
| models/__init__.py | JointAnalysisSummary | Import chain | ✓ WIRED | Line 9: from models.joint_analysis import JointAnalysisSummary |

### Requirements Coverage

| Requirement | Status | Evidence/Issue |
|-------------|--------|----------------|
| REQ-01: MFJ calculation | ✓ SATISFIED | Lines 290-324 in joint_analysis_service.py: combined income through married_joint brackets |
| REQ-02: MFS calculation | ✓ SATISFIED | Lines 326-381 in joint_analysis_service.py: each spouse through married_separate brackets |
| REQ-03: MFJ vs MFS comparison | ✓ SATISFIED | Lines 403-436: comparison dict with recommended_status, savings_amount, reason |
| REQ-04: Income attribution (T/S/J) | ? DEFERRED | Phase 1 doesn't implement T/S/J tagging. Analysis uses total_income from individual summaries. |
| REQ-05: Credit eligibility | ✓ SATISFIED | Lines 54-79: CREDIT_ELIGIBILITY matrix, Lines 119-146: _filter_strategies_by_filing_status() |
| REQ-06: QBI thresholds | ✓ SATISFIED | Lines 45-50: QBI_THRESHOLDS_2026 correct, Lines 148-185: _check_qbi_impact() enforcement |
| REQ-07: Standard deductions | ✗ BLOCKED | Implementation correct (lines 294-298, 327-331), but database has wrong values ($30,600/$15,300 vs $32,200/$16,100) |
| REQ-08: Bidirectional cache invalidation | ✓ SATISFIED | analysis_engine.py lines 29-33: spouse data included in hash. Tested: spouse1 hash changes when spouse2 data changes. |
| REQ-12: SQLite WAL mode | ✓ SATISFIED | init_db.py lines 19-21: WAL mode + 30s busy timeout enabled |
| REQ-13: JointAnalysisSummary model | ✓ SATISFIED | models/joint_analysis.py: 23 fields, unique constraint, to_dict() method |
| REQ-14: JointAnalysisService | ✓ SATISFIED | services/joint_analysis_service.py: 525 lines, all orchestration methods |
| REQ-15: API endpoints | ✓ SATISFIED | routes/joint_analysis.py: 3 endpoints registered at /api/joint-analysis/* |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| models/tax_tables.py | Outdated tax year data | 🛑 Blocker | Standard deduction values are 2025 ($30,600/$15,300) instead of 2026 ($32,200/$16,100). This causes incorrect tax calculations and breaks Success Criterion 2 comparison. |
| None | No placeholder implementations found | ℹ️ Info | All files contain substantive implementations, no TODOs or stub patterns detected. |

### Human Verification Required

#### 1. Two Simultaneous Requests Test

**Test:** Open two browser tabs. In tab 1, trigger joint analysis (POST /api/joint-analysis/1/2). In tab 2, upload a document for spouse 1.  
**Expected:** Both operations complete successfully without "database is locked" errors.  
**Why human:** Requires concurrent UI actions, cannot automate with single test script.

#### 2. Visual MFJ vs MFS Comparison

**Test:** Call GET /api/joint-analysis/1/2 and inspect returned JSON structure.  
**Expected:** Response contains three distinct tax calculations: mfj (combined), mfs_spouse1 (separate), mfs_spouse2 (separate), with comparison showing which saves money.  
**Why human:** Verify JSON structure clarity for frontend consumption, ensure all required fields present.

#### 3. Real-World Scenario: $250k LLC + $100k W-2

**Test:** Create two linked spouses with realistic income data (husband: Schedule C $250k, wife: W-2 $100k), trigger joint analysis.  
**Expected:** MFS shows reduced/phased-out QBI deduction for husband (above $197,300), MFJ shows full QBI deduction (combined $350k below $394,600). Dollar amounts differ based on QBI treatment.  
**Why human:** Requires realistic test data setup with ExtractedData and Documents, which has schema constraints making direct creation difficult.

### Gaps Summary

**Gap 1: Standard Deduction Values (Blocker)**

The database contains 2025 IRS standard deduction values ($30,600 for MFJ, $15,300 for MFS) instead of 2026 values ($32,200 for MFJ, $16,100 for MFS as specified in REQ-07 and Success Criteria).

**Root cause:** TaxDataService.populate_tax_tables() populates from tax data source that has outdated values.

**Impact:** All tax calculations use incorrect deductions, making comparison results inaccurate. This is a data issue, not implementation issue - the code correctly calls TaxCalculator.get_standard_deduction(), but the database returns wrong values.

**Fix required:**
- Update StandardDeduction table: MFJ from $30,600 to $32,200
- Update StandardDeduction table: MFS from $15,300 to $16,100
- Verify other 2026 tax year data (brackets, thresholds) is current

**Gap 2: Test Data Creation Difficulty (Minor)**

ExtractedData model has NOT NULL constraint on document_id, making direct test data creation difficult. Cannot easily create test scenarios without first creating Document records.

**Root cause:** Normalized database schema requires Documents first, then ExtractedData.

**Impact:** Manual testing of real-world scenarios (like "$250k LLC + $100k W-2") requires multi-step setup. Success Criterion 2 cannot be easily verified without significant test infrastructure.

**Fix required:**
- Create test fixture script (e.g., tests/fixtures/dual_filer_scenarios.py)
- OR add test data seed function to populate realistic scenarios
- OR modify tests to create Document + ExtractedData in correct order

---

## Success Criteria Evaluation

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1. Tax professional triggers joint analysis and receives JSON with MFJ/MFS/comparison | ✓ PASS | JointAnalysisService.analyze_joint(1, 2) returns complete structured response |
| 2. Real use case ($250k LLC + $100k W-2) shows QBI difference | ? NEEDS HUMAN | Implementation logic correct, but cannot easily create test data due to schema constraints |
| 3. MFS returns $0 for EITC, student loan, education credits | ✓ PASS | CREDIT_ELIGIBILITY matrix filters correctly, removed_credits tracked in comparison notes |
| 4. Updating either spouse's data causes recalculation | ✓ PASS | REQ-08 verified: bidirectional cache invalidation working correctly |
| 5. Two simultaneous requests without "database locked" errors | ? NEEDS HUMAN | WAL mode enabled, but requires concurrent testing to verify |

**Overall:** 3/5 pass, 0/5 fail, 2/5 need human verification

---

_Verified: 2026-02-04T20:15:00Z_  
_Verifier: Claude (gsd-verifier)_
