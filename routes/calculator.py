from flask import Blueprint, request, jsonify
from services.tax_calculator import TaxCalculator
from models import TaxBracket, StandardDeduction

calculator_bp = Blueprint('calculator', __name__)

# US States list
US_STATES = [
    {'code': 'AL', 'name': 'Alabama'}, {'code': 'AK', 'name': 'Alaska'}, {'code': 'AZ', 'name': 'Arizona'},
    {'code': 'AR', 'name': 'Arkansas'}, {'code': 'CA', 'name': 'California'}, {'code': 'CO', 'name': 'Colorado'},
    {'code': 'CT', 'name': 'Connecticut'}, {'code': 'DE', 'name': 'Delaware'}, {'code': 'FL', 'name': 'Florida'},
    {'code': 'GA', 'name': 'Georgia'}, {'code': 'HI', 'name': 'Hawaii'}, {'code': 'ID', 'name': 'Idaho'},
    {'code': 'IL', 'name': 'Illinois'}, {'code': 'IN', 'name': 'Indiana'}, {'code': 'IA', 'name': 'Iowa'},
    {'code': 'KS', 'name': 'Kansas'}, {'code': 'KY', 'name': 'Kentucky'}, {'code': 'LA', 'name': 'Louisiana'},
    {'code': 'ME', 'name': 'Maine'}, {'code': 'MD', 'name': 'Maryland'}, {'code': 'MA', 'name': 'Massachusetts'},
    {'code': 'MI', 'name': 'Michigan'}, {'code': 'MN', 'name': 'Minnesota'}, {'code': 'MS', 'name': 'Mississippi'},
    {'code': 'MO', 'name': 'Missouri'}, {'code': 'MT', 'name': 'Montana'}, {'code': 'NE', 'name': 'Nebraska'},
    {'code': 'NV', 'name': 'Nevada'}, {'code': 'NH', 'name': 'New Hampshire'}, {'code': 'NJ', 'name': 'New Jersey'},
    {'code': 'NM', 'name': 'New Mexico'}, {'code': 'NY', 'name': 'New York'}, {'code': 'NC', 'name': 'North Carolina'},
    {'code': 'ND', 'name': 'North Dakota'}, {'code': 'OH', 'name': 'Ohio'}, {'code': 'OK', 'name': 'Oklahoma'},
    {'code': 'OR', 'name': 'Oregon'}, {'code': 'PA', 'name': 'Pennsylvania'}, {'code': 'RI', 'name': 'Rhode Island'},
    {'code': 'SC', 'name': 'South Carolina'}, {'code': 'SD', 'name': 'South Dakota'}, {'code': 'TN', 'name': 'Tennessee'},
    {'code': 'TX', 'name': 'Texas'}, {'code': 'UT', 'name': 'Utah'}, {'code': 'VT', 'name': 'Vermont'},
    {'code': 'VA', 'name': 'Virginia'}, {'code': 'WA', 'name': 'Washington'}, {'code': 'WV', 'name': 'West Virginia'},
    {'code': 'WI', 'name': 'Wisconsin'}, {'code': 'WY', 'name': 'Wyoming'}, {'code': 'DC', 'name': 'District of Columbia'}
]

@calculator_bp.route('/calculator/states', methods=['GET'])
def get_states():
    """Get list of US states"""
    return jsonify(US_STATES)

@calculator_bp.route('/calculator/tax-brackets', methods=['GET'])
def get_tax_brackets():
    """Get tax brackets for a given year/state/filing status"""
    tax_type = request.args.get('tax_type', 'federal')  # 'federal' or 'state'
    state_code = request.args.get('state_code', None)
    filing_status = request.args.get('filing_status', 'single')
    tax_year = int(request.args.get('tax_year', 2026))
    
    brackets = TaxCalculator.get_tax_brackets(tax_type, state_code, filing_status, tax_year)
    return jsonify([b.to_dict() for b in brackets])

@calculator_bp.route('/calculator/standard-deductions', methods=['GET'])
def get_standard_deductions():
    """Get standard deductions for a given year/state/filing status"""
    tax_type = request.args.get('tax_type', 'federal')
    state_code = request.args.get('state_code', None)
    filing_status = request.args.get('filing_status', 'single')
    tax_year = int(request.args.get('tax_year', 2026))
    
    deduction = TaxCalculator.get_standard_deduction(filing_status, tax_type, state_code, tax_year)
    return jsonify({'deduction_amount': deduction})

@calculator_bp.route('/calculator/calculate', methods=['POST'])
def calculate_tax():
    """Calculate tax liability"""
    try:
        data = request.get_json()
        
        # Extract parameters
        income = float(data.get('income', 0))
        income_frequency = data.get('income_frequency', 'annual')
        income_source = data.get('income_source', 'w2')
        salary = float(data.get('salary', 0))
        distributions = float(data.get('distributions', 0))
        filing_status = data.get('filing_status', 'single')
        dependents = int(data.get('dependents', 0))  # Number of qualifying children (ages 17 and under) for Child Tax Credit
        state_code = data.get('state_code', None)
        multiple_states = data.get('multiple_states', False)
        selected_states = data.get('selected_states', [])  # List of state codes if multiple_states is True
        tax_year = int(data.get('tax_year', 2026))
        
        # Validate S-Corp types require salary and distributions
        if income_source in ['llc_s_corp', 's_corp']:
            if not salary or salary <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Salary is required for S-Corp income sources'
                }), 400
            if distributions < 0:
                return jsonify({
                    'success': False,
                    'error': 'Distributions must be 0 or greater'
                }), 400
        
        # Convert income to annual
        annual_income = TaxCalculator.convert_income_to_annual(income, income_frequency)
        
        # For S-Corp types, use salary + distributions as total income
        if income_source in ['llc_s_corp', 's_corp']:
            annual_income = salary + distributions
        
        # Calculate federal tax
        federal_result = TaxCalculator.calculate_federal_tax(
            annual_income, filing_status, dependents, tax_year,
            income_source=income_source, salary=salary, distributions=distributions
        )
        
        # Use gross_income from federal result for state tax calculation (handles S-Corp correctly)
        income_for_state_tax = federal_result.get('gross_income', annual_income)
        
        # Calculate state tax(es)
        state_results = []
        total_state_tax = 0.0
        
        if multiple_states and selected_states:
            # Calculate for multiple selected states
            for state in selected_states:
                state_result = TaxCalculator.calculate_state_tax(
                    income_for_state_tax, filing_status, dependents, state, tax_year
                )
                if state_result:
                    state_results.append(state_result)
                    total_state_tax += state_result['total_tax']
        elif state_code:
            # Calculate for single state
            state_result = TaxCalculator.calculate_state_tax(
                income_for_state_tax, filing_status, dependents, state_code, tax_year
            )
            if state_result:
                state_results.append(state_result)
                total_state_tax = state_result['total_tax']
        
        # Calculate totals
        # Use gross_income from federal result (which may be salary + distributions for S-Corp)
        total_income_for_rate = federal_result.get('gross_income', annual_income)
        total_tax = federal_result['total_tax'] + total_state_tax
        total_effective_rate = (total_tax / total_income_for_rate * 100) if total_income_for_rate > 0 else 0.0
        
        return jsonify({
            'success': True,
            'annual_income': total_income_for_rate,
            'federal': federal_result,
            'state': state_results,
            'totals': {
                'federal_tax': federal_result['total_tax'],
                'state_tax': total_state_tax,
                'total_tax': round(total_tax, 2),
                'effective_tax_rate': round(total_effective_rate, 2),
                'marginal_tax_rate': max(
                    federal_result['marginal_tax_rate'],
                    max([s['marginal_tax_rate'] for s in state_results] + [0])
                )
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def _get_annual_income(spouse_data):
    """Convert spouse data to annual income, handling S-Corp types."""
    income = float(spouse_data.get('income', 0))
    income_frequency = spouse_data.get('income_frequency', 'annual')
    income_source = spouse_data.get('income_source', 'w2')
    salary = float(spouse_data.get('salary', 0))
    distributions = float(spouse_data.get('distributions', 0))

    if income_source in ['llc_s_corp', 's_corp']:
        return salary + distributions
    return TaxCalculator.convert_income_to_annual(income, income_frequency)


def _get_qbi_eligible_income(spouse_data, annual_income):
    """Get QBI-eligible income: LLC=full, S-Corp types=distributions, W2=0."""
    source = spouse_data.get('income_source', 'w2')
    if source == 'llc':
        return annual_income
    elif source in ['llc_s_corp', 's_corp']:
        return float(spouse_data.get('distributions', 0))
    return 0.0


def _calculate_spouse_payroll_tax(spouse_data, annual_income, filing_status, tax_year):
    """Calculate FICA or SE tax for one spouse based on income source."""
    source = spouse_data.get('income_source', 'w2')
    salary = float(spouse_data.get('salary', 0))

    if source == 'w2':
        return {'fica_tax': 0.0, 'se_tax': 0.0, 'total': 0.0}
    elif source == 'llc':
        se = TaxCalculator.calculate_self_employment_tax(annual_income, tax_year)
        return {'fica_tax': 0.0, 'se_tax': se['net_se_tax'], 'total': se['net_se_tax']}
    elif source in ['llc_s_corp', 's_corp']:
        fica = TaxCalculator.calculate_fica_tax(salary, filing_status, tax_year)
        return {'fica_tax': fica['total_fica_tax'], 'se_tax': 0.0, 'total': fica['total_fica_tax']}
    return {'fica_tax': 0.0, 'se_tax': 0.0, 'total': 0.0}


def _calculate_spouse_individual(spouse_data, filing_status, dependents, tax_year):
    """Calculate one spouse's full tax for MFS scenario."""
    annual_income = _get_annual_income(spouse_data)
    income_source = spouse_data.get('income_source', 'w2')
    salary = float(spouse_data.get('salary', 0))
    distributions = float(spouse_data.get('distributions', 0))
    state_code = spouse_data.get('state_code', None)

    federal = TaxCalculator.calculate_federal_tax(
        annual_income, filing_status, dependents, tax_year,
        income_source=income_source, salary=salary, distributions=distributions
    )

    state_result = None
    state_tax = 0.0
    if state_code:
        income_for_state = federal.get('gross_income', annual_income)
        state_result = TaxCalculator.calculate_state_tax(
            income_for_state, filing_status, dependents, state_code, tax_year
        )
        if state_result:
            state_tax = state_result['total_tax']

    total_tax = federal['total_tax'] + state_tax
    effective_rate = (total_tax / annual_income * 100) if annual_income > 0 else 0.0

    return {
        'federal': federal,
        'state': state_result,
        'annual_income': annual_income,
        'totals': {
            'federal_tax': federal['total_tax'],
            'state_tax': state_tax,
            'total_tax': round(total_tax, 2),
            'effective_rate': round(effective_rate, 2)
        }
    }


def _calculate_mfj_combined(husband_data, wife_data, dependents, tax_year):
    """Calculate MFJ combined: ONE standard deduction on combined income, FICA per-individual."""
    h_income = _get_annual_income(husband_data)
    w_income = _get_annual_income(wife_data)
    combined_income = h_income + w_income

    # ONE standard deduction for the couple
    standard_deduction = TaxCalculator.get_standard_deduction('married_joint', 'federal', None, tax_year)

    # Combined QBI from both spouses
    h_qbi = _get_qbi_eligible_income(husband_data, h_income)
    w_qbi = _get_qbi_eligible_income(wife_data, w_income)
    combined_qbi = h_qbi + w_qbi

    # Taxable income before QBI
    taxable_before_qbi = max(0, combined_income - standard_deduction)

    # QBI deduction on combined
    qbi_result = TaxCalculator.calculate_qbi_deduction(combined_qbi, taxable_before_qbi, 'married_joint', tax_year)
    qbi_deduction = qbi_result['deduction_amount']

    # Taxable income after standard deduction and QBI
    taxable_income = max(0, combined_income - standard_deduction - qbi_deduction)

    # Income tax using MFJ brackets
    brackets = TaxCalculator.get_tax_brackets('federal', None, 'married_joint', tax_year)
    tax_result = TaxCalculator.calculate_tax_by_brackets(taxable_income, brackets)

    # Child tax credit (non-refundable)
    child_credit = TaxCalculator.calculate_child_tax_credit(dependents, tax_year)
    income_tax_before_credit = tax_result['total_tax']
    income_tax = max(0.0, income_tax_before_credit - child_credit)
    credit_applied = min(child_credit, income_tax_before_credit)

    # FICA/SE per-individual (CRITICAL: never combine)
    h_payroll = _calculate_spouse_payroll_tax(husband_data, h_income, 'married_joint', tax_year)
    w_payroll = _calculate_spouse_payroll_tax(wife_data, w_income, 'married_joint', tax_year)

    # State tax per-individual
    h_state_code = husband_data.get('state_code')
    w_state_code = wife_data.get('state_code')
    h_state_result = None
    w_state_result = None
    h_state_tax = 0.0
    w_state_tax = 0.0

    if h_state_code:
        h_state_result = TaxCalculator.calculate_state_tax(h_income, 'married_joint', dependents, h_state_code, tax_year)
        if h_state_result:
            h_state_tax = h_state_result['total_tax']
    if w_state_code:
        w_state_result = TaxCalculator.calculate_state_tax(w_income, 'married_joint', 0, w_state_code, tax_year)
        if w_state_result:
            w_state_tax = w_state_result['total_tax']

    total_fica_se = h_payroll['total'] + w_payroll['total']
    total_state_tax = h_state_tax + w_state_tax
    total_tax = income_tax + total_fica_se + total_state_tax
    effective_rate = (total_tax / combined_income * 100) if combined_income > 0 else 0.0

    husband_breakdown = {
        'annual_income': h_income,
        'income_source': husband_data.get('income_source', 'w2'),
        'federal_income_tax_share': 'Joint return - income tax is on combined income',
        'fica_tax': h_payroll['fica_tax'],
        'se_tax': h_payroll['se_tax'],
        'state_tax': h_state_tax,
        'state_code': h_state_code,
        'state_detail': h_state_result
    }

    wife_breakdown = {
        'annual_income': w_income,
        'income_source': wife_data.get('income_source', 'w2'),
        'federal_income_tax_share': 'Joint return - income tax is on combined income',
        'fica_tax': w_payroll['fica_tax'],
        'se_tax': w_payroll['se_tax'],
        'state_tax': w_state_tax,
        'state_code': w_state_code,
        'state_detail': w_state_result
    }

    totals = {
        'combined_income': round(combined_income, 2),
        'standard_deduction': standard_deduction,
        'combined_qbi_deduction': qbi_deduction,
        'taxable_income': round(taxable_income, 2),
        'income_tax_before_credit': round(income_tax_before_credit, 2),
        'child_tax_credit': child_credit,
        'child_tax_credit_applied': round(credit_applied, 2),
        'income_tax': round(income_tax, 2),
        'total_fica_se': round(total_fica_se, 2),
        'total_state_tax': round(total_state_tax, 2),
        'total_tax': round(total_tax, 2),
        'effective_rate': round(effective_rate, 2),
        'marginal_tax_rate': round(tax_result['marginal_rate'] * 100, 2),
        'bracket_breakdown': tax_result['bracket_breakdown']
    }

    return {
        'husband_breakdown': husband_breakdown,
        'wife_breakdown': wife_breakdown,
        'totals': totals
    }


@calculator_bp.route('/calculator/calculate-dual', methods=['POST'])
def calculate_dual_tax():
    """Calculate dual-spouse tax liability with MFJ and MFS comparison."""
    try:
        data = request.get_json()

        husband = data.get('husband', {})
        wife = data.get('wife', {})
        dependents = int(data.get('dependents', 0))
        tax_year = int(data.get('tax_year', 2026))

        # Always calculate MFJ
        mfj = _calculate_mfj_combined(husband, wife, dependents, tax_year)

        # Always calculate MFS (dependents default to husband)
        mfs_husband = _calculate_spouse_individual(husband, 'married_separate', dependents, tax_year)
        mfs_wife = _calculate_spouse_individual(wife, 'married_separate', 0, tax_year)

        # Build comparison
        mfj_total = mfj['totals']['total_tax']
        mfs_total = mfs_husband['totals']['total_tax'] + mfs_wife['totals']['total_tax']
        savings = abs(mfj_total - mfs_total)

        if mfj_total <= mfs_total:
            recommended = 'MFJ'
            reason = f'Filing jointly saves ${savings:,.2f} compared to filing separately'
        else:
            recommended = 'MFS'
            reason = f'Filing separately saves ${savings:,.2f} compared to filing jointly'

        comparison = {
            'mfj_total_tax': round(mfj_total, 2),
            'mfs_combined_tax': round(mfs_total, 2),
            'savings': round(savings, 2),
            'recommended': recommended,
            'reason': reason
        }

        return jsonify({
            'success': True,
            'mfj': mfj,
            'mfs_husband': mfs_husband,
            'mfs_wife': mfs_wife,
            'comparison': comparison
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
