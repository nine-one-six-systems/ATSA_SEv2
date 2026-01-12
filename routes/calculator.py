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
