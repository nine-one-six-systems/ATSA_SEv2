---
phase: 04
plan: 03
subsystem: strategies
tags: [income-detection, personalization, strategies, REQ-21]
requires:
  - 04-02 (document attribution)
provides:
  - income type detection from extracted data
  - per-spouse strategy prioritization
  - UI rendering of personalized strategies
affects:
  - 04-04 (summary report generation)
tech-stack:
  added: []
  patterns:
    - strategy prioritization by income relevance
    - form-type to income-type mapping
key-files:
  created: []
  modified:
    - services/tax_strategies.py
    - services/joint_analysis_service.py
    - static/js/joint_analysis.js
    - static/css/style.css
decisions:
  - "Form types map to income types: W-2 -> w2_employee, Schedule C -> self_employed, etc."
  - "Strategies prioritized by income relevance (relevant first, then by priority)"
  - "Income types displayed as human-readable labels in UI"
metrics:
  tasks: 3
  duration: 188s
  completed: 2026-02-04
---

# Phase 4 Plan 3: Per-Spouse Strategy Enhancement Summary

**One-liner:** Income type detection from extracted data forms enables personalized strategy recommendations for each spouse based on their W-2/LLC/business profile.

## What Was Built

### Task 1: Income Type Detection (TaxStrategiesService)

Added three new static methods to TaxStrategiesService:

1. **`detect_income_types(client_id)`** - Queries ExtractedData for distinct form types and maps to income categories:
   - W-2 -> `w2_employee`
   - Schedule C -> `self_employed`
   - Schedule E -> `rental_income`
   - K-1 -> `business_owner`
   - Schedule D/Form 8949 -> `capital_gains`
   - 1099-INT/1099-DIV -> `investment_income`

2. **`filter_strategies_by_income_type(strategies, income_types)`** - Prioritizes strategies relevant to detected income types by moving them to front of list while preserving priority ordering within groups.

3. **`get_personalized_strategies(data_by_form, client)`** - Convenience method combining analysis with income filtering, returns tuple of (strategies, income_types).

Added constant **`INCOME_TYPE_STRATEGIES`** mapping each income type to relevant strategy IDs:
- `w2_employee`: retirement_contributions
- `self_employed`: retirement_contributions, qbi_deduction, se_tax_deduction, se_health_insurance, home_office
- `business_owner`: qbi_deduction, section_179, bonus_depreciation, rd_deduction, fmla_credit
- `rental_income`: section_179, bonus_depreciation
- `capital_gains`: qsbs_exclusion

### Task 2: Joint Analysis Integration

Modified `JointAnalysisService.analyze_joint()`:
- After analyzing each spouse, detect their income types
- Prioritize their strategies by income type relevance
- Include `income_types` array in spouse1/spouse2 response objects

Updated `_format_cached_result()`:
- Also includes income type detection and strategy filtering for cached responses

### Task 3: UI Rendering

Added to `joint_analysis.js`:
- **`renderSpouseStrategies(strategies, incomeTypes)`** - Renders strategy cards with status colors and relevance badges
- **`parseStrategyInfo(strategy)`** - Parses JSON strategy_description
- **`getStatusClass(status)`** - Maps status to CSS class (status-good, status-warning, etc.)
- **`formatStatus(status)`** - Human-readable status labels
- **`isStrategyRelevant(strategyId, incomeTypes)`** - Checks if strategy matches income type

Added to `style.css`:
- `.spouse-strategies` section styling
- `.income-type-badge` for displaying income type label
- `.strategy-item` cards with status colors
- `.relevance-badge` "Recommended" indicator for income-relevant strategies

## Commits

| Commit | Description |
|--------|-------------|
| `2d4479a` | feat(04-03): add income type detection to TaxStrategiesService |
| `34e0f9d` | feat(04-03): integrate income-type detection into joint analysis |
| `49075a2` | feat(04-03): display per-spouse strategies in joint analysis UI |

## Verification Results

All verification criteria passed:

1. **Income detection for W-2**: Client 1 (TestHusband) correctly detected as `['w2_employee']`
2. **Income detection for Schedule C**: Method properly returns `['self_employed']` when Schedule C data present
3. **Strategy prioritization**: Self-employed income types prioritize QBI and retirement strategies first
4. **API response**: Joint analysis includes `income_types` in both spouse1 and spouse2 objects

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

- Income type detection queries ExtractedData table for distinct form_type values
- Strategy prioritization uses stable sort (relevant strategies first, then by priority)
- INCOME_TYPE_STRATEGIES mapping mirrors Python constant in JavaScript for UI relevance checking
- All filtering happens server-side; UI only receives pre-sorted strategies

## REQ-21 Completion Status

**COMPLETE**: Per-spouse tax strategies with individual recommendations based on income type:
- LLC owner (Schedule C) sees SEP-IRA and QBI optimization prioritized
- W-2 employee sees 401(k)/retirement contributions prioritized
- Each spouse panel shows "Income: {type}" label and "Recommended" badges on relevant strategies
