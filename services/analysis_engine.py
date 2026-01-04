from models import db, ExtractedData, AnalysisResult, Client
from services.irs_reference import IRSReferenceService
from decimal import Decimal

class AnalysisEngine:
    """Service for analyzing tax data and generating strategy recommendations"""
    
    @staticmethod
    def analyze_client(client_id):
        """
        Analyze a client's tax situation and generate recommendations
        
        Args:
            client_id: ID of the client to analyze
        
        Returns:
            tuple: (list of AnalysisResult objects, summary dict)
        """
        # Get all extracted data for the client
        extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()
        
        if not extracted_data:
            return [], AnalysisEngine._generate_empty_summary()
        
        # Organize data by form type
        data_by_form = {}
        for data in extracted_data:
            if data.form_type not in data_by_form:
                data_by_form[data.form_type] = {}
            data_by_form[data.form_type][data.field_name] = data.field_value
        
        # Get client info
        client = Client.query.get(client_id)
        
        # Generate summary
        summary = AnalysisEngine._calculate_summary(data_by_form, client)
        
        # Generate strategies
        strategies = []
        
        # Analyze income and generate strategies
        strategies.extend(AnalysisEngine._analyze_retirement_strategies(data_by_form, client))
        strategies.extend(AnalysisEngine._analyze_business_strategies(data_by_form, client))
        strategies.extend(AnalysisEngine._analyze_deduction_strategies(data_by_form, client))
        strategies.extend(AnalysisEngine._analyze_investment_strategies(data_by_form, client))
        strategies.extend(AnalysisEngine._analyze_education_strategies(data_by_form, client))
        
        # Store strategies in database
        for strategy in strategies:
            db.session.add(strategy)
        
        db.session.commit()
        
        return strategies, summary
    
    @staticmethod
    def _generate_empty_summary():
        """Generate an empty summary when no data is available"""
        return {
            'total_income': 0,
            'adjusted_gross_income': 0,
            'taxable_income': 0,
            'total_tax': 0,
            'tax_withheld': 0,
            'tax_owed': 0,
            'tax_refund': 0,
            'effective_tax_rate': 0,
            'marginal_tax_rate': 0,
            'income_sources': []
        }
    
    @staticmethod
    def _calculate_summary(data_by_form, client):
        """Calculate tax summary from extracted data"""
        # Get income values
        wages_1040 = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'wages', 0)
        wages_w2 = AnalysisEngine._get_numeric_value(data_by_form, 'W-2', 'wages', 0)
        total_wages = wages_1040 + wages_w2
        
        # Get other income sources
        interest_income = AnalysisEngine._get_numeric_value(data_by_form, '1099-INT', 'income', 0)
        dividend_income = AnalysisEngine._get_numeric_value(data_by_form, '1099-DIV', 'income', 0)
        business_income = AnalysisEngine._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
        misc_income = AnalysisEngine._get_numeric_value(data_by_form, '1099-MISC', 'income', 0)
        nec_income = AnalysisEngine._get_numeric_value(data_by_form, '1099-NEC', 'income', 0)
        
        # Build income breakdown
        income_sources = []
        if total_wages > 0:
            income_sources.append({'source': 'Wages, Salaries, Tips', 'amount': round(total_wages, 2)})
        if interest_income > 0:
            income_sources.append({'source': 'Interest Income', 'amount': round(interest_income, 2)})
        if dividend_income > 0:
            income_sources.append({'source': 'Dividend Income', 'amount': round(dividend_income, 2)})
        if business_income > 0:
            income_sources.append({'source': 'Business Income (Schedule C)', 'amount': round(business_income, 2)})
        if misc_income > 0:
            income_sources.append({'source': 'Miscellaneous Income', 'amount': round(misc_income, 2)})
        if nec_income > 0:
            income_sources.append({'source': 'Nonemployee Compensation', 'amount': round(nec_income, 2)})
        
        # Calculate total from sources
        total_from_sources = sum(source['amount'] for source in income_sources)
        
        # Get AGI
        agi = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'agi', total_from_sources)
        
        # If AGI is higher than sum of sources, add "Other Income" category
        if agi > total_from_sources and total_from_sources > 0:
            other_income = agi - total_from_sources
            income_sources.append({'source': 'Other Income', 'amount': round(other_income, 2)})
        elif agi > 0 and total_from_sources == 0:
            # If we have AGI but no specific sources, show it as "Total Income"
            income_sources.append({'source': 'Total Income (from AGI)', 'amount': round(agi, 2)})
        
        # Get taxable income
        taxable_income = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'taxable_income', agi)
        
        # Get tax amounts
        total_tax = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'total_tax', 0)
        federal_tax_withheld = AnalysisEngine._get_numeric_value(data_by_form, 'W-2', 'federal_tax_withheld', 0)
        
        # Calculate effective tax rate
        effective_tax_rate = (total_tax / agi * 100) if agi > 0 else 0
        
        # Estimate marginal tax rate based on taxable income (2024 brackets)
        marginal_tax_rate = AnalysisEngine._estimate_marginal_rate(taxable_income)
        
        # Calculate tax owed or refund
        tax_owed = max(0, total_tax - federal_tax_withheld)
        tax_refund = max(0, federal_tax_withheld - total_tax)
        
        # Calculate total income (use AGI as proxy if available, otherwise sum of sources)
        total_income = agi if agi > 0 else total_from_sources
        
        return {
            'total_income': round(total_income, 2),
            'adjusted_gross_income': round(agi, 2),
            'taxable_income': round(taxable_income, 2),
            'total_tax': round(total_tax, 2),
            'tax_withheld': round(federal_tax_withheld, 2),
            'tax_owed': round(tax_owed, 2),
            'tax_refund': round(tax_refund, 2),
            'effective_tax_rate': round(effective_tax_rate, 2),
            'marginal_tax_rate': marginal_tax_rate,
            'income_sources': income_sources
        }
    
    @staticmethod
    def _estimate_marginal_rate(taxable_income):
        """Estimate marginal tax rate based on 2024 tax brackets"""
        if taxable_income <= 0:
            return 0
        elif taxable_income <= 11600:  # 10% bracket
            return 10
        elif taxable_income <= 47150:  # 12% bracket
            return 12
        elif taxable_income <= 100525:  # 22% bracket
            return 22
        elif taxable_income <= 191950:  # 24% bracket
            return 24
        elif taxable_income <= 243725:  # 32% bracket
            return 32
        elif taxable_income <= 609350:  # 35% bracket
            return 35
        else:  # 37% bracket
            return 37
    
    @staticmethod
    def _get_numeric_value(data_dict, form_type, field_name, default=0):
        """Helper to get numeric value from extracted data"""
        try:
            if form_type in data_dict and field_name in data_dict[form_type]:
                value = data_dict[form_type][field_name]
                if value:
                    return float(value)
        except:
            pass
        return default
    
    @staticmethod
    def _analyze_retirement_strategies(data_by_form, client):
        """Analyze retirement contribution opportunities"""
        strategies = []
        
        # Get income
        wages = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'wages', 0)
        wages += AnalysisEngine._get_numeric_value(data_by_form, 'W-2', 'wages', 0)
        agi = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'agi', wages)
        
        if agi > 0:
            # 401(k) contribution strategy
            if wages > 0:
                max_401k = min(23000, wages * 0.20)  # 2024 limit
                if max_401k > 0:
                    potential_savings = max_401k * 0.22  # Assume 22% bracket
                    irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 401(k)')
                    strategies.append(AnalysisResult(
                        client_id=client.id,
                        strategy_name='Maximize 401(k) Contributions',
                        strategy_description=f'Contribute up to ${max_401k:,.0f} to your 401(k) plan to reduce taxable income.',
                        potential_savings=potential_savings,
                        irs_section=irs_ref.section if irs_ref else 'IRC Section 401(k)',
                        irs_code='IRC Section 401(k)',
                        irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/retirement-plans/401k-plans',
                        priority=1
                    ))
            
            # Traditional IRA strategy
            if agi < 83000:  # Below phase-out for 2024
                max_ira = 7000  # 2024 limit
                potential_savings = max_ira * 0.22
                irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 408')
                strategies.append(AnalysisResult(
                    client_id=client.id,
                    strategy_name='Traditional IRA Contribution',
                    strategy_description=f'Contribute up to ${max_ira:,} to a traditional IRA for tax-deductible contributions.',
                    potential_savings=potential_savings,
                    irs_section=irs_ref.section if irs_ref else 'IRC Section 408',
                    irs_code='IRC Section 408',
                    irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/retirement-plans/individual-retirement-arrangements-iras',
                    priority=2
                ))
            
            # HSA strategy
            if agi < 83000:  # Simplified check
                max_hsa = 4150  # 2024 individual limit
                potential_savings = max_hsa * 0.22
                irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 223')
                strategies.append(AnalysisResult(
                    client_id=client.id,
                    strategy_name='Health Savings Account (HSA)',
                    strategy_description=f'Contribute up to ${max_hsa:,} to an HSA if you have a high-deductible health plan.',
                    potential_savings=potential_savings,
                    irs_section=irs_ref.section if irs_ref else 'IRC Section 223',
                    irs_code='IRC Section 223',
                    irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/publications/p969',
                    priority=2
                ))
        
        return strategies
    
    @staticmethod
    def _analyze_business_strategies(data_by_form, client):
        """Analyze business deduction opportunities"""
        strategies = []
        
        # Check for Schedule C
        if 'Schedule C' in data_by_form:
            gross_receipts = AnalysisEngine._get_numeric_value(data_by_form, 'Schedule C', 'gross_receipts', 0)
            net_profit = AnalysisEngine._get_numeric_value(data_by_form, 'Schedule C', 'net_profit', 0)
            
            if gross_receipts > 0:
                # Section 179 deduction
                irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 179')
                strategies.append(AnalysisResult(
                    client_id=client.id,
                    strategy_name='Section 179 Equipment Deduction',
                    strategy_description='Consider Section 179 deduction for qualifying business equipment purchases up to $1,160,000.',
                    potential_savings=gross_receipts * 0.20 * 0.22,  # Rough estimate
                    irs_section=irs_ref.section if irs_ref else 'IRC Section 179',
                    irs_code='IRC Section 179',
                    irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/publications/p946',
                    priority=1
                ))
                
                # QBI deduction
                if net_profit > 0:
                    qbi_deduction = net_profit * 0.20
                    potential_savings = qbi_deduction * 0.22
                    irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 199A')
                    strategies.append(AnalysisResult(
                        client_id=client.id,
                        strategy_name='Qualified Business Income Deduction',
                        strategy_description=f'You may be eligible for a 20% deduction on qualified business income, potentially saving ${potential_savings:,.0f}.',
                        potential_savings=potential_savings,
                        irs_section=irs_ref.section if irs_ref else 'IRC Section 199A',
                        irs_code='IRC Section 199A',
                        irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/newsroom/tax-cuts-and-jobs-act-provision-11011-section-199a-qualified-business-income-deduction',
                        priority=1
                    ))
        
        return strategies
    
    @staticmethod
    def _analyze_deduction_strategies(data_by_form, client):
        """Analyze deduction opportunities"""
        strategies = []
        
        agi = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'agi', 0)
        
        # Charitable contributions
        charity = AnalysisEngine._get_numeric_value(data_by_form, 'Schedule A', 'charitable_contributions', 0)
        if charity == 0 and agi > 50000:
            irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 170')
            strategies.append(AnalysisResult(
                client_id=client.id,
                strategy_name='Charitable Contribution Deduction',
                strategy_description='Consider making charitable contributions to qualified organizations for tax deductions.',
                potential_savings=5000 * 0.22,  # Example
                irs_section=irs_ref.section if irs_ref else 'IRC Section 170',
                irs_code='IRC Section 170',
                irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/charities-non-profits/charitable-organizations',
                priority=3
            ))
        
        return strategies
    
    @staticmethod
    def _analyze_investment_strategies(data_by_form, client):
        """Analyze investment-related strategies"""
        strategies = []
        
        # Tax-loss harvesting
        if 'Schedule D' in data_by_form or '1099-DIV' in data_by_form:
            irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 1211')
            strategies.append(AnalysisResult(
                client_id=client.id,
                strategy_name='Tax-Loss Harvesting',
                strategy_description='Consider selling losing investments to offset capital gains and reduce tax liability.',
                potential_savings=3000 * 0.22,  # Up to $3k deduction
                irs_section=irs_ref.section if irs_ref else 'IRC Section 1211',
                irs_code='IRC Section 1211',
                irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/publications/p544',
                priority=3
            ))
        
        return strategies
    
    @staticmethod
    def _analyze_education_strategies(data_by_form, client):
        """Analyze education-related strategies"""
        strategies = []
        
        agi = AnalysisEngine._get_numeric_value(data_by_form, '1040', 'agi', 0)
        
        # Education credits
        if agi < 90000:  # Phase-out range
            irs_ref = IRSReferenceService.get_reference_by_section('IRC Section 25A')
            strategies.append(AnalysisResult(
                client_id=client.id,
                strategy_name='Education Credits',
                strategy_description='Consider education credits (AOTC or LLC) for qualified education expenses.',
                potential_savings=2500,  # AOTC max
                irs_section=irs_ref.section if irs_ref else 'IRC Section 25A',
                irs_code='IRC Section 25A',
                irs_url=irs_ref.url if irs_ref else 'https://www.irs.gov/credits-deductions/individuals/education-credits-aotc-llc',
                priority=4
            ))
        
        return strategies

