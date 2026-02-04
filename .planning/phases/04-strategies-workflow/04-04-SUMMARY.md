---
phase: 04-strategies-workflow
plan: 04
subsystem: joint-strategies
tags: [mfj, mfs, spousal-ira, eitc, education-credits, bracket-utilization]
dependency-graph:
  requires: ["04-03"]
  provides: ["REQ-22", "REQ-23"]
  affects: []
tech-stack:
  added: []
  patterns: ["strategy-service-pattern", "feasibility-warnings"]
key-files:
  created:
    - services/joint_strategy_service.py
  modified:
    - services/joint_analysis_service.py
    - static/js/joint_analysis.js
    - static/css/style.css
decisions:
  - "Joint strategies generated dynamically based on spouse income data"
  - "Strategies show 'MFJ Only' badge and feasibility warnings for MFS"
metrics:
  duration: "~4 minutes"
  completed: "2026-02-04"
---

# Phase 4 Plan 04: Joint Optimization Strategies Summary

**One-liner:** MFJ-only strategies (Spousal IRA, Bracket Utilization, EITC, Education Credits) with feasibility warnings when MFS is recommended.

## What Was Built

### JointStrategyService (REQ-22)

New service for generating joint-only optimization strategies:

```python
# services/joint_strategy_service.py
class JointStrategyService:
    JOINT_STRATEGIES = [
        {'id': 'spousal_ira', 'name': 'Spousal IRA Contribution', ...},
        {'id': 'bracket_utilization', 'name': 'MFJ Bracket Utilization', ...},
        {'id': 'eitc_eligibility', 'name': 'Earned Income Tax Credit (EITC)', ...},
        {'id': 'education_credits', 'name': 'Education Credits (AOTC/LLC)', ...}
    ]

    @staticmethod
    def generate_joint_strategies(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        # Returns list of applicable joint strategies
```

**Strategy Detection Logic:**

1. **Spousal IRA**: Detected when one spouse has income < $7,500 and other has >= $7,500
   - Calculates tax benefit based on MFJ marginal rate (24%)
   - Example: $7,500 contribution x 24% = $1,800 potential savings

2. **Bracket Utilization**: Calculates MFS combined tax vs MFJ tax
   - Savings = MFS_combined - MFJ_total
   - Shows effective rate comparison

3. **EITC/Education Credits**: Eligibility checks based on income limits
   - Both are completely unavailable for MFS filers

### API Integration

JointAnalysisService now returns `joint_strategies` array:

```python
# In analyze_joint() and _format_cached_result()
return {
    'spouse1': {...},
    'spouse2': {...},
    'mfj': {...},
    'mfs_spouse1': {...},
    'mfs_spouse2': {...},
    'comparison': {...},
    'joint_strategies': [...]  # NEW
}
```

### UI Components (REQ-23)

**JavaScript (joint_analysis.js):**

- `renderJointStrategies(strategies, recommendedStatus)` - Renders strategy cards
- `STRATEGY_FILING_REQUIREMENTS` - Maps strategy IDs to filing requirements
- `getStrategyFeasibilityWarning(strategyId, context)` - Returns warning if MFS context

**CSS (style.css):**

- `.joint-strategies-section` - Container with top border separator
- `.joint-strategies-grid` - Responsive grid layout (auto-fit, minmax 280px)
- `.joint-strategy-card` - Individual strategy cards with status colors
- `.mfj-only-badge` - Blue badge indicating MFJ requirement
- `.feasibility-warning` - Orange warning box with icon

### Feasibility Warnings

When MFS is recommended, joint strategies show warnings:

```html
<div class="feasibility-warning">
    <span class="warning-icon">!</span>
    Not available with MFS: Spousal IRA Contribution
</div>
```

## Commits

| Commit | Description | Files |
|--------|-------------|-------|
| 82d1a5e | JointStrategyService for MFJ-only strategies | services/joint_strategy_service.py |
| 235459d | Integrate joint strategies into JointAnalysisService | services/joint_analysis_service.py |
| 2d6f6a4 | UI for joint strategies with feasibility warnings | static/css/style.css |

Note: JavaScript changes were interleaved with 04-03 commits in the same session.

## Verification Results

| Test | Result |
|------|--------|
| JointStrategyService generates 4 strategies | PASS |
| Spousal IRA detected for low-income spouse | PASS - $1,800 benefit |
| Bracket utilization calculates savings | PASS - $5,000 savings |
| MFS feasibility warnings present | PASS |
| API returns joint_strategies | PASS |
| UI renderJointStrategies function | PASS |
| CSS styling for joint strategies | PASS |

## Requirements Satisfied

- **REQ-22:** Joint optimization strategies (Spousal IRA, Bracket Utilization, EITC, Education Credits) displayed when MFJ is recommended
- **REQ-23:** Strategy feasibility flags showing warnings when strategy requires MFJ but MFS is being viewed

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

- `JointStrategyService.generate_joint_strategies()` called from `JointAnalysisService.analyze_joint()`
- Strategy data passed through API to `displayComparison()` in JavaScript
- UI renders between comparison notes and detailed table

## Next Phase Readiness

Phase 4 Plan 04 is the final plan. All 26 requirements for the Dual-Filer MFJ/MFS Support milestone are now complete.
