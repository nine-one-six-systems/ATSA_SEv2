# Feature Landscape: Dual-Filer Tax Analysis (MFJ vs MFS)

**Domain:** Tax professional software for married couples (dual-filer analysis)
**Researched:** 2026-02-04
**Confidence:** HIGH (based on professional tax software documentation, IRS guidelines, and tax professional workflows)

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Side-by-side income entry** | Tax pros need to see both spouses' individual tax pictures simultaneously | Medium | Split-screen: husband left, wife right. Each spouse has their own income sources, deductions. Industry standard in Drake Tax, TaxSlayer Pro. |
| **MFJ vs MFS comparison report** | Core value proposition — showing which filing status saves money is the #1 reason to use dual-filer tools | Medium | Must show: (1) Joint return outcome, (2) Each separate return outcome, (3) Net difference in dollars. Format: columns showing refund/amount due for each scenario. |
| **Automatic tax calculation for both statuses** | Manual calculation defeats the purpose of software | High | Calculate brackets, deductions, credits for: (1) MFJ combined, (2) MFS spouse 1, (3) MFS spouse 2. Three parallel calculations from one data entry. |
| **Income source attribution (T/S/J)** | When filing separately, software must know which spouse earned which income | Medium | T = Taxpayer, S = Spouse, J = Joint (split 50/50). Required for accurate MFS calculation. Without this, MFS returns are wrong. |
| **Deduction method enforcement** | IRS rule: if one spouse itemizes on MFS, the other MUST itemize too | Low | Critical compliance feature. If spouse A itemizes, spouse B cannot take standard deduction. Software must validate and warn. |
| **Standard deduction amounts** | 2026: MFJ $32,200 / MFS $16,100 per spouse | Low | Core tax calculation. Already exists in single-filer tool, just needs MFS amounts added. |
| **Tax bracket application** | MFJ brackets are wider than MFS (which mirror single filer brackets) | Medium | MFS brackets are roughly half of MFJ. This is why MFJ usually saves money. Must calculate both accurately. |
| **Shared expense allocation** | Mortgage interest, property taxes paid from joint accounts must be split for MFS | Medium | UI must allow: "Who paid this expense?" T/S/Both. If Both, split 50/50 or custom percentage. Critical for MFS accuracy. |
| **Credit availability by status** | Many credits unavailable on MFS (Child Tax Credit reduced, EITC unavailable, education credits unavailable) | High | Tax pros need to see which credits are lost when filing separately. Major factor in MFJ vs MFS decision. |
| **Document upload for each spouse** | Both spouses bring W-2s, 1099s, K-1s — software must handle documents for each | Low | Extend existing OCR to tag documents to Taxpayer vs Spouse. Already have upload, just add attribution. |
| **Spouse linking workflow** | Create both client records, link them, then analyze together | Low | Already exists via `spouse_id` field. Just needs UI to trigger joint analysis after linking. |

## Differentiators

Features that set product apart. Not expected, but highly valued by tax professionals.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Per-spouse tax strategies** | Show individual recommendations for each spouse based on their income type | Medium | Example: Husband (LLC) → SEP-IRA, QBI deduction. Wife (W-2) → 401k max, HSA. Personalized to income source. |
| **Joint optimization strategies** | Strategies that only work when filing jointly (e.g., spousal IRA, income averaging across brackets) | High | Example: "Filing jointly allows your combined income to utilize the wider 22% bracket instead of pushing spouse 2 into 24%." Show bracket utilization. |
| **Visual bracket utilization** | Show how much income falls into each bracket for MFJ vs MFS (chart/graph) | Medium | Tax pros can see "marriage bonus" visually. Differentiator because most tools only show bottom-line number, not the why. |
| **Income source breakdown by spouse** | Tooltip/modal showing: Husband: $250k LLC + $0 W-2. Wife: $0 LLC + $100k W-2 | Low | Contextual understanding. Tax pro can see "this is a mixed-income couple" at a glance. Builds on existing income summary. |
| **What-if scenario modeling** | Change income amounts and see MFJ vs MFS update in real-time | High | "What if wife earns $120k instead of $100k?" Instant recalc. Very valuable for planning, but complex to build. |
| **Deduction allocation optimizer** | For MFS: suggest optimal split of shared expenses to minimize combined tax | High | Advanced feature. If splitting mortgage interest 60/40 instead of 50/50 saves money (due to bracket differences), suggest it. Rare in consumer tools. |
| **Community property state handling** | CA, TX, WA, etc. require special income splitting rules even for MFS | High | Form 8958 generation. Required for accuracy in community property states, but adds significant complexity. |
| **Prior year comparison** | "Last year MFJ saved $5,400. This year MFS saves $1,200." | Medium | Shows year-over-year trend. Useful when circumstances change (one spouse starts business, income shifts). |
| **Strategy feasibility flags** | "SEP-IRA only available if filing jointly" or "Student loan interest deduction lost if filing separately" | Medium | Proactive warnings. Prevents tax pro from recommending incompatible strategies. Cross-references strategy engine with filing status. |
| **Automatic SALT cap calculation** | 2026 MFS SALT cap is $10k per spouse (not $20k combined) | Low | Itemization analysis. Show: "MFS allows $20k combined SALT vs $10k on MFJ." Rare edge case where MFS wins. |

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **"Auto-select best filing status" button** | Removes tax professional judgment from decision. Filing status choice involves liability protection, future implications, not just lowest tax. | Show comparison, let tax pro decide. Provide recommendation with rationale, but never auto-select. |
| **Simplified "Quick MFS" that skips income attribution** | Creates inaccurate returns. If income isn't properly attributed (T/S/J), MFS calculation is wrong. | Always require income source attribution for MFS. No shortcuts. |
| **Combining MFJ and MFS strategies in one list** | Confusing. Some strategies only work for MFJ, some only for MFS. Mixing them creates impossible recommendations. | Separate strategy sections: "If filing jointly" and "If filing separately." Clear context. |
| **Allowing one spouse to itemize, other to take standard deduction on MFS** | IRS rule violation. Both must use same method on MFS. Software that allows this creates compliance risk. | Enforce deduction method matching. Show error if violated. |
| **Allocating 100% of joint income to one spouse** | Income attribution must be reasonable. IRS scrutinizes artificial income shifting to lower-earning spouse. | Require realistic allocation. Community property states: enforce 50/50 split. Non-community: allow flexibility but warn if unrealistic. |
| **Real-time collaboration / multi-user editing** | Tax prep is single-operator. Adding real-time collaboration adds complexity without value for this use case. | Single-session editing. If needed, export/import data between sessions. |
| **Mobile-first interface** | Tax professionals work at desks with large monitors. Optimizing for mobile sacrifices information density. | Desktop-first. Side-by-side view requires screen real estate. |
| **Automated strategy execution** | Strategies require client action (open IRA, adjust withholding, etc.). Software cannot execute. Pretending otherwise creates confusion. | Show recommendations with action items. Make clear these are suggestions, not automated actions. |
| **Historical filing status editing** | Changing prior year filing status in software doesn't change IRS records. Creates false historical data. | Lock historical data. To model "what if we filed differently," use separate scenario tool, not actual data edit. |

## Feature Dependencies

```
Spouse Linking
    ↓
Income Source Attribution (T/S/J)
    ↓
Dual Tax Calculation (MFJ + MFS for both spouses)
    ↓
MFJ vs MFS Comparison Report
    ↓
Filing Status-Specific Strategies
```

**Critical Path:**
1. Must have spouse linking before dual entry makes sense
2. Must have income attribution before MFS calculation is accurate
3. Must have both calculations before comparison is possible
4. Must have comparison before strategies can be filing-status-aware

**Parallel Development Opportunities:**
- Document upload attribution (independent of calculation)
- Per-spouse strategy recommendations (can build alongside comparison)
- Visual bracket utilization (enhancement, can add after core comparison works)

## MVP Recommendation

For MVP, prioritize:

1. **Side-by-side income entry with T/S/J attribution** — Core data model
2. **Automatic MFJ + MFS calculation** — Core engine extension
3. **MFJ vs MFS comparison report** — Core deliverable (the "aha" moment)
4. **Deduction method enforcement** — Compliance requirement
5. **Credit availability by status** — Critical for accurate comparison
6. **Per-spouse tax strategies** — Differentiator (low complexity, high value)

Defer to post-MVP:

- **What-if scenario modeling** — High complexity, nice-to-have. Core comparison already provides value without this.
- **Community property state handling** — Adds significant complexity, only affects subset of users. Can validate manually in MVP.
- **Deduction allocation optimizer** — Advanced feature. Tax pros can manually optimize in MVP.
- **Prior year comparison** — Requires historical data structure. V2 feature.
- **Visual bracket utilization** — Enhancement. Text-based comparison is sufficient for MVP.

## Complexity Notes

**High Complexity Features:**
- **Dual tax calculation engine** — Must calculate 3 returns (1 joint + 2 separate) from single data entry. Bracket logic, credit logic, deduction logic all differ by status.
- **Credit availability** — Different rules for each credit (some reduced on MFS, some eliminated). Requires detailed IRS rule modeling.
- **What-if scenarios** — Recalculation performance, state management, UI for editing hypotheticals.
- **Community property states** — Entire separate ruleset for income splitting. Form 8958 generation.

**Medium Complexity Features:**
- **Side-by-side entry UI** — Split-screen layout, data binding for each spouse, synchronized state.
- **Income source attribution** — Data model change (add T/S/J field to income sources), UI dropdowns, validation.
- **Shared expense allocation** — UI for "who paid this," percentage splits, validation that totals make sense.
- **Per-spouse strategies** — Extend existing strategy engine to filter recommendations by income type and filing status.

**Low Complexity Features:**
- **Deduction method enforcement** — Simple validation rule: if spouse1.itemizes and spouse2.standardDeduction, show error.
- **Standard deduction amounts** — Just add MFS amounts to existing bracket/deduction table.
- **Document upload attribution** — Add "spouse" dropdown to existing upload UI.
- **Income source breakdown tooltip** — Display existing data in tooltip format.

## Real-World Usage Patterns

Based on tax professional workflows:

**Common Scenario 1: Mixed Income (LLC + W-2)**
- Husband: $250k LLC (Schedule C or K-1)
- Wife: $100k W-2
- **Tax pro needs:** See if QBI deduction is better on MFJ (combined income might phase out) or if splitting income keeps both in QBI range
- **Feature requirement:** Per-spouse strategies showing QBI availability + bracket utilization

**Common Scenario 2: High Medical Expenses**
- One spouse has $30k medical expenses
- On MFS, that spouse might exceed 7.5% AGI threshold for deduction
- On MFJ, combined income makes threshold harder to reach
- **Tax pro needs:** Itemization analysis showing medical deduction for each status
- **Feature requirement:** Deduction allocation + itemization comparison

**Common Scenario 3: Student Loan Repayment**
- Filing separately affects income-driven repayment plans
- Lower AGI on MFS might reduce monthly payments
- But lose education credits on MFS
- **Tax pro needs:** See tax impact separate from student loan payment impact
- **Feature requirement:** Show MFJ vs MFS comparison + note that education credits are unavailable on MFS

**Common Scenario 4: Liability Protection**
- One spouse has tax debt or potential audit risk
- Filing separately shields other spouse from joint liability
- Tax cost might be worth the protection
- **Tax pro needs:** Quantify the tax cost of filing separately
- **Feature requirement:** Clear dollar difference: "MFS costs $3,200 more than MFJ, but limits liability exposure"

## Industry Standards (What Competitors Do)

| Software | MFJ vs MFS Comparison | Income Attribution | Split Returns | Visual Reporting |
|----------|----------------------|-------------------|---------------|------------------|
| **Drake Tax** | ✅ Filing Status Optimization Report (Wks MFS Comp) | ✅ T/S/J fields on all income screens | ✅ Can split joint return into 2 MFS returns | ❌ Text-based report |
| **TaxSlayer Pro** | ✅ MFJ vs MFS module | ✅ Required before MFS calculation | ✅ Separate returns from joint data entry | ❌ Text-based report |
| **TurboTax (consumer)** | ✅ Comparison table (columns) | ⚠️ Limited (mostly joint) | ❌ No split function | ⚠️ Basic table |
| **Lacerte (Intuit Pro)** | ✅ Comprehensive diagnostics | ✅ Full attribution | ✅ Split returns | ✅ Detailed reports |
| **ProSeries (Intuit)** | ✅ MFJ vs MFS comparison | ✅ Income attribution | ✅ Split returns | ⚠️ Basic reporting |

**Key Takeaway:** Professional tax software (Drake, TaxSlayer Pro, Lacerte) ALL have:
1. T/S/J income attribution
2. MFJ vs MFS comparison report
3. Ability to split joint return into two separate returns
4. These are table stakes for professional tools.

**Differentiator Opportunity:** Most tools provide text-based reports (columns of numbers). Adding visual bracket utilization or interactive what-if scenarios would differentiate from competition.

## Sources

**Professional Tax Software Features:**
- [Drake Tax Split Return Features](https://kb.drakesoftware.com/kb/Drake-Tax/10648.htm)
- [TaxSlayer Pro MFJ vs MFS Comparison](https://support.taxslayerpro.com/hc/en-us/articles/360009305513-Desktop-MFJ-vs-MFS-Comparison)
- [Drake Tax Net Effect of Filing Separately](https://kb.drakesoftware.com/kb/Drake-Tax/13359.htm)
- [TaxSlayer Pro Tax Preparer Guide](https://www.taxslayerpro.com/blog/post/married-filing-jointly-vs-married-filing-separate)

**IRS Rules and Compliance:**
- [IRS Itemized Deductions FAQs](https://www.irs.gov/faqs/itemized-deductions-standard-deduction/other-deduction-questions/other-deduction-questions)
- [IRS Married Couples in Business](https://www.irs.gov/businesses/small-businesses-self-employed/married-couples-in-business)
- [Drake Tax Community Property Returns](https://kb.drakesoftware.com/kb/Drake-Tax/12143.htm)

**Tax Professional Workflows:**
- [Harness - Dual-Income Tax Strategies](https://www.harness.co/articles/dual-income-tax-strategies-married-couples/)
- [Method CPA - High-Income Dual-Income Households](https://methodcpa.com/married-successful-and-overpaying-tax-planning-strategies-for-high-income-dual-income-households/)
- [Doctored Money - MFJ vs MFS Implications](https://www.doctoredmoney.org/taxes/mfj-vs-mfs)

**MFJ vs MFS Comparison Analysis:**
- [Bright Advisers - MFS vs MFJ Differences](https://brightadvisers.com/mfs-vs-mfj-key-differences-every-young-family-should-know/)
- [TaxAct MFJ vs MFS Federal and State](https://www.taxact.com/support/1157/2024/mfj-vs-mfs-federal-and-state)
- [CPA Solutions - Married Filing Separately 2025](https://weneedacpa.com/2026/01/married-filing-separately-2025/)

**2026 Tax Brackets and Rules:**
- [Tax Foundation 2026 Tax Brackets](https://taxfoundation.org/data/all/federal/2026-tax-brackets/)
- [SWAT Advisors 2026 Tax Brackets Married vs Single](https://swatadvisors.com/irs-tax-brackets-for-2026/)
- [National Debt Relief 2025-2026 Tax Brackets MFJ](https://www.nationaldebtrelief.com/blog/financial-wellness/taxes/2025-2026-tax-brackets-for-married-filing-jointly-rates-deductions-and-planning-tips/)

**Tax Planning Strategies:**
- [Defiant Capital - W-2 Tax Planning 2026](https://defiantcap.com/w2-tax-planning-strategies-high-income-earners/)
- [WCG Inc - High Earners Reduce Taxable Income 2026](https://blog.cmp.cpa/reduce-taxable-income-high-earners)
- [Uncle Kam - 2026 Tax Trends for Business Owners](https://unclekam.com/tax-strategy-blog/2026-tax-trends/)

**Mixed Income Household Planning:**
- [MileIQ - Filing Taxes One Spouse Owns Business](https://mileiq.com/blog/how-to-file-taxes-when-one-spouse-owns-a-business)
- [Haven - Filing Taxes When One Spouse Owns Business](https://www.usehaven.com/blog-posts/how-to-file-taxes-when-one-spouse-owns-a-business)
- [GRF CPAs - Hire Your Spouse Tax Strategy](https://www.grfcpa.com/resource/a-tax-smart-strategy-hire-your-spouse/)

---

**Confidence Assessment:**

| Category | Confidence | Reason |
|----------|------------|--------|
| Table Stakes | HIGH | Verified against Drake Tax, TaxSlayer Pro documentation. T/S/J attribution and MFJ vs MFS comparison are industry standard. |
| Differentiators | MEDIUM-HIGH | Per-spouse strategies and bracket visualization are logical extensions. What-if scenarios and optimization features are more speculative. |
| Anti-Features | HIGH | Deduction method enforcement is IRS rule. Auto-select caution is standard professional tool practice. |
| Complexity | HIGH | Accurate based on dual-calculation requirements and IRS rule complexity. |
| Dependencies | HIGH | Logical dependency chain verified against software architecture patterns. |
