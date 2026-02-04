"""
Joint Strategy Service - MFJ-Only Optimization Strategies

Generates strategies that are only available when filing jointly:
- Spousal IRA (non-working spouse can contribute using working spouse's income)
- Bracket Utilization (wider MFJ brackets save money vs 2x MFS brackets)
- EITC Eligibility (MFS filers are generally ineligible)
- Education Credits (AOTC, LLC unavailable for MFS)

These strategies are NOT personalized to income type - they're joint optimizations.
"""


class JointStrategyService:
    """Service for generating joint-only optimization strategies"""

    # 2026 IRA limits
    IRA_LIMIT_2026 = 7500
    IRA_CATCHUP_2026 = 1000  # Additional for 50+

    # Strategy definitions
    JOINT_STRATEGIES = [
        {
            'id': 'spousal_ira',
            'name': 'Spousal IRA Contribution',
            'requires': 'married_joint',
            'description': 'Non-working spouse can contribute to IRA using working spouse earned income',
            'check_method': '_check_spousal_ira'
        },
        {
            'id': 'bracket_utilization',
            'name': 'MFJ Bracket Utilization',
            'requires': 'married_joint',
            'description': 'MFJ brackets are wider, keeping more income in lower tiers',
            'check_method': '_check_bracket_benefit'
        },
        {
            'id': 'eitc_eligibility',
            'name': 'Earned Income Tax Credit (EITC)',
            'requires': 'married_joint',
            'description': 'Up to $8,046 credit for qualifying families',
            'check_method': '_check_eitc'
        },
        {
            'id': 'education_credits',
            'name': 'Education Credits (AOTC/LLC)',
            'requires': 'married_joint',
            'description': 'American Opportunity ($2,500) and Lifetime Learning ($2,000) credits',
            'check_method': '_check_education_credits'
        }
    ]

    # Filing status requirements for all strategies (including individual ones)
    STRATEGY_FILING_REQUIREMENTS = {
        'spousal_ira': {'requires': 'married_joint', 'warning': 'Spousal IRA requires filing jointly'},
        'eitc_eligibility': {'requires': 'married_joint', 'warning': 'EITC unavailable when filing separately'},
        'education_credits': {'requires': 'married_joint', 'warning': 'Education credits unavailable when filing separately'},
        'student_loan_interest': {'requires': 'married_joint', 'warning': 'Student loan interest deduction unavailable when filing separately'},
        'adoption_credit': {'requires': 'married_joint', 'warning': 'Adoption credit unavailable when filing separately'},
        'roth_ira_direct': {'mfs_limit': 10000, 'warning': 'Roth IRA MAGI limit is $10,000 for MFS (vs $230,000 MFJ)'},
        # Most strategies have no filing status restriction
        'qbi_deduction': {'requires': None, 'note': 'Available for both MFJ and MFS, but thresholds differ'},
        'retirement_contributions': {'requires': None, 'note': 'Available for both filing statuses'},
        'section_179': {'requires': None, 'note': 'Available for both filing statuses'},
        'bonus_depreciation': {'requires': None, 'note': 'Available for both filing statuses'},
        'home_office': {'requires': None, 'note': 'Available for both filing statuses'},
        'se_tax_deduction': {'requires': None, 'note': 'Available for both filing statuses'},
        'se_health_insurance': {'requires': None, 'note': 'Available for both filing statuses'},
    }

    @staticmethod
    def generate_joint_strategies(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        """
        Generate strategies available only when filing jointly.

        Args:
            spouse1_summary: Analysis summary for spouse 1
            spouse2_summary: Analysis summary for spouse 2
            mfj_result: MFJ calculation result dict
            mfs_result: MFS calculation result dict (combined both spouses)

        Returns:
            list: Joint strategy recommendations
        """
        strategies = []

        for strategy_def in JointStrategyService.JOINT_STRATEGIES:
            check_method = getattr(JointStrategyService, strategy_def['check_method'])
            result = check_method(spouse1_summary, spouse2_summary, mfj_result, mfs_result)

            if result['applicable']:
                strategies.append({
                    'strategy_id': strategy_def['id'],
                    'strategy_name': strategy_def['name'],
                    'requires_filing_status': strategy_def['requires'],
                    'description': strategy_def['description'],
                    'status': result['status'],
                    'potential_benefit': result.get('benefit', 0),
                    'recommendation': result.get('recommendation', ''),
                    'details': result.get('details', {}),
                    'warning_if_mfs': f"Not available with MFS: {strategy_def['name']}"
                })

        return strategies

    @staticmethod
    def get_filing_requirement(strategy_id):
        """
        Get filing status requirement for a strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            dict: {requires, warning} or None if no requirement
        """
        return JointStrategyService.STRATEGY_FILING_REQUIREMENTS.get(strategy_id)

    @staticmethod
    def _check_spousal_ira(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        """Check Spousal IRA eligibility and benefit"""
        spouse1_income = spouse1_summary.get('total_income', 0)
        spouse2_income = spouse2_summary.get('total_income', 0)
        combined_income = spouse1_income + spouse2_income

        # Spousal IRA requires one spouse with low/no earned income
        # while the other has sufficient income to cover contributions
        limit = JointStrategyService.IRA_LIMIT_2026

        low_income_spouse = None
        if spouse1_income < limit and spouse2_income >= limit:
            low_income_spouse = 'spouse1'
            working_spouse_income = spouse2_income
        elif spouse2_income < limit and spouse1_income >= limit:
            low_income_spouse = 'spouse2'
            working_spouse_income = spouse1_income
        else:
            # Both have sufficient income - no spousal IRA benefit
            return {
                'applicable': False,
                'reason': 'Both spouses have sufficient earned income for their own IRA'
            }

        # Calculate tax benefit (estimate 22% marginal rate if unknown)
        marginal_rate = mfj_result.get('marginal_rate', 22) / 100
        max_contribution = limit
        benefit = max_contribution * marginal_rate

        return {
            'applicable': True,
            'status': 'POTENTIALLY_MISSED',
            'benefit': round(benefit, 2),
            'recommendation': f"Non-working spouse ({low_income_spouse}) can contribute up to ${max_contribution:,} to IRA using working spouse's earned income",
            'details': {
                'beneficiary': low_income_spouse,
                'max_contribution': max_contribution,
                'estimated_tax_savings': round(benefit, 2),
                'working_spouse_income': working_spouse_income
            }
        }

    @staticmethod
    def _check_bracket_benefit(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        """Check MFJ bracket utilization benefit"""
        mfj_tax = mfj_result.get('total_tax', 0)
        mfs_combined_tax = mfs_result.get('mfs_combined_tax', 0) if isinstance(mfs_result, dict) else 0

        if mfs_combined_tax <= 0:
            return {'applicable': False, 'reason': 'MFS tax data not available'}

        # Calculate bracket savings
        savings = mfs_combined_tax - mfj_tax

        if savings <= 0:
            return {
                'applicable': True,
                'status': 'NOT_APPLICABLE',
                'benefit': 0,
                'recommendation': 'MFJ does not provide bracket savings in this case',
                'details': {}
            }

        mfj_effective = mfj_result.get('effective_rate', 0)
        combined_income = mfj_result.get('combined_income', 0)

        return {
            'applicable': True,
            'status': 'FULLY_UTILIZED' if savings > 0 else 'NOT_APPLICABLE',
            'benefit': round(savings, 2),
            'recommendation': f"Filing jointly saves ${savings:,.2f} through wider tax brackets (effective rate: {mfj_effective:.1f}%)",
            'details': {
                'mfj_tax': mfj_tax,
                'mfs_combined_tax': mfs_combined_tax,
                'savings': savings,
                'effective_rate_mfj': mfj_effective
            }
        }

    @staticmethod
    def _check_eitc(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        """Check EITC eligibility"""
        combined_income = mfj_result.get('combined_income', 0)

        # 2026 EITC income limits (no children) - rough check
        # MFJ with no children: ~$25,500 max
        # MFJ with 3+ children: ~$66,800 max
        eitc_max_income = 66800  # Assume children for max benefit

        if combined_income > eitc_max_income:
            return {
                'applicable': True,
                'status': 'NOT_APPLICABLE',
                'benefit': 0,
                'recommendation': f'Income (${combined_income:,.0f}) exceeds EITC limit',
                'details': {'income_limit': eitc_max_income}
            }

        # EITC is complex - just flag as potential
        return {
            'applicable': True,
            'status': 'POTENTIALLY_MISSED',
            'benefit': 0,  # Would need dependent info for accurate calc
            'recommendation': 'EITC may be available - requires qualifying children and income verification',
            'details': {
                'note': 'EITC is completely unavailable for MFS filers',
                'max_credit_2026': 8046  # With 3+ children
            }
        }

    @staticmethod
    def _check_education_credits(spouse1_summary, spouse2_summary, mfj_result, mfs_result):
        """Check education credit eligibility"""
        combined_income = mfj_result.get('combined_income', 0)

        # AOTC phase-out: $160k-$180k MFJ (2026 estimate)
        # LLC phase-out: $160k-$180k MFJ
        aotc_limit = 180000
        llc_limit = 180000

        if combined_income > aotc_limit:
            return {
                'applicable': True,
                'status': 'NOT_APPLICABLE',
                'benefit': 0,
                'recommendation': f'Income exceeds education credit limits',
                'details': {}
            }

        return {
            'applicable': True,
            'status': 'POTENTIALLY_MISSED',
            'benefit': 0,  # Would need education expenses for calc
            'recommendation': 'Education credits may be available if paying qualified education expenses. AOTC up to $2,500, LLC up to $2,000.',
            'details': {
                'note': 'Education credits are completely unavailable for MFS filers',
                'aotc_max': 2500,
                'llc_max': 2000
            }
        }
