"""
Itemized Deduction Service - SALT Cap, Medical Threshold, Expense Allocation

Implements MFS compliance rules for itemized deductions:
- REQ-10: SALT cap by filing status ($20k MFS per spouse, $40.4k MFJ under 2026 OBBBA)
- REQ-11: Shared expense allocation (taxpayer/spouse/both/joint methods)

2026 SALT Caps (One Big Beautiful Bill Act):
- MFJ/Single/HOH: $40,400 base, phases out above $505k MAGI to $10k floor
- MFS: $20,000 per spouse, phases out above $250k MAGI to $5k floor
- Phase-out: $0.30 reduction per $1 over threshold
"""

from models import db, Client, ItemizedDeduction
from services.tax_calculator import TaxCalculator


class ItemizedDeductionService:
    """Service for calculating itemized deductions with IRS compliance rules"""

    # 2026 SALT caps under OBBBA
    SALT_CAPS_2026 = {
        'married_joint': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
        'married_separate': {'base': 20000, 'floor': 5000, 'phaseout_start': 250000},
        'single': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
        'head_of_household': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
        'qualifying_surviving_spouse': {'base': 40400, 'floor': 10000, 'phaseout_start': 505000},
    }

    # Pre-OBBBA SALT caps (TCJA, for years != 2026)
    SALT_CAPS_TCJA = {
        'married_joint': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
        'married_separate': {'base': 5000, 'floor': 5000, 'phaseout_start': float('inf')},
        'single': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
        'head_of_household': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
        'qualifying_surviving_spouse': {'base': 10000, 'floor': 10000, 'phaseout_start': float('inf')},
    }

    # Medical expense AGI threshold
    MEDICAL_AGI_THRESHOLD = 0.075  # 7.5% of AGI

    @staticmethod
    def calculate_salt_deduction(state_local_taxes, filing_status, magi, tax_year=2026):
        """
        Calculate SALT deduction with cap and income phase-out (REQ-10).

        Args:
            state_local_taxes: Total state and local taxes paid
            filing_status: Filing status string
            magi: Modified Adjusted Gross Income (for phase-out calculation)
            tax_year: Tax year

        Returns:
            dict: {raw_salt, cap_applied, deduction_allowed, capped_amount, phaseout_applied}
        """
        if tax_year == 2026:
            caps = ItemizedDeductionService.SALT_CAPS_2026
        else:
            caps = ItemizedDeductionService.SALT_CAPS_TCJA

        cap_data = caps.get(filing_status, caps.get('single'))
        base_cap = cap_data['base']
        floor_cap = cap_data['floor']
        phaseout_start = cap_data['phaseout_start']

        # Apply income phase-out
        phaseout_applied = False
        if magi > phaseout_start:
            phaseout_applied = True
            excess_magi = magi - phaseout_start
            reduction = excess_magi * 0.30  # $0.30 per $1 over threshold
            effective_cap = max(floor_cap, base_cap - reduction)
        else:
            effective_cap = base_cap

        # Apply cap to actual state/local taxes paid
        deduction = min(state_local_taxes, effective_cap)

        return {
            'raw_salt': state_local_taxes,
            'cap_applied': effective_cap,
            'deduction_allowed': round(deduction, 2),
            'capped_amount': round(max(0, state_local_taxes - deduction), 2),
            'phaseout_applied': phaseout_applied
        }

    @staticmethod
    def allocate_shared_expense(expense_type, total_amount, allocation_method, taxpayer_pct=None):
        """
        Allocate shared expense between spouses for MFS (REQ-11).

        Allocation methods:
        - 'taxpayer': 100% to taxpayer, 0% to spouse
        - 'spouse': 0% to taxpayer, 100% to spouse
        - 'both': Custom split by taxpayer_pct (must be 0-100)
        - 'joint': 50/50 split (default for joint payment from joint account)

        Args:
            expense_type: Type of expense (e.g., 'mortgage_interest', 'state_local_taxes')
            total_amount: Total expense amount
            allocation_method: One of 'taxpayer', 'spouse', 'both', 'joint'
            taxpayer_pct: Taxpayer's percentage (required for 'both' method)

        Returns:
            dict: {taxpayer_amount, spouse_amount, taxpayer_pct, spouse_pct, method}
        """
        if allocation_method == 'taxpayer':
            return {
                'taxpayer_amount': round(total_amount, 2),
                'spouse_amount': 0,
                'taxpayer_pct': 100,
                'spouse_pct': 0,
                'method': 'taxpayer'
            }

        elif allocation_method == 'spouse':
            return {
                'taxpayer_amount': 0,
                'spouse_amount': round(total_amount, 2),
                'taxpayer_pct': 0,
                'spouse_pct': 100,
                'method': 'spouse'
            }

        elif allocation_method == 'both':
            if taxpayer_pct is None:
                raise ValueError("taxpayer_pct required for 'both' allocation")
            if not (0 <= taxpayer_pct <= 100):
                raise ValueError("taxpayer_pct must be between 0 and 100")

            spouse_pct = 100 - taxpayer_pct
            taxpayer_amount = total_amount * (taxpayer_pct / 100)
            spouse_amount = total_amount * (spouse_pct / 100)

            return {
                'taxpayer_amount': round(taxpayer_amount, 2),
                'spouse_amount': round(spouse_amount, 2),
                'taxpayer_pct': taxpayer_pct,
                'spouse_pct': spouse_pct,
                'method': 'both'
            }

        else:  # 'joint' or default
            return {
                'taxpayer_amount': round(total_amount / 2, 2),
                'spouse_amount': round(total_amount / 2, 2),
                'taxpayer_pct': 50,
                'spouse_pct': 50,
                'method': 'joint'
            }

    @staticmethod
    def calculate_itemized_deductions(client_id, tax_year=2026):
        """
        Calculate total itemized deductions with SALT cap and medical threshold.

        Steps:
        1. Query ItemizedDeduction record for client + year
        2. Apply medical expense threshold (7.5% of AGI)
        3. Apply SALT cap with income phase-out
        4. Sum all categories
        5. Compare to standard deduction

        Args:
            client_id: Client ID
            tax_year: Tax year

        Returns:
            dict: {use_itemized, itemized_total, standard_deduction, benefit_vs_standard, breakdown}
        """
        client = Client.query.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Get standard deduction for comparison
        standard_deduction = TaxCalculator.get_standard_deduction(
            filing_status=client.filing_status,
            tax_type='federal',
            tax_year=tax_year
        )

        # Query itemized deduction record
        itemized = ItemizedDeduction.query.filter_by(
            client_id=client_id,
            tax_year=tax_year
        ).first()

        if not itemized:
            # No itemized data entered -- default to standard
            return {
                'use_itemized': False,
                'itemized_total': 0,
                'standard_deduction': standard_deduction,
                'benefit_vs_standard': -standard_deduction,
                'breakdown': {
                    'medical_expenses': {'raw': 0, 'threshold': 0, 'deductible': 0},
                    'state_local_taxes': {'raw': 0, 'cap': 0, 'deductible': 0, 'capped_amount': 0},
                    'mortgage_interest': 0,
                    'charitable_contributions': 0
                }
            }

        # Estimate AGI from existing analysis or income data
        from services.analysis_engine import AnalysisEngine
        try:
            _, summary = AnalysisEngine.analyze_client(client_id)
            agi = summary.get('total_income', 0)
        except Exception:
            agi = 0

        # 1. Medical expenses: only above 7.5% of AGI
        medical_threshold = agi * ItemizedDeductionService.MEDICAL_AGI_THRESHOLD
        medical_deductible = max(0, (itemized.medical_expenses or 0) - medical_threshold)

        # 2. SALT deduction with cap
        salt_result = ItemizedDeductionService.calculate_salt_deduction(
            state_local_taxes=itemized.state_local_taxes or 0,
            filing_status=client.filing_status,
            magi=agi,
            tax_year=tax_year
        )

        # 3. Mortgage interest (no cap for primary residence up to $750k mortgage)
        mortgage_interest = itemized.mortgage_interest or 0

        # 4. Charitable contributions (no cap for basic analysis)
        charitable = itemized.charitable_contributions or 0

        # Sum itemized deductions
        itemized_total = round(
            medical_deductible +
            salt_result['deduction_allowed'] +
            mortgage_interest +
            charitable,
            2
        )

        use_itemized = itemized_total > standard_deduction

        return {
            'use_itemized': use_itemized,
            'itemized_total': itemized_total,
            'standard_deduction': standard_deduction,
            'benefit_vs_standard': round(itemized_total - standard_deduction, 2),
            'breakdown': {
                'medical_expenses': {
                    'raw': itemized.medical_expenses or 0,
                    'threshold': round(medical_threshold, 2),
                    'deductible': round(medical_deductible, 2)
                },
                'state_local_taxes': {
                    'raw': salt_result['raw_salt'],
                    'cap': salt_result['cap_applied'],
                    'deductible': salt_result['deduction_allowed'],
                    'capped_amount': salt_result['capped_amount']
                },
                'mortgage_interest': mortgage_interest,
                'charitable_contributions': charitable
            }
        }
