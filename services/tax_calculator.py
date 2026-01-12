from models import TaxBracket, StandardDeduction
from decimal import Decimal, ROUND_HALF_UP

class TaxCalculator:
    """Service for calculating federal and state tax liability"""
    
    # Dependent exemption amount (2026)
    DEPENDENT_EXEMPTION = 0  # Note: Personal exemptions were suspended, but dependents may affect other credits
    
    @staticmethod
    def convert_income_to_annual(amount, frequency):
        """
        Convert income from various frequencies to annual amount.
        
        Args:
            amount: Income amount
            frequency: 'annual', 'monthly', 'bi_monthly', 'bi_weekly', 'weekly'
        
        Returns:
            float: Annual income amount
        """
        if not amount or amount <= 0:
            return 0.0
        
        conversion_factors = {
            'annual': 1.0,
            'monthly': 12.0,
            'bi_monthly': 24.0,
            'bi_weekly': 26.0,  # 52 weeks / 2
            'weekly': 52.0
        }
        
        factor = conversion_factors.get(frequency.lower(), 1.0)
        return float(amount) * factor
    
    @staticmethod
    def get_standard_deduction(filing_status, tax_type='federal', state_code=None, tax_year=2026):
        """
        Retrieve standard deduction for given parameters.
        
        Args:
            filing_status: Filing status string
            tax_type: 'federal' or 'state'
            state_code: 2-letter state code (None for federal)
            tax_year: Tax year
        
        Returns:
            float: Standard deduction amount, or 0 if not found
        """
        query = StandardDeduction.query.filter_by(
            tax_type=tax_type,
            filing_status=filing_status,
            tax_year=tax_year
        )
        
        if tax_type == 'state' and state_code:
            query = query.filter_by(state_code=state_code)
        elif tax_type == 'federal':
            query = query.filter_by(state_code=None)
        
        deduction = query.first()
        return deduction.deduction_amount if deduction else 0.0
    
    @staticmethod
    def calculate_taxable_income(gross_income, standard_deduction, qbi_deduction=0.0):
        """
        Calculate taxable income after standard deduction and QBI deduction.
        Note: Dependents no longer affect taxable income (personal exemptions were suspended).
        Child Tax Credit is applied separately as a credit against tax liability.
        
        Args:
            gross_income: Gross annual income
            standard_deduction: Standard deduction amount
            qbi_deduction: QBI deduction amount (optional, defaults to 0)
        
        Returns:
            float: Taxable income
        """
        taxable = gross_income - standard_deduction - qbi_deduction
        return max(0.0, taxable)  # Cannot be negative
    
    @staticmethod
    def get_tax_brackets(tax_type='federal', state_code=None, filing_status='single', tax_year=2026):
        """
        Retrieve tax brackets for given parameters.
        
        Args:
            tax_type: 'federal' or 'state'
            state_code: 2-letter state code (None for federal)
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            list: List of TaxBracket objects, sorted by bracket_min
        """
        query = TaxBracket.query.filter_by(
            tax_type=tax_type,
            filing_status=filing_status,
            tax_year=tax_year
        )
        
        if tax_type == 'state' and state_code:
            query = query.filter_by(state_code=state_code)
        elif tax_type == 'federal':
            query = query.filter_by(state_code=None)
        
        brackets = query.order_by(TaxBracket.bracket_min.asc()).all()
        return brackets
    
    @staticmethod
    def calculate_tax_by_brackets(taxable_income, brackets):
        """
        Calculate tax liability using progressive tax brackets.
        
        Args:
            taxable_income: Taxable income amount
            brackets: List of TaxBracket objects, sorted by bracket_min
        
        Returns:
            dict: {
                'total_tax': total tax amount,
                'bracket_breakdown': list of dicts with bracket details,
                'marginal_rate': highest applicable tax rate
            }
        """
        if not brackets or taxable_income <= 0:
            return {
                'total_tax': 0.0,
                'bracket_breakdown': [],
                'marginal_rate': 0.0
            }
        
        total_tax = 0.0
        bracket_breakdown = []
        marginal_rate = 0.0
        
        remaining_income = taxable_income
        
        for bracket in brackets:
            bracket_min = bracket.bracket_min
            bracket_max = bracket.bracket_max if bracket.bracket_max else float('inf')
            tax_rate = bracket.tax_rate
            
            if taxable_income <= bracket_min:
                # Income hasn't reached this bracket yet
                break
            
            # Calculate taxable amount in this bracket
            bracket_income = min(remaining_income, bracket_max - bracket_min) if bracket_max else remaining_income
            
            if bracket_income > 0:
                bracket_tax = bracket_income * tax_rate
                total_tax += bracket_tax
                marginal_rate = tax_rate
                
                # Convert Infinity to None for JSON serialization
                bracket_max_serializable = None if bracket_max == float('inf') else bracket_max
                
                bracket_breakdown.append({
                    'bracket_min': bracket_min,
                    'bracket_max': bracket_max_serializable,
                    'tax_rate': tax_rate,
                    'taxable_in_bracket': bracket_income,
                    'tax_in_bracket': bracket_tax
                })
                
                remaining_income -= bracket_income
                
                if remaining_income <= 0:
                    break
        
        return {
            'total_tax': round(total_tax, 2),
            'bracket_breakdown': bracket_breakdown,
            'marginal_rate': marginal_rate
        }
    
    @staticmethod
    def calculate_fica_tax(salary, filing_status='single', tax_year=2026):
        """
        Calculate FICA taxes (Social Security + Medicare) for S-Corp salary.
        Includes both employee and employer portions (15.3% total).
        
        Args:
            salary: Annual salary amount
            filing_status: Filing status (for Medicare surtax threshold)
            tax_year: Tax year
        
        Returns:
            dict: FICA tax breakdown
        """
        # 2026 estimated wage base (adjust from 2024's $168,600)
        SOCIAL_SECURITY_WAGE_BASE = 175000
        SOCIAL_SECURITY_RATE = 0.062  # 6.2% employee + 6.2% employer = 12.4% total
        MEDICARE_RATE = 0.0145  # 1.45% employee + 1.45% employer = 2.9% total
        MEDICARE_SURTAX_RATE = 0.009  # 0.9% additional Medicare surtax
        
        # Medicare surtax thresholds (2026 estimates)
        MEDICARE_SURTAX_THRESHOLD_SINGLE = 200000
        MEDICARE_SURTAX_THRESHOLD_MARRIED = 250000
        
        # Social Security tax (capped at wage base)
        ss_taxable = min(salary, SOCIAL_SECURITY_WAGE_BASE)
        social_security_tax = ss_taxable * SOCIAL_SECURITY_RATE
        
        # Medicare tax (on all salary)
        medicare_tax = salary * MEDICARE_RATE
        
        # Medicare surtax (on income above threshold)
        surtax_threshold = MEDICARE_SURTAX_THRESHOLD_MARRIED if filing_status == 'married_joint' else MEDICARE_SURTAX_THRESHOLD_SINGLE
        medicare_surtax = max(0, (salary - surtax_threshold) * MEDICARE_SURTAX_RATE) if salary > surtax_threshold else 0.0
        
        total_fica = social_security_tax + medicare_tax + medicare_surtax
        
        return {
            'social_security_tax': round(social_security_tax, 2),
            'medicare_tax': round(medicare_tax, 2),
            'medicare_surtax': round(medicare_surtax, 2),
            'total_fica_tax': round(total_fica, 2),
            'fica_rate': 0.153  # 15.3% base rate
        }
    
    @staticmethod
    def calculate_self_employment_tax(net_income, tax_year=2026):
        """
        Calculate self-employment tax for LLC income.
        15.3% on net income (12.4% Social Security + 2.9% Medicare).
        Employer portion (7.65%) is deductible as business expense.
        
        Args:
            net_income: Net business income
            tax_year: Tax year
        
        Returns:
            dict: Self-employment tax breakdown
        """
        # 2026 estimated wage base
        SOCIAL_SECURITY_WAGE_BASE = 175000
        SE_TAX_RATE = 0.153  # 15.3% total (12.4% SS + 2.9% Medicare)
        EMPLOYER_PORTION_RATE = 0.0765  # 7.65% (deductible)
        
        # SE tax is calculated on 92.35% of net income (after deduction)
        se_taxable_income = net_income * 0.9235
        
        # Social Security portion (capped at wage base)
        ss_taxable = min(se_taxable_income, SOCIAL_SECURITY_WAGE_BASE)
        social_security_se_tax = ss_taxable * 0.124  # 12.4%
        
        # Medicare portion (on all SE taxable income)
        medicare_se_tax = se_taxable_income * 0.029  # 2.9%
        
        # Total SE tax
        total_se_tax = social_security_se_tax + medicare_se_tax
        
        # Employer portion deduction (7.65% of SE taxable income, up to wage base)
        employer_portion_deduction = min(se_taxable_income, SOCIAL_SECURITY_WAGE_BASE) * EMPLOYER_PORTION_RATE
        
        # Net SE tax after deduction
        net_se_tax = total_se_tax - employer_portion_deduction
        
        return {
            'gross_se_tax': round(total_se_tax, 2),
            'employer_portion_deduction': round(employer_portion_deduction, 2),
            'net_se_tax': round(net_se_tax, 2),
            'social_security_se_tax': round(social_security_se_tax, 2),
            'medicare_se_tax': round(medicare_se_tax, 2)
        }
    
    @staticmethod
    def calculate_child_tax_credit(num_children, tax_year=2026):
        """
        Calculate Child Tax Credit amount.
        
        Args:
            num_children: Number of qualifying children (ages 17 and under)
            tax_year: Tax year
        
        Returns:
            float: Total Child Tax Credit amount ($2,200 per child for 2026)
        """
        if tax_year == 2026:
            credit_per_child = 2200.0
        else:
            # Default to 2026 rate for other years
            credit_per_child = 2200.0
        
        total_credit = num_children * credit_per_child
        return round(total_credit, 2)
    
    @staticmethod
    def get_qbi_income_thresholds(filing_status='single', tax_year=2026):
        """
        Get QBI income thresholds for a given filing status and year.
        Below these thresholds, full 20% QBI deduction is generally allowed.
        Above these thresholds, deduction may be limited by W-2 wages and business property.
        
        Args:
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            float: Income threshold amount
        """
        if tax_year == 2026:
            # 2026 QBI Income Thresholds (estimated with inflation adjustment from 2025)
            thresholds = {
                'single': 197300.0,
                'married_joint': 394600.0,
                'married_separate': 197300.0,  # Same as single
                'head_of_household': 197300.0,  # Same as single (estimated)
                'qualifying_surviving_spouse': 394600.0  # Same as married joint
            }
        else:
            # Default to 2026 thresholds for other years
            return TaxCalculator.get_qbi_income_thresholds(filing_status, 2026)
        
        return thresholds.get(filing_status, thresholds['single'])
    
    @staticmethod
    def calculate_qbi_deduction(qbi_amount, taxable_income_before_qbi, filing_status='single', tax_year=2026):
        """
        Calculate Qualified Business Income (QBI) deduction under Section 199A.
        
        Args:
            qbi_amount: Qualified business income amount
            taxable_income_before_qbi: Taxable income before QBI deduction (gross income - standard deduction)
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            dict: {
                'qbi_amount': QBI amount,
                'deduction_amount': QBI deduction amount,
                'deduction_rate': 0.20 (20%)
            }
        """
        if qbi_amount <= 0:
            return {
                'qbi_amount': 0.0,
                'deduction_amount': 0.0,
                'deduction_rate': 0.20
            }
        
        # Base deduction is 20% of QBI
        base_deduction = qbi_amount * 0.20
        
        # Get income threshold
        income_threshold = TaxCalculator.get_qbi_income_thresholds(filing_status, tax_year)
        
        # Overall limit: Cannot exceed 20% of taxable income before QBI deduction and net capital gains
        # For simplicity, we'll use taxable income before QBI as the limit
        overall_limit = taxable_income_before_qbi * 0.20
        
        # Apply overall limit
        deduction = min(base_deduction, overall_limit)
        
        # Apply minimum deduction: $400 if QBI >= $1,000 (2026 change)
        if tax_year == 2026 and qbi_amount >= 1000.0:
            deduction = max(deduction, 400.0)
        
        # Note: Above income thresholds, deduction may be limited by W-2 wages and business property
        # For simplicity, we'll apply the full deduction below thresholds and use overall limit above
        # In a full implementation, would need W-2 wages and business property values
        
        return {
            'qbi_amount': round(qbi_amount, 2),
            'deduction_amount': round(deduction, 2),
            'deduction_rate': 0.20
        }
    
    @staticmethod
    def get_long_term_capital_gains_brackets(filing_status='single', tax_year=2026):
        """
        Get long-term capital gains tax brackets for a given filing status and year.
        
        Args:
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            list: List of dicts with bracket information: {'threshold': amount, 'rate': rate}
        """
        if tax_year == 2026:
            # 2026 Long-Term Capital Gains Brackets (estimated with inflation adjustment from 2025)
            # Thresholds are based on taxable income (ordinary income + capital gains)
            # Each bracket entry: threshold is the start, rate applies to income from this threshold to next threshold
            brackets = {
                'single': [
                    {'threshold': 0, 'rate': 0.0},  # 0% from 0 to 48350
                    {'threshold': 48350, 'rate': 0.15},  # 15% from 48350 to 533400
                    {'threshold': 533400, 'rate': 0.20},  # 20% above 533400
                    {'threshold': float('inf'), 'rate': 0.20}  # 20% rate (top bracket)
                ],
                'married_joint': [
                    {'threshold': 0, 'rate': 0.0},  # 0% from 0 to 96700
                    {'threshold': 96700, 'rate': 0.15},  # 15% from 96700 to 600050
                    {'threshold': 600050, 'rate': 0.20},  # 20% above 600050
                    {'threshold': float('inf'), 'rate': 0.20}  # 20% rate (top bracket)
                ],
                'married_separate': [
                    {'threshold': 0, 'rate': 0.0},  # 0% from 0 to 48350
                    {'threshold': 48350, 'rate': 0.15},  # 15% from 48350 to 300025
                    {'threshold': 300025, 'rate': 0.20},  # 20% above 300025
                    {'threshold': float('inf'), 'rate': 0.20}  # 20% rate (top bracket)
                ],
                'head_of_household': [
                    {'threshold': 0, 'rate': 0.0},  # 0% from 0 to 51600
                    {'threshold': 51600, 'rate': 0.15},  # 15% from 51600 to 533400
                    {'threshold': 533400, 'rate': 0.20},  # 20% above 533400
                    {'threshold': float('inf'), 'rate': 0.20}  # 20% rate (top bracket)
                ],
                'qualifying_surviving_spouse': [
                    {'threshold': 0, 'rate': 0.0},  # 0% from 0 to 96700
                    {'threshold': 96700, 'rate': 0.15},  # 15% from 96700 to 600050
                    {'threshold': 600050, 'rate': 0.20},  # 20% above 600050
                    {'threshold': float('inf'), 'rate': 0.20}  # 20% rate (top bracket)
                ]
            }
        else:
            # Default to 2026 brackets for other years
            return TaxCalculator.get_long_term_capital_gains_brackets(filing_status, 2026)
        
        return brackets.get(filing_status, brackets['single'])
    
    @staticmethod
    def calculate_long_term_capital_gains_tax(capital_gains_amount, ordinary_income_taxable, filing_status='single', tax_year=2026):
        """
        Calculate long-term capital gains tax.
        
        Capital gains are "stacked" on top of ordinary income. The rate applied depends on
        where the total taxable income (ordinary income + capital gains) falls in the brackets.
        
        Args:
            capital_gains_amount: Amount of capital gains to tax
            ordinary_income_taxable: Taxable ordinary income (before capital gains)
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            dict: {
                'total_tax': total capital gains tax,
                'rate_applied': highest rate applied,
                'breakdown': list of bracket breakdowns
            }
        """
        if capital_gains_amount <= 0:
            return {
                'total_tax': 0.0,
                'rate_applied': 0.0,
                'breakdown': []
            }
        
        brackets = TaxCalculator.get_long_term_capital_gains_brackets(filing_status, tax_year)
        
        # Sort brackets by threshold
        sorted_brackets = sorted(brackets, key=lambda x: x['threshold'])
        
        total_tax = 0.0
        breakdown = []
        remaining_capital_gains = capital_gains_amount
        highest_rate = 0.0
        
        # Calculate total taxable income
        total_taxable_income = ordinary_income_taxable + capital_gains_amount
        
        # Process capital gains through brackets
        # Capital gains are taxed starting from where ordinary income ends
        for i in range(len(sorted_brackets) - 1):
            bracket_threshold = sorted_brackets[i]['threshold']
            next_threshold = sorted_brackets[i + 1]['threshold']
            bracket_rate = sorted_brackets[i]['rate']
            
            # Calculate how much of capital gains falls in this bracket
            # The bracket applies to income from bracket_threshold to next_threshold
            bracket_start = max(bracket_threshold, ordinary_income_taxable)
            bracket_end = min(next_threshold, total_taxable_income)
            
            if bracket_end > bracket_start and remaining_capital_gains > 0:
                # Amount of capital gains in this bracket
                capital_gains_in_bracket = min(remaining_capital_gains, bracket_end - bracket_start)
                tax_in_bracket = capital_gains_in_bracket * bracket_rate
                
                if capital_gains_in_bracket > 0:
                    breakdown.append({
                        'threshold_min': bracket_start,
                        'threshold_max': bracket_end if next_threshold != float('inf') else None,
                        'rate': bracket_rate,
                        'taxable_amount': capital_gains_in_bracket,
                        'tax': tax_in_bracket
                    })
                    
                    total_tax += tax_in_bracket
                    remaining_capital_gains -= capital_gains_in_bracket
                    highest_rate = max(highest_rate, bracket_rate)
        
        # Handle any remaining capital gains at the highest bracket (20%)
        if remaining_capital_gains > 0 and len(sorted_brackets) > 0:
            highest_bracket = sorted_brackets[-1]
            highest_rate_value = highest_bracket['rate']
            tax_on_remaining = remaining_capital_gains * highest_rate_value
            
            prev_threshold = sorted_brackets[-2]['threshold'] if len(sorted_brackets) > 1 else 0
            breakdown.append({
                'threshold_min': max(prev_threshold, ordinary_income_taxable),
                'threshold_max': None,
                'rate': highest_rate_value,
                'taxable_amount': remaining_capital_gains,
                'tax': tax_on_remaining
            })
            
            total_tax += tax_on_remaining
            highest_rate = max(highest_rate, highest_rate_value)
        
        # Convert infinity to None for JSON serialization
        for item in breakdown:
            if item.get('threshold_max') == float('inf'):
                item['threshold_max'] = None
        
        return {
            'total_tax': round(total_tax, 2),
            'rate_applied': highest_rate,
            'breakdown': breakdown
        }
    
    @staticmethod
    def calculate_federal_tax(income, filing_status='single', dependents=0, tax_year=2026, 
                              income_source='w2', salary=0, distributions=0):
        """
        Calculate federal tax liability based on income source.
        
        Args:
            income: Annual gross income (for W2/LLC)
            filing_status: Filing status
            dependents: Number of dependents
            tax_year: Tax year
            income_source: 'w2', 'llc', 'llc_s_corp', 's_corp'
            salary: Salary amount (for S-Corp types)
            distributions: Distributions amount (for S-Corp types)
        
        Returns:
            dict: Detailed tax calculation results
        """
        # Get standard deduction
        standard_deduction = TaxCalculator.get_standard_deduction(
            filing_status, 'federal', None, tax_year
        )
        
        # Calculate Child Tax Credit
        child_tax_credit = TaxCalculator.calculate_child_tax_credit(dependents, tax_year)
        
        # Route to appropriate calculation based on income source
        if income_source == 'w2':
            # Standard W2 employee - no FICA/SE taxes
            taxable_income = TaxCalculator.calculate_taxable_income(
                income, standard_deduction
            )
            
            brackets = TaxCalculator.get_tax_brackets(
                'federal', None, filing_status, tax_year
            )
            
            tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)
            
            # Apply Child Tax Credit (non-refundable, cannot go below $0)
            income_tax_before_credit = tax_result['total_tax']
            income_tax_after_credit = max(0.0, income_tax_before_credit - child_tax_credit)
            credit_applied = min(child_tax_credit, income_tax_before_credit)
            
            total_tax = income_tax_after_credit
            effective_rate = (total_tax / income * 100) if income > 0 else 0.0
            
            return {
                'gross_income': income,
                'standard_deduction': standard_deduction,
                'taxable_income': taxable_income,
                'income_tax_before_credit': income_tax_before_credit,
                'income_tax_after_credit': round(income_tax_after_credit, 2),
                'child_tax_credit': child_tax_credit,
                'child_tax_credit_applied': round(credit_applied, 2),
                'income_tax': round(income_tax_after_credit, 2),
                'fica_tax': 0.0,
                'se_tax': 0.0,
                'total_tax': round(total_tax, 2),
                'effective_tax_rate': round(effective_rate, 2),
                'marginal_tax_rate': round(tax_result['marginal_rate'] * 100, 2),
                'bracket_breakdown': tax_result['bracket_breakdown'],
                'income_source': income_source
            }
        
        elif income_source == 'llc':
            # LLC - QBI deduction + self-employment tax + income tax
            # For LLC, entire income is QBI
            qbi_amount = income
            
            # Calculate taxable income before QBI (for QBI deduction calculation)
            taxable_income_before_qbi = TaxCalculator.calculate_taxable_income(
                income, standard_deduction
            )
            
            # Calculate QBI deduction
            qbi_result = TaxCalculator.calculate_qbi_deduction(
                qbi_amount, taxable_income_before_qbi, filing_status, tax_year
            )
            qbi_deduction = qbi_result['deduction_amount']
            
            # Calculate taxable income after QBI deduction
            taxable_income = TaxCalculator.calculate_taxable_income(
                income, standard_deduction, qbi_deduction
            )
            
            brackets = TaxCalculator.get_tax_brackets(
                'federal', None, filing_status, tax_year
            )
            
            # Calculate income tax on reduced taxable income
            tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)
            
            # Apply Child Tax Credit (non-refundable, cannot go below $0)
            income_tax_before_credit = tax_result['total_tax']
            income_tax_after_credit = max(0.0, income_tax_before_credit - child_tax_credit)
            credit_applied = min(child_tax_credit, income_tax_before_credit)
            
            # Calculate self-employment tax
            se_tax_result = TaxCalculator.calculate_self_employment_tax(income, tax_year)
            
            total_tax = income_tax_after_credit + se_tax_result['net_se_tax']
            effective_rate = (total_tax / income * 100) if income > 0 else 0.0
            
            return {
                'gross_income': income,
                'standard_deduction': standard_deduction,
                'qbi_amount': qbi_result['qbi_amount'],
                'qbi_deduction': qbi_deduction,
                'taxable_income_before_qbi': taxable_income_before_qbi,
                'taxable_income': taxable_income,
                'income_tax_before_credit': income_tax_before_credit,
                'income_tax_after_credit': round(income_tax_after_credit, 2),
                'child_tax_credit': child_tax_credit,
                'child_tax_credit_applied': round(credit_applied, 2),
                'income_tax': round(income_tax_after_credit, 2),
                'fica_tax': 0.0,
                'se_tax': se_tax_result['net_se_tax'],
                'se_tax_breakdown': se_tax_result,
                'total_tax': round(total_tax, 2),
                'effective_tax_rate': round(effective_rate, 2),
                'marginal_tax_rate': round(tax_result['marginal_rate'] * 100, 2),
                'bracket_breakdown': tax_result['bracket_breakdown'],
                'income_source': income_source
            }
        
        elif income_source in ['llc_s_corp', 's_corp']:
            # S-Corp types - Salary taxed as ordinary income, distributions taxed as capital gains
            # QBI = distributions only (salary is wage income, not QBI)
            total_income = salary + distributions
            
            # Calculate taxable income for salary (ordinary income) before QBI
            # Standard deduction applies to total income, but we allocate it to salary first
            salary_taxable_before_qbi = TaxCalculator.calculate_taxable_income(
                salary, standard_deduction
            )
            
            # Calculate QBI deduction (only on distributions)
            qbi_amount = distributions
            # For QBI deduction calculation, use total taxable income before QBI
            total_taxable_before_qbi = salary_taxable_before_qbi + distributions
            
            qbi_result = TaxCalculator.calculate_qbi_deduction(
                qbi_amount, total_taxable_before_qbi, filing_status, tax_year
            )
            qbi_deduction = qbi_result['deduction_amount']
            
            # Apply QBI deduction to reduce salary taxable income (ordinary income)
            # QBI deduction reduces taxable income for ordinary income tax calculation
            salary_taxable = max(0.0, salary_taxable_before_qbi - qbi_deduction)
            
            # If standard deduction exceeds salary, remaining deduction applies to distributions
            remaining_deduction = max(0.0, standard_deduction - salary)
            distributions_taxable = max(0.0, distributions - remaining_deduction)
            
            # Calculate total taxable income for capital gains calculation
            total_taxable_income = salary_taxable + distributions_taxable
            
            # Calculate ordinary income tax on salary portion (after QBI deduction)
            brackets = TaxCalculator.get_tax_brackets(
                'federal', None, filing_status, tax_year
            )
            ordinary_income_tax_result = TaxCalculator.calculate_tax_by_brackets(salary_taxable, brackets)
            
            # Apply Child Tax Credit to ordinary income tax only (not capital gains)
            ordinary_income_tax_before_credit = ordinary_income_tax_result['total_tax']
            ordinary_income_tax_after_credit = max(0.0, ordinary_income_tax_before_credit - child_tax_credit)
            credit_applied = min(child_tax_credit, ordinary_income_tax_before_credit)
            
            # Calculate capital gains tax on distributions
            capital_gains_result = TaxCalculator.calculate_long_term_capital_gains_tax(
                distributions_taxable, salary_taxable, filing_status, tax_year
            )
            
            # Calculate FICA tax on salary only (distributions are not subject to FICA)
            fica_result = TaxCalculator.calculate_fica_tax(salary, filing_status, tax_year)
            
            # Total tax = ordinary income tax (after credit) + capital gains tax + FICA tax
            total_tax = ordinary_income_tax_after_credit + capital_gains_result['total_tax'] + fica_result['total_fica_tax']
            effective_rate = (total_tax / total_income * 100) if total_income > 0 else 0.0
            
            return {
                'gross_income': total_income,
                'salary': salary,
                'distributions': distributions,
                'standard_deduction': standard_deduction,
                'qbi_amount': qbi_result['qbi_amount'],
                'qbi_deduction': qbi_deduction,
                'salary_taxable_before_qbi': salary_taxable_before_qbi,
                'salary_taxable': salary_taxable,
                'distributions_taxable': distributions_taxable,
                'total_taxable_income': total_taxable_income,
                'ordinary_income_tax_before_credit': ordinary_income_tax_before_credit,
                'ordinary_income_tax_after_credit': round(ordinary_income_tax_after_credit, 2),
                'capital_gains_tax': capital_gains_result['total_tax'],
                'capital_gains_rate_applied': round(capital_gains_result['rate_applied'] * 100, 2),
                'capital_gains_breakdown': capital_gains_result['breakdown'],
                'child_tax_credit': child_tax_credit,
                'child_tax_credit_applied': round(credit_applied, 2),
                'income_tax': round(ordinary_income_tax_after_credit, 2),  # For backward compatibility
                'fica_tax': fica_result['total_fica_tax'],
                'fica_tax_breakdown': fica_result,
                'se_tax': 0.0,
                'total_tax': round(total_tax, 2),
                'effective_tax_rate': round(effective_rate, 2),
                'marginal_tax_rate': round(ordinary_income_tax_result['marginal_rate'] * 100, 2),
                'bracket_breakdown': ordinary_income_tax_result['bracket_breakdown'],
                'income_source': income_source
            }
        
        else:
            # Default to W2 calculation
            taxable_income = TaxCalculator.calculate_taxable_income(
                income, standard_deduction
            )
            
            brackets = TaxCalculator.get_tax_brackets(
                'federal', None, filing_status, tax_year
            )
            
            tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)
            
            # Apply Child Tax Credit (non-refundable, cannot go below $0)
            income_tax_before_credit = tax_result['total_tax']
            income_tax_after_credit = max(0.0, income_tax_before_credit - child_tax_credit)
            credit_applied = min(child_tax_credit, income_tax_before_credit)
            
            total_tax = income_tax_after_credit
            effective_rate = (total_tax / income * 100) if income > 0 else 0.0
            
            return {
                'gross_income': income,
                'standard_deduction': standard_deduction,
                'taxable_income': taxable_income,
                'income_tax_before_credit': income_tax_before_credit,
                'income_tax_after_credit': round(income_tax_after_credit, 2),
                'child_tax_credit': child_tax_credit,
                'child_tax_credit_applied': round(credit_applied, 2),
                'income_tax': round(income_tax_after_credit, 2),
                'fica_tax': 0.0,
                'se_tax': 0.0,
                'total_tax': round(total_tax, 2),
                'effective_tax_rate': round(effective_rate, 2),
                'marginal_tax_rate': round(tax_result['marginal_rate'] * 100, 2),
                'bracket_breakdown': tax_result['bracket_breakdown'],
                'income_source': income_source
            }
    
    @staticmethod
    def calculate_state_tax(income, filing_status='single', dependents=0, state_code=None, tax_year=2026):
        """
        Calculate state tax liability.
        Note: Child Tax Credit only applies to federal taxes, not state taxes.
        
        Args:
            income: Annual gross income
            filing_status: Filing status
            dependents: Number of dependents (not used in state tax calculation)
            state_code: 2-letter state code
            tax_year: Tax year
        
        Returns:
            dict: Detailed tax calculation results, or None if state has no income tax
        """
        if not state_code:
            return None
        
        # Check if state has income tax (simplified - would check database)
        # States with no income tax: AK, FL, NV, NH, SD, TN, TX, WA, WY
        no_income_tax_states = ['AK', 'FL', 'NV', 'NH', 'SD', 'TN', 'TX', 'WA', 'WY']
        if state_code.upper() in no_income_tax_states:
            return {
                'gross_income': income,
                'standard_deduction': 0.0,
                'taxable_income': 0.0,
                'total_tax': 0.0,
                'effective_tax_rate': 0.0,
                'marginal_tax_rate': 0.0,
                'bracket_breakdown': [],
                'no_income_tax': True
            }
        
        # Get standard deduction
        standard_deduction = TaxCalculator.get_standard_deduction(
            filing_status, 'state', state_code, tax_year
        )
        
        # Calculate taxable income (dependents not used - Child Tax Credit is federal only)
        taxable_income = TaxCalculator.calculate_taxable_income(
            income, standard_deduction
        )
        
        # Get tax brackets
        brackets = TaxCalculator.get_tax_brackets(
            'state', state_code, filing_status, tax_year
        )
        
        if not brackets:
            # No brackets found - return zero tax
            return {
                'gross_income': income,
                'standard_deduction': standard_deduction,
                'taxable_income': taxable_income,
                'total_tax': 0.0,
                'effective_tax_rate': 0.0,
                'marginal_tax_rate': 0.0,
                'bracket_breakdown': []
            }
        
        # Calculate tax
        tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)
        
        # Calculate surtax (if applicable)
        surtax_amount = TaxCalculator._calculate_state_surtax(
            state_code, taxable_income, filing_status, tax_year
        )
        
        # Total tax includes base tax + surtax
        total_tax = tax_result['total_tax'] + surtax_amount
        
        # Calculate effective tax rate
        effective_rate = (total_tax / income * 100) if income > 0 else 0.0
        
        result = {
            'gross_income': income,
            'standard_deduction': standard_deduction,
            'taxable_income': taxable_income,
            'base_tax': tax_result['total_tax'],
            'surtax': surtax_amount,
            'total_tax': round(total_tax, 2),
            'effective_tax_rate': round(effective_rate, 2),
            'marginal_tax_rate': round(tax_result['marginal_rate'] * 100, 2),
            'bracket_breakdown': tax_result['bracket_breakdown'],
            'state_code': state_code.upper()
        }
        
        return result
    
    @staticmethod
    def _calculate_state_surtax(state_code, taxable_income, filing_status='single', tax_year=2026):
        """
        Calculate state surtax for applicable states.
        
        Args:
            state_code: 2-letter state code
            taxable_income: Taxable income amount
            filing_status: Filing status
            tax_year: Tax year
        
        Returns:
            float: Surtax amount
        """
        state_code = state_code.upper()
        
        if tax_year == 2026:
            # California: 1% Behavioral Health Services Tax on taxable income over $1,000,000
            if state_code == 'CA':
                if taxable_income > 1000000:
                    surtax = (taxable_income - 1000000) * 0.01
                    return round(surtax, 2)
            
            # Massachusetts: Additional surtaxes (if any documented)
            # Note: MA surtax details would need to be added based on reference file
            
            # Other states with surtaxes can be added here as needed
        
        return 0.0