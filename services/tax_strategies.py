"""
Tax Strategies Analysis Service
Implements comprehensive analysis of 10 key tax strategies based on tax-strategies-cursor.md
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from models import AnalysisResult


class TaxStrategyStatus:
    """Status constants for tax strategy utilization"""
    FULLY_UTILIZED = "FULLY_UTILIZED"
    PARTIALLY_UTILIZED = "PARTIALLY_UTILIZED"
    NOT_UTILIZED = "NOT_UTILIZED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR_DETECTED = "ERROR_DETECTED"
    POTENTIALLY_MISSED = "POTENTIALLY_MISSED"
    SUBOPTIMAL = "SUBOPTIMAL"
    COMPLIANT_PRE_OBBBA = "COMPLIANT_PRE_OBBBA"


class TaxStrategiesService:
    """Service for analyzing tax strategies based on extracted tax data"""
    
    # 2024/2025 tax year constants
    TAX_YEAR = 2025  # Can be made dynamic
    
    # QBI thresholds (2025)
    QBI_THRESHOLDS = {
        'single': {'phase_in_start': 191950, 'phase_in_end': 266950},
        'married_joint': {'phase_in_start': 383900, 'phase_in_end': 533900},
        'married_separate': {'phase_in_start': 191950, 'phase_in_end': 266950},
        'head_of_household': {'phase_in_start': 191950, 'phase_in_end': 266950}
    }
    
    # Section 179 limits (Post-OBBBA)
    SECTION_179_MAX = 2500000
    SECTION_179_PHASEOUT = 4000000
    
    # Retirement contribution limits (2024/2025)
    SEP_MAX = 69000
    SIMPLE_MAX = 16000
    SOLO_401K_EMPLOYEE_MAX = 23000
    SOLO_401K_TOTAL_MAX = 69000

    # Income type to relevant strategies mapping (REQ-21)
    INCOME_TYPE_STRATEGIES = {
        'w2_employee': [
            'retirement_contributions',  # 401(k) via employer
            # HSA, FSA typically employer-provided
        ],
        'self_employed': [
            'retirement_contributions',  # SEP-IRA, Solo 401(k)
            'qbi_deduction',
            'se_tax_deduction',
            'se_health_insurance',
            'home_office'
        ],
        'business_owner': [
            'qbi_deduction',
            'section_179',
            'bonus_depreciation',
            'rd_deduction',
            'fmla_credit'
        ],
        'rental_income': [
            'section_179',
            'bonus_depreciation'
        ],
        'capital_gains': [
            'qsbs_exclusion'
        ],
        'investment_income': []  # General investment income has no specific strategy prioritization
    }

    @staticmethod
    def detect_income_types(client_id):
        """
        Detect income types from client's extracted data based on form types present.

        Args:
            client_id: Client ID to check

        Returns:
            list: Income type strings (e.g., ['w2_employee', 'self_employed'])
        """
        from models import ExtractedData
        from models import db

        # Query distinct form types for this client
        forms = db.session.query(ExtractedData.form_type).filter_by(
            client_id=client_id
        ).distinct().all()
        form_types = {f[0] for f in forms if f[0]}

        income_types = []

        if 'W-2' in form_types:
            income_types.append('w2_employee')
        if 'Schedule C' in form_types:
            income_types.append('self_employed')
        if 'Schedule E' in form_types:
            income_types.append('rental_income')
        if 'K-1' in form_types:
            income_types.append('business_owner')
        if 'Schedule D' in form_types or 'Form 8949' in form_types:
            income_types.append('capital_gains')
        if '1099-INT' in form_types or '1099-DIV' in form_types:
            income_types.append('investment_income')

        return income_types if income_types else ['unknown']

    @staticmethod
    def filter_strategies_by_income_type(strategies, income_types):
        """
        Prioritize strategies relevant to detected income types.

        Moves relevant strategies to front of list, others follow.

        Args:
            strategies: List of AnalysisResult objects
            income_types: List of income type strings

        Returns:
            list: Sorted strategies with relevant ones first
        """
        import json

        # Build set of relevant strategy IDs
        relevant_ids = set()
        for income_type in income_types:
            relevant_ids.update(TaxStrategiesService.INCOME_TYPE_STRATEGIES.get(income_type, []))

        def get_relevance_key(strategy):
            """Sort key: relevant strategies first, then by priority"""
            try:
                # Parse detailed_info from strategy_description JSON
                info = json.loads(strategy.strategy_description)
                strategy_id = info.get('strategy_id', '')
                is_relevant = strategy_id in relevant_ids
                return (0 if is_relevant else 1, strategy.priority)
            except (json.JSONDecodeError, AttributeError):
                return (1, strategy.priority)

        return sorted(strategies, key=get_relevance_key)

    @staticmethod
    def get_personalized_strategies(data_by_form, client):
        """
        Get strategies personalized to client's income type.

        Analyzes all strategies, then prioritizes by income type relevance.

        Args:
            data_by_form: Dictionary of form data
            client: Client model instance

        Returns:
            tuple: (strategies_list, income_types_list)
        """
        # Detect income types
        income_types = TaxStrategiesService.detect_income_types(client.id)

        # Analyze all strategies
        strategies = TaxStrategiesService.analyze_all_strategies(data_by_form, client)

        # Filter/prioritize by income type
        prioritized = TaxStrategiesService.filter_strategies_by_income_type(strategies, income_types)

        return prioritized, income_types

    @staticmethod
    def analyze_all_strategies(data_by_form: Dict, client) -> List[AnalysisResult]:
        """
        Analyze all 10 tax strategies and return results
        
        Args:
            data_by_form: Dictionary of form data organized by form type
            client: Client model instance
            
        Returns:
            List of AnalysisResult objects
        """
        strategies = []
        
        # Strategy 1: QBI Deduction
        strategies.append(TaxStrategiesService._analyze_qbi_deduction(data_by_form, client))
        
        # Strategy 2: Section 179 Expensing
        strategies.append(TaxStrategiesService._analyze_section_179(data_by_form, client))
        
        # Strategy 3: Bonus Depreciation
        strategies.append(TaxStrategiesService._analyze_bonus_depreciation(data_by_form, client))
        
        # Strategy 4: Domestic R&D Expense Deduction
        strategies.append(TaxStrategiesService._analyze_rd_deduction(data_by_form, client))
        
        # Strategy 5: Retirement Plan Contributions
        strategies.append(TaxStrategiesService._analyze_retirement_contributions(data_by_form, client))
        
        # Strategy 6: Self-Employment Tax Deduction
        strategies.append(TaxStrategiesService._analyze_se_tax_deduction(data_by_form, client))
        
        # Strategy 7: Self-Employed Health Insurance Deduction
        strategies.append(TaxStrategiesService._analyze_se_health_insurance(data_by_form, client))
        
        # Strategy 8: Home Office Deduction
        strategies.append(TaxStrategiesService._analyze_home_office(data_by_form, client))
        
        # Strategy 9: QSBS Exclusion
        strategies.append(TaxStrategiesService._analyze_qsbs_exclusion(data_by_form, client))
        
        # Strategy 10: Paid Family and Medical Leave Credit
        strategies.append(TaxStrategiesService._analyze_fmla_credit(data_by_form, client))
        
        # Filter out None results (not applicable)
        return [s for s in strategies if s is not None]
    
    @staticmethod
    def _get_numeric_value(data_dict: Dict, form_type: str, field_name: str, default: float = 0.0) -> float:
        """Helper to get numeric value from extracted data"""
        try:
            if form_type in data_dict and field_name in data_dict[form_type]:
                value = data_dict[form_type][field_name]
                if value:
                    return float(value)
        except (ValueError, TypeError, KeyError):
            pass
        return default
    
    @staticmethod
    def _get_filing_status(client) -> str:
        """Get filing status from client, defaulting to single"""
        if hasattr(client, 'filing_status') and client.filing_status:
            return client.filing_status
        return 'single'
    
    @staticmethod
    def _create_strategy_result(
        client_id: int,
        strategy_name: str,
        strategy_id: str,
        status: str,
        current_benefit: float = 0.0,
        potential_benefit: float = 0.0,
        unused_capacity: float = 0.0,
        flags: List[str] = None,
        recommendations: List[str] = None,
        forms_analyzed: List[str] = None,
        irs_section: str = "",
        priority: int = 3,
        description: str = ""
    ) -> AnalysisResult:
        """Create an AnalysisResult with detailed strategy information"""
        if flags is None:
            flags = []
        if recommendations is None:
            recommendations = []
        if forms_analyzed is None:
            forms_analyzed = []
        
        # Build description from components
        if not description:
            description = f"Status: {status}"
            if current_benefit > 0:
                description += f" | Current Benefit: ${current_benefit:,.2f}"
            if potential_benefit > current_benefit:
                description += f" | Potential Benefit: ${potential_benefit:,.2f}"
            if unused_capacity > 0:
                description += f" | Unused Capacity: ${unused_capacity:,.2f}"
            if flags:
                description += f" | Flags: {', '.join(flags)}"
            if recommendations:
                description += f" | Recommendations: {'; '.join(recommendations)}"
        
        # Store detailed info in strategy_description as JSON-like structure
        detailed_info = {
            'strategy_id': strategy_id,
            'status': status,
            'current_benefit': current_benefit,
            'potential_benefit': potential_benefit,
            'unused_capacity': unused_capacity,
            'flags': flags,
            'recommendations': recommendations,
            'forms_analyzed': forms_analyzed
        }
        
        result = AnalysisResult(
            client_id=client_id,
            strategy_name=strategy_name,
            strategy_description=description,
            potential_savings=potential_benefit - current_benefit,
            irs_section=irs_section,
            irs_code=irs_section,
            priority=priority
        )
        
        # Store detailed info in a way we can retrieve it
        # We'll use a JSON string in strategy_description for now
        import json
        result.strategy_description = json.dumps(detailed_info)
        
        return result
    
    # Strategy 1: QBI Deduction (§ 199A)
    @staticmethod
    def _analyze_qbi_deduction(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Qualified Business Income Deduction"""
        forms_analyzed = []
        
        # Check for pass-through income
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        schedule_e_income = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule E', 'net_income', 0)
        k1_qbi = TaxStrategiesService._get_numeric_value(data_by_form, 'K-1', 'qbi_amount', 0)
        
        has_pass_through = schedule_c_profit > 0 or schedule_e_income > 0 or k1_qbi > 0
        
        if not has_pass_through:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Qualified Business Income (QBI) Deduction",
                strategy_id="qbi_deduction",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Schedule C', 'Schedule E', 'K-1'],
                irs_section="IRC Section 199A",
                priority=1,
                description="No pass-through business income detected."
            )
        
        forms_analyzed.extend(['Schedule C', 'Schedule E', 'K-1'])
        
        # Check if Form 8995 or 8995-A was filed
        form_8995_filed = 'Form 8995' in data_by_form or 'Form 8995-A' in data_by_form
        qbi_deduction = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8995', 'qbi_deduction', 0)
        if qbi_deduction == 0:
            qbi_deduction = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8995-A', 'qbi_deduction', 0)
        
        # Calculate qualified business income
        qbi = schedule_c_profit + schedule_e_income + k1_qbi
        
        # Calculate expected QBI deduction (20% of QBI, subject to limitations)
        expected_qbi_deduction = qbi * 0.20
        
        # Get taxable income for limitation check
        taxable_income = TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        qbi_limit_by_taxable = taxable_income * 0.20 if taxable_income > 0 else 0
        
        flags = []
        recommendations = []
        
        if form_8995_filed:
            if qbi_deduction > 0:
                if qbi_deduction < expected_qbi_deduction * 0.95:
                    status = TaxStrategyStatus.PARTIALLY_UTILIZED
                    flags.append("Deduction limited by W-2 wages, UBIA, or taxable income")
                    recommendations.append("Review W-2 wages and UBIA to maximize deduction")
                else:
                    status = TaxStrategyStatus.FULLY_UTILIZED
            else:
                status = TaxStrategyStatus.NOT_UTILIZED
                flags.append("QBI deduction is zero - check for SSTB limitations or loss")
                recommendations.append("Review if business qualifies as SSTB or if loss occurred")
        else:
            status = TaxStrategyStatus.NOT_UTILIZED
            flags.append("Form 8995/8995-A not filed despite pass-through income")
            recommendations.append("File Form 8995 or 8995-A to claim QBI deduction")
            qbi_deduction = 0
        
        # Calculate potential benefit
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(taxable_income)
        current_benefit = qbi_deduction * (marginal_rate / 100)
        potential_benefit = min(expected_qbi_deduction, qbi_limit_by_taxable) * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Qualified Business Income (QBI) Deduction",
            strategy_id="qbi_deduction",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 199A",
            priority=1
        )
    
    # Strategy 2: Section 179 Expensing
    @staticmethod
    def _analyze_section_179(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Section 179 Expensing"""
        forms_analyzed = []
        
        # Check Form 4562 for Section 179
        form_4562_part1 = 'Form 4562' in data_by_form
        line_12_deduction = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'section_179_deduction', 0)
        line_2_cost = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'total_cost_179_property', 0)
        line_11_limitation = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'business_income_limitation', 0)
        
        # Check Schedule C for business property
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        business_property_acquired = line_2_cost > 0 or schedule_c_profit > 0
        
        if not business_property_acquired:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Section 179 Expensing",
                strategy_id="section_179",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Form 4562', 'Schedule C'],
                irs_section="IRC Section 179",
                priority=1,
                description="No business property acquisitions detected."
            )
        
        forms_analyzed.extend(['Form 4562', 'Schedule C'])
        
        flags = []
        recommendations = []
        
        if form_4562_part1:
            if line_12_deduction > 0:
                status = TaxStrategyStatus.FULLY_UTILIZED
                if line_12_deduction < line_2_cost and line_12_deduction < TaxStrategiesService.SECTION_179_MAX:
                    if line_11_limitation > 0 and line_12_deduction < line_11_limitation:
                        status = TaxStrategyStatus.PARTIALLY_UTILIZED
                        flags.append("Limited by business income")
                        carryforward = line_2_cost - line_12_deduction
                        recommendations.append(f"Carryforward available: ${carryforward:,.2f}")
            else:
                status = TaxStrategyStatus.NOT_UTILIZED
                flags.append("Section 179 election not made for qualifying property")
                recommendations.append("Consider electing Section 179 for qualifying business property")
        else:
            status = TaxStrategyStatus.POTENTIALLY_MISSED
            flags.append("Review asset purchases for 179 eligibility")
            recommendations.append("File Form 4562 Part I if qualifying property was acquired")
        
        # Calculate benefits
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = line_12_deduction * (marginal_rate / 100)
        potential_benefit = min(line_2_cost, TaxStrategiesService.SECTION_179_MAX) * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Section 179 Expensing",
            strategy_id="section_179",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 179",
            priority=1
        )
    
    # Strategy 3: Bonus Depreciation
    @staticmethod
    def _analyze_bonus_depreciation(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Bonus Depreciation (Full Expensing)"""
        forms_analyzed = []
        
        # Check Form 4562 Part II for bonus depreciation
        line_14_bonus = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'bonus_depreciation', 0)
        form_4562_part3 = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'macrs_depreciation', 0)
        
        depreciable_property = line_14_bonus > 0 or form_4562_part3 > 0
        
        if not depreciable_property:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Bonus Depreciation (Full Expensing)",
                strategy_id="bonus_depreciation",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Form 4562'],
                irs_section="IRC Section 168(k)",
                priority=1,
                description="No depreciable property detected."
            )
        
        forms_analyzed.append('Form 4562')
        
        flags = []
        recommendations = []
        
        if line_14_bonus > 0:
            status = TaxStrategyStatus.FULLY_UTILIZED
            # Check if all eligible property claimed bonus
            if form_4562_part3 > 0:
                flags.append("Some property depreciated under MACRS - verify if election out was intentional")
        else:
            if form_4562_part3 > 0:
                status = TaxStrategyStatus.POTENTIALLY_MISSED
                flags.append("Property depreciated under MACRS may qualify for bonus")
                recommendations.append("Review for election out under § 168(k)(7)")
            else:
                status = TaxStrategyStatus.NOT_APPLICABLE
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = line_14_bonus * (marginal_rate / 100)
        potential_benefit = (line_14_bonus + form_4562_part3) * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Bonus Depreciation (Full Expensing)",
            strategy_id="bonus_depreciation",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 168(k)",
            priority=1
        )
    
    # Strategy 4: Domestic R&D Expense Deduction
    @staticmethod
    def _analyze_rd_deduction(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Domestic R&D Expense Deduction (§ 174A)"""
        forms_analyzed = []
        
        # Check for R&D indicators
        form_6765_filed = 'Form 6765' in data_by_form
        rd_expenses = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'rd_expenses', 0)
        rd_amortization = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 4562', 'rd_amortization', 0)
        
        # Check business type indicators (simplified)
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        
        if rd_expenses == 0 and not form_6765_filed and schedule_c_profit == 0:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Domestic R&D Expense Deduction",
                strategy_id="rd_deduction",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Form 6765', 'Schedule C', 'Form 4562'],
                irs_section="IRC Section 174A",
                priority=2,
                description="No R&D expenses detected."
            )
        
        forms_analyzed.extend(['Form 6765', 'Schedule C', 'Form 4562'])
        
        flags = []
        recommendations = []
        
        if TaxStrategiesService.TAX_YEAR >= 2025:
            if rd_expenses > 0 and rd_amortization == 0:
                status = TaxStrategyStatus.FULLY_UTILIZED
            elif rd_amortization > 0:
                status = TaxStrategyStatus.SUBOPTIMAL
                flags.append("Elective amortization chosen over immediate deduction")
                recommendations.append("Consider immediate deduction under § 174A (may be strategic for NOL management)")
            else:
                status = TaxStrategyStatus.NOT_UTILIZED
        else:
            if rd_amortization > 0:
                status = TaxStrategyStatus.COMPLIANT_PRE_OBBBA
                flags.append("Check for OBBBA retroactive election if applicable")
            else:
                status = TaxStrategyStatus.NOT_UTILIZED
        
        if form_6765_filed and rd_expenses == 0:
            flags.append("R&D credit claimed but no 174A deduction identified")
            recommendations.append("Review R&D expenses for § 174A deduction eligibility")
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = 0  # Amortization provides less benefit
        potential_benefit = rd_expenses * (marginal_rate / 100) if rd_expenses > 0 else 0
        unused_capacity = potential_benefit - current_benefit
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Domestic R&D Expense Deduction",
            strategy_id="rd_deduction",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 174A",
            priority=2
        )
    
    # Strategy 5: Retirement Plan Contributions
    @staticmethod
    def _analyze_retirement_contributions(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Retirement Plan Contributions"""
        forms_analyzed = []
        
        # Get self-employment income
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        schedule_se_income = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule SE', 'net_earnings', 0)
        
        # Get retirement contributions
        schedule_1_line_16 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule 1', 'retirement_contributions', 0)
        form_5498_sep = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 5498', 'sep_contributions', 0)
        form_5498_simple = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 5498', 'simple_contributions', 0)
        
        self_employment_income = max(schedule_c_profit, schedule_se_income)
        
        if self_employment_income <= 0:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Retirement Plan Contributions",
                strategy_id="retirement_contributions",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Schedule C', 'Schedule SE', 'Schedule 1', 'Form 5498'],
                irs_section="IRC Section 219, 401(k), 408, 404",
                priority=2,
                description="No self-employment income detected."
            )
        
        forms_analyzed.extend(['Schedule C', 'Schedule SE', 'Schedule 1', 'Form 5498'])
        
        # Calculate max SEP contribution (25% of net SE income, capped at $69,000)
        max_sep_contribution = min(self_employment_income * 0.25, TaxStrategiesService.SEP_MAX)
        
        total_contributions = schedule_1_line_16 + form_5498_sep + form_5498_simple
        
        flags = []
        recommendations = []
        
        if total_contributions > 0:
            if total_contributions >= max_sep_contribution * 0.90:
                status = TaxStrategyStatus.FULLY_UTILIZED
            else:
                status = TaxStrategyStatus.PARTIALLY_UTILIZED
                unused_capacity = max_sep_contribution - total_contributions
                recommendations.append(f"Additional contribution capacity: ${unused_capacity:,.2f}")
        else:
            status = TaxStrategyStatus.NOT_UTILIZED
            recommendations.append("Consider SEP-IRA, SIMPLE, or Solo 401(k)")
        
        # High income flag
        if self_employment_income > 200000 and total_contributions < 50000:
            flags.append("SIGNIFICANT_OPTIMIZATION_OPPORTUNITY")
            recommendations.append("Consider defined benefit plan for maximum deduction")
        
        # Solo 401(k) flag
        if schedule_c_profit > 50000 and form_5498_sep > 0:
            flags.append("SOLO_401K_MAY_BE_BETTER")
            recommendations.append("Solo 401(k) allows employee + employer contributions")
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = total_contributions * (marginal_rate / 100)
        potential_benefit = max_sep_contribution * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Retirement Plan Contributions",
            strategy_id="retirement_contributions",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 219, 401(k), 408, 404",
            priority=2
        )
    
    # Strategy 6: Self-Employment Tax Deduction
    @staticmethod
    def _analyze_se_tax_deduction(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Self-Employment Tax Deduction (§ 164(f))"""
        forms_analyzed = []
        
        schedule_se_filed = 'Schedule SE' in data_by_form
        schedule_se_line_6 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule SE', 'total_se_tax', 0)
        schedule_1_line_15 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule 1', 'se_tax_deduction', 0)
        
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        schedule_f_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule F', 'net_profit', 0)
        
        if not schedule_se_filed:
            if schedule_c_profit > 400 or schedule_f_profit > 400:
                return TaxStrategiesService._create_strategy_result(
                    client_id=client.id,
                    strategy_name="Self-Employment Tax Deduction",
                    strategy_id="se_tax_deduction",
                    status=TaxStrategyStatus.ERROR_DETECTED,
                    flags=["Schedule SE required but not filed"],
                    recommendations=["File Schedule SE for self-employment income"],
                    forms_analyzed=['Schedule C', 'Schedule F'],
                    irs_section="IRC Section 164(f)",
                    priority=1
                )
            else:
                return TaxStrategiesService._create_strategy_result(
                    client_id=client.id,
                    strategy_name="Self-Employment Tax Deduction",
                    strategy_id="se_tax_deduction",
                    status=TaxStrategyStatus.NOT_APPLICABLE,
                    forms_analyzed=['Schedule C', 'Schedule F'],
                    irs_section="IRC Section 164(f)",
                    priority=1
                )
        
        forms_analyzed.extend(['Schedule SE', 'Schedule 1'])
        
        expected_deduction = schedule_se_line_6 * 0.50
        flags = []
        recommendations = []
        
        if abs(schedule_1_line_15 - expected_deduction) < 0.01:
            status = TaxStrategyStatus.FULLY_UTILIZED
        elif schedule_1_line_15 < expected_deduction:
            status = TaxStrategyStatus.ERROR_DETECTED
            flags.append("Deduction appears understated")
            recommendations.append("Verify Schedule 1 Line 15 equals Schedule SE Line 13")
        elif schedule_1_line_15 == 0 and schedule_se_line_6 > 0:
            status = TaxStrategyStatus.NOT_UTILIZED
            flags.append("CRITICAL: Missing deduction")
            recommendations.append("Claim 50% of self-employment tax on Schedule 1 Line 15")
        else:
            status = TaxStrategyStatus.FULLY_UTILIZED
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = schedule_1_line_15 * (marginal_rate / 100)
        potential_benefit = expected_deduction * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Self-Employment Tax Deduction",
            strategy_id="se_tax_deduction",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 164(f)",
            priority=1
        )
    
    # Strategy 7: Self-Employed Health Insurance Deduction
    @staticmethod
    def _analyze_se_health_insurance(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Self-Employed Health Insurance Deduction (§ 162(l))"""
        forms_analyzed = []
        
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        schedule_se_line_6 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule SE', 'total_se_tax', 0)
        schedule_1_line_17 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule 1', 'se_health_insurance', 0)
        
        # Estimate health insurance premiums (would need actual data)
        health_premiums = TaxStrategiesService._get_numeric_value(data_by_form, '1095-A', 'premiums', 0)
        
        if schedule_c_profit == 0:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Self-Employed Health Insurance Deduction",
                strategy_id="se_health_insurance",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Schedule C', 'Schedule SE', 'Schedule 1', 'Form 1095-A'],
                irs_section="IRC Section 162(l)",
                priority=2,
                description="No self-employment income detected."
            )
        
        forms_analyzed.extend(['Schedule C', 'Schedule SE', 'Schedule 1', 'Form 1095-A'])
        
        # Calculate net SE income (after SE tax deduction)
        net_se_income = schedule_c_profit - (schedule_se_line_6 * 0.5)
        deduction_limit = min(health_premiums if health_premiums > 0 else 10000, net_se_income)  # Estimate if not available
        
        flags = []
        recommendations = []
        
        if schedule_1_line_17 >= deduction_limit * 0.95:
            status = TaxStrategyStatus.FULLY_UTILIZED
        elif schedule_1_line_17 > 0:
            status = TaxStrategyStatus.PARTIALLY_UTILIZED
            unused = deduction_limit - schedule_1_line_17
            recommendations.append(f"Additional deduction available: ${unused:,.2f}")
        else:
            status = TaxStrategyStatus.NOT_UTILIZED
            flags.append("CRITICAL: Missing deduction for health insurance")
            recommendations.append("Claim self-employed health insurance deduction on Schedule 1 Line 17")
        
        # Check for PTC coordination
        if 'Form 8962' in data_by_form:
            flags.append("Verify PTC coordination is correct")
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = schedule_1_line_17 * (marginal_rate / 100)
        potential_benefit = deduction_limit * (marginal_rate / 100)
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Self-Employed Health Insurance Deduction",
            strategy_id="se_health_insurance",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 162(l)",
            priority=2
        )
    
    # Strategy 8: Home Office Deduction
    @staticmethod
    def _analyze_home_office(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Home Office Deduction (§ 280A(c))"""
        forms_analyzed = []
        
        form_8829_filed = 'Form 8829' in data_by_form
        form_8829_line_36 = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8829', 'home_office_deduction', 0)
        form_8829_line_35 = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8829', 'tentative_deduction', 0)
        schedule_c_line_18 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'simplified_home_office', 0)
        schedule_c_line_30 = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'home_office_deduction', 0)
        
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        
        if schedule_c_profit == 0:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Home Office Deduction",
                strategy_id="home_office",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Form 8829', 'Schedule C'],
                irs_section="IRC Section 280A(c)",
                priority=3,
                description="No business income detected."
            )
        
        forms_analyzed.extend(['Form 8829', 'Schedule C'])
        
        flags = []
        recommendations = []
        
        if form_8829_filed:
            status = TaxStrategyStatus.FULLY_UTILIZED
            if form_8829_line_35 > form_8829_line_36:
                status = TaxStrategyStatus.PARTIALLY_UTILIZED
                flags.append("Limited by gross income")
                carryforward = form_8829_line_35 - form_8829_line_36
                recommendations.append(f"Carryforward available: ${carryforward:,.2f}")
        elif schedule_c_line_18 > 0 or schedule_c_line_30 > 0:
            deduction = schedule_c_line_18 + schedule_c_line_30
            if deduction <= 1500:
                status = TaxStrategyStatus.FULLY_UTILIZED
                flags.append("Simplified method used")
                recommendations.append("Consider regular method if actual expenses higher")
            else:
                status = TaxStrategyStatus.FULLY_UTILIZED
        else:
            status = TaxStrategyStatus.NOT_UTILIZED
            flags.append("Potential deduction missed")
            recommendations.append("Review home office eligibility and expenses")
        
        deduction_amount = form_8829_line_36 if form_8829_line_36 > 0 else (schedule_c_line_18 + schedule_c_line_30)
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = deduction_amount * (marginal_rate / 100)
        potential_benefit = current_benefit * 1.2  # Estimate 20% more potential
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Home Office Deduction",
            strategy_id="home_office",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 280A(c)",
            priority=3
        )
    
    # Strategy 9: QSBS Exclusion
    @staticmethod
    def _analyze_qsbs_exclusion(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Qualified Small Business Stock (QSBS) Exclusion (§ 1202)"""
        forms_analyzed = []
        
        schedule_d_filed = 'Schedule D' in data_by_form
        form_8949_code_q = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8949', 'qsbs_exclusion', 0)
        capital_gains = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule D', 'capital_gains', 0)
        
        if not schedule_d_filed and capital_gains == 0:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Qualified Small Business Stock (QSBS) Exclusion",
                strategy_id="qsbs_exclusion",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Schedule D', 'Form 8949'],
                irs_section="IRC Section 1202",
                priority=4,
                description="No stock sales or capital gains detected."
            )
        
        forms_analyzed.extend(['Schedule D', 'Form 8949'])
        
        flags = []
        recommendations = []
        
        if form_8949_code_q > 0:
            status = TaxStrategyStatus.FULLY_UTILIZED
            # Check exclusion percentage (would need holding period data)
            flags.append("QSBS exclusion claimed")
        else:
            if capital_gains > 0:
                status = TaxStrategyStatus.POTENTIALLY_MISSED
                flags.append("INVESTIGATE_QSBS_ELIGIBILITY")
                recommendations.extend([
                    "Was stock acquired at original issuance?",
                    "Was corporation a C-corp with <$50M gross assets?",
                    "Is corporation in qualified trade or business?",
                    "Was stock held for required period (3-5 years)?"
                ])
            else:
                status = TaxStrategyStatus.NOT_APPLICABLE
        
        marginal_rate = TaxStrategiesService._estimate_marginal_rate(
            TaxStrategiesService._get_numeric_value(data_by_form, '1040', 'taxable_income', 0)
        )
        current_benefit = form_8949_code_q * (marginal_rate / 100)
        potential_benefit = capital_gains * 0.5 * (marginal_rate / 100) if capital_gains > 0 else 0  # Estimate 50% exclusion
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Qualified Small Business Stock (QSBS) Exclusion",
            strategy_id="qsbs_exclusion",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 1202",
            priority=4
        )
    
    # Strategy 10: Paid Family and Medical Leave Credit
    @staticmethod
    def _analyze_fmla_credit(data_by_form: Dict, client) -> Optional[AnalysisResult]:
        """Analyze Paid Family and Medical Leave Credit (§ 45S)"""
        forms_analyzed = []
        
        form_8994_filed = 'Form 8994' in data_by_form
        form_8994_line_3 = TaxStrategiesService._get_numeric_value(data_by_form, 'Form 8994', 'credit_amount', 0)
        w2_employees = TaxStrategiesService._get_numeric_value(data_by_form, 'W-2', 'employee_count', 0)
        
        # Check for business with employees
        schedule_c_profit = TaxStrategiesService._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        has_business = schedule_c_profit > 0 or w2_employees > 0
        
        if not has_business:
            return TaxStrategiesService._create_strategy_result(
                client_id=client.id,
                strategy_name="Paid Family and Medical Leave Credit",
                strategy_id="fmla_credit",
                status=TaxStrategyStatus.NOT_APPLICABLE,
                forms_analyzed=['Form 8994', 'W-2', 'Schedule C'],
                irs_section="IRC Section 45S",
                priority=4,
                description="No business with employees detected."
            )
        
        forms_analyzed.extend(['Form 8994', 'W-2', 'Schedule C'])
        
        flags = []
        recommendations = []
        
        if form_8994_filed:
            if form_8994_line_3 > 0:
                status = TaxStrategyStatus.FULLY_UTILIZED
            else:
                status = TaxStrategyStatus.NOT_UTILIZED
                flags.append("Form filed but no credit - check qualifying employee criteria")
        else:
            if w2_employees > 0:
                status = TaxStrategyStatus.POTENTIALLY_MISSED
                flags.append("INVESTIGATE_FMLA_CREDIT_ELIGIBILITY")
                recommendations.extend([
                    "Does employer have written FMLA policy?",
                    "Were employees paid during FMLA leave?",
                    "Did employees earn <$78,000 (2024)?",
                    "Were employees employed 1+ year?",
                    "Do employees work 20+ hours/week?"
                ])
            else:
                status = TaxStrategyStatus.NOT_APPLICABLE
        
        current_benefit = form_8994_line_3
        potential_benefit = current_benefit * 1.5 if current_benefit > 0 else 0  # Estimate
        unused_capacity = max(0, potential_benefit - current_benefit)
        
        return TaxStrategiesService._create_strategy_result(
            client_id=client.id,
            strategy_name="Paid Family and Medical Leave Credit",
            strategy_id="fmla_credit",
            status=status,
            current_benefit=current_benefit,
            potential_benefit=potential_benefit,
            unused_capacity=unused_capacity,
            flags=flags,
            recommendations=recommendations,
            forms_analyzed=forms_analyzed,
            irs_section="IRC Section 45S",
            priority=4
        )
    
    @staticmethod
    def _estimate_marginal_rate(taxable_income: float) -> float:
        """Estimate marginal tax rate based on 2024 tax brackets"""
        if taxable_income <= 0:
            return 0
        elif taxable_income <= 11600:
            return 10
        elif taxable_income <= 47150:
            return 12
        elif taxable_income <= 100525:
            return 22
        elif taxable_income <= 191950:
            return 24
        elif taxable_income <= 243725:
            return 32
        elif taxable_income <= 609350:
            return 35
        else:
            return 37

