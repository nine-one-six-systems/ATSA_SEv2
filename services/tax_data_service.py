from models import db, TaxBracket, StandardDeduction
from datetime import datetime
import os
from services.state_tax_parser import get_state_tax_data

class TaxDataService:
    """Service for fetching and populating tax tables from online sources"""
    
    @staticmethod
    def fetch_federal_tax_brackets(tax_year=2026):
        """
        Fetch federal tax brackets for a given year.
        Returns hardcoded data for 2026 (with inflation adjustments from 2024).
        Can be extended to fetch from IRS.gov.
        
        Returns:
            list: List of dicts with bracket information
        """
        if tax_year == 2026:
            # 2026 Federal Tax Brackets (estimated with ~5% inflation adjustment from 2024)
            brackets = [
                # Single
                {'filing_status': 'single', 'bracket_min': 0, 'bracket_max': 12200, 'tax_rate': 0.10},
                {'filing_status': 'single', 'bracket_min': 12200, 'bracket_max': 49500, 'tax_rate': 0.12},
                {'filing_status': 'single', 'bracket_min': 49500, 'bracket_max': 105550, 'tax_rate': 0.22},
                {'filing_status': 'single', 'bracket_min': 105550, 'bracket_max': 201550, 'tax_rate': 0.24},
                {'filing_status': 'single', 'bracket_min': 201550, 'bracket_max': 255900, 'tax_rate': 0.32},
                {'filing_status': 'single', 'bracket_min': 255900, 'bracket_max': 639800, 'tax_rate': 0.35},
                {'filing_status': 'single', 'bracket_min': 639800, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Married Filing Jointly
                {'filing_status': 'married_joint', 'bracket_min': 0, 'bracket_max': 24400, 'tax_rate': 0.10},
                {'filing_status': 'married_joint', 'bracket_min': 24400, 'bracket_max': 99000, 'tax_rate': 0.12},
                {'filing_status': 'married_joint', 'bracket_min': 99000, 'bracket_max': 211100, 'tax_rate': 0.22},
                {'filing_status': 'married_joint', 'bracket_min': 211100, 'bracket_max': 403100, 'tax_rate': 0.24},
                {'filing_status': 'married_joint', 'bracket_min': 403100, 'bracket_max': 511800, 'tax_rate': 0.32},
                {'filing_status': 'married_joint', 'bracket_min': 511800, 'bracket_max': 767800, 'tax_rate': 0.35},
                {'filing_status': 'married_joint', 'bracket_min': 767800, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Married Filing Separately
                {'filing_status': 'married_separate', 'bracket_min': 0, 'bracket_max': 12200, 'tax_rate': 0.10},
                {'filing_status': 'married_separate', 'bracket_min': 12200, 'bracket_max': 49500, 'tax_rate': 0.12},
                {'filing_status': 'married_separate', 'bracket_min': 49500, 'bracket_max': 105550, 'tax_rate': 0.22},
                {'filing_status': 'married_separate', 'bracket_min': 105550, 'bracket_max': 201550, 'tax_rate': 0.24},
                {'filing_status': 'married_separate', 'bracket_min': 201550, 'bracket_max': 255900, 'tax_rate': 0.32},
                {'filing_status': 'married_separate', 'bracket_min': 255900, 'bracket_max': 383900, 'tax_rate': 0.35},
                {'filing_status': 'married_separate', 'bracket_min': 383900, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Head of Household
                {'filing_status': 'head_of_household', 'bracket_min': 0, 'bracket_max': 17350, 'tax_rate': 0.10},
                {'filing_status': 'head_of_household', 'bracket_min': 17350, 'bracket_max': 66200, 'tax_rate': 0.12},
                {'filing_status': 'head_of_household', 'bracket_min': 66200, 'bracket_max': 105550, 'tax_rate': 0.22},
                {'filing_status': 'head_of_household', 'bracket_min': 105550, 'bracket_max': 201550, 'tax_rate': 0.24},
                {'filing_status': 'head_of_household', 'bracket_min': 201550, 'bracket_max': 255900, 'tax_rate': 0.32},
                {'filing_status': 'head_of_household', 'bracket_min': 255900, 'bracket_max': 639800, 'tax_rate': 0.35},
                {'filing_status': 'head_of_household', 'bracket_min': 639800, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Qualifying Surviving Spouse (same as Married Filing Jointly)
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 0, 'bracket_max': 24400, 'tax_rate': 0.10},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 24400, 'bracket_max': 99000, 'tax_rate': 0.12},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 99000, 'bracket_max': 211100, 'tax_rate': 0.22},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 211100, 'bracket_max': 403100, 'tax_rate': 0.24},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 403100, 'bracket_max': 511800, 'tax_rate': 0.32},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 511800, 'bracket_max': 767800, 'tax_rate': 0.35},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 767800, 'bracket_max': None, 'tax_rate': 0.37},
            ]
        else:
            # Fallback to 2024 data for other years
            brackets = [
                # Single
                {'filing_status': 'single', 'bracket_min': 0, 'bracket_max': 11600, 'tax_rate': 0.10},
                {'filing_status': 'single', 'bracket_min': 11600, 'bracket_max': 47150, 'tax_rate': 0.12},
                {'filing_status': 'single', 'bracket_min': 47150, 'bracket_max': 100525, 'tax_rate': 0.22},
                {'filing_status': 'single', 'bracket_min': 100525, 'bracket_max': 191950, 'tax_rate': 0.24},
                {'filing_status': 'single', 'bracket_min': 191950, 'bracket_max': 243725, 'tax_rate': 0.32},
                {'filing_status': 'single', 'bracket_min': 243725, 'bracket_max': 609350, 'tax_rate': 0.35},
                {'filing_status': 'single', 'bracket_min': 609350, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Married Filing Jointly
                {'filing_status': 'married_joint', 'bracket_min': 0, 'bracket_max': 23200, 'tax_rate': 0.10},
                {'filing_status': 'married_joint', 'bracket_min': 23200, 'bracket_max': 94300, 'tax_rate': 0.12},
                {'filing_status': 'married_joint', 'bracket_min': 94300, 'bracket_max': 201050, 'tax_rate': 0.22},
                {'filing_status': 'married_joint', 'bracket_min': 201050, 'bracket_max': 383900, 'tax_rate': 0.24},
                {'filing_status': 'married_joint', 'bracket_min': 383900, 'bracket_max': 487450, 'tax_rate': 0.32},
                {'filing_status': 'married_joint', 'bracket_min': 487450, 'bracket_max': 731200, 'tax_rate': 0.35},
                {'filing_status': 'married_joint', 'bracket_min': 731200, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Married Filing Separately
                {'filing_status': 'married_separate', 'bracket_min': 0, 'bracket_max': 11600, 'tax_rate': 0.10},
                {'filing_status': 'married_separate', 'bracket_min': 11600, 'bracket_max': 47150, 'tax_rate': 0.12},
                {'filing_status': 'married_separate', 'bracket_min': 47150, 'bracket_max': 100525, 'tax_rate': 0.22},
                {'filing_status': 'married_separate', 'bracket_min': 100525, 'bracket_max': 191950, 'tax_rate': 0.24},
                {'filing_status': 'married_separate', 'bracket_min': 191950, 'bracket_max': 243725, 'tax_rate': 0.32},
                {'filing_status': 'married_separate', 'bracket_min': 243725, 'bracket_max': 365600, 'tax_rate': 0.35},
                {'filing_status': 'married_separate', 'bracket_min': 365600, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Head of Household
                {'filing_status': 'head_of_household', 'bracket_min': 0, 'bracket_max': 16550, 'tax_rate': 0.10},
                {'filing_status': 'head_of_household', 'bracket_min': 16550, 'bracket_max': 63100, 'tax_rate': 0.12},
                {'filing_status': 'head_of_household', 'bracket_min': 63100, 'bracket_max': 100500, 'tax_rate': 0.22},
                {'filing_status': 'head_of_household', 'bracket_min': 100500, 'bracket_max': 191950, 'tax_rate': 0.24},
                {'filing_status': 'head_of_household', 'bracket_min': 191950, 'bracket_max': 243700, 'tax_rate': 0.32},
                {'filing_status': 'head_of_household', 'bracket_min': 243700, 'bracket_max': 609350, 'tax_rate': 0.35},
                {'filing_status': 'head_of_household', 'bracket_min': 609350, 'bracket_max': None, 'tax_rate': 0.37},
                
                # Qualifying Surviving Spouse (same as Married Filing Jointly)
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 0, 'bracket_max': 23200, 'tax_rate': 0.10},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 23200, 'bracket_max': 94300, 'tax_rate': 0.12},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 94300, 'bracket_max': 201050, 'tax_rate': 0.22},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 201050, 'bracket_max': 383900, 'tax_rate': 0.24},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 383900, 'bracket_max': 487450, 'tax_rate': 0.32},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 487450, 'bracket_max': 731200, 'tax_rate': 0.35},
                {'filing_status': 'qualifying_surviving_spouse', 'bracket_min': 731200, 'bracket_max': None, 'tax_rate': 0.37},
            ]
        
        return brackets
    
    @staticmethod
    def fetch_federal_standard_deductions(tax_year=2026):
        """
        Fetch federal standard deductions for a given year.
        Returns hardcoded data for 2026 (with inflation adjustments from 2024).
        
        Returns:
            list: List of dicts with deduction information
        """
        if tax_year == 2026:
            # 2026 Federal Standard Deductions (estimated with ~5% inflation adjustment from 2024)
            deductions = [
                {'filing_status': 'single', 'deduction_amount': 15300},
                {'filing_status': 'married_joint', 'deduction_amount': 30600},
                {'filing_status': 'married_separate', 'deduction_amount': 15300},
                {'filing_status': 'head_of_household', 'deduction_amount': 23000},
                {'filing_status': 'qualifying_surviving_spouse', 'deduction_amount': 30600},
            ]
        else:
            # Fallback to 2024 data for other years
            deductions = [
                {'filing_status': 'single', 'deduction_amount': 14600},
                {'filing_status': 'married_joint', 'deduction_amount': 29200},
                {'filing_status': 'married_separate', 'deduction_amount': 14600},
                {'filing_status': 'head_of_household', 'deduction_amount': 21900},
                {'filing_status': 'qualifying_surviving_spouse', 'deduction_amount': 29200},
            ]
        
        return deductions
    
    @staticmethod
    def fetch_state_tax_data(tax_year=2026):
        """
        Fetch state tax brackets and deductions for all 50 states.
        Parses data from state_tax_reference.md file.
        
        Returns:
            tuple: (brackets list, deductions list)
        """
        if tax_year != 2026:
            # For now, only support 2026 data
            # Could extend to parse other years if needed
            return [], []
        
        # Get file path to markdown reference
        # Try multiple possible locations
        possible_paths = [
            os.path.join(os.path.expanduser('~'), 'Downloads', 'files', 'state_tax_reference.md'),
            os.path.join(os.path.dirname(__file__), '..', 'data', 'state_tax_reference.md'),
            'data/state_tax_reference.md',
            'state_tax_reference.md'
        ]
        
        filepath = None
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            # Fallback to placeholder data if file not found
            print("Warning: state_tax_reference.md not found. Using placeholder data.")
            return TaxDataService._get_placeholder_state_data()
        
        try:
            # Parse the markdown file
            parsed_data = get_state_tax_data(filepath)
            
            brackets = parsed_data['brackets']
            deductions = parsed_data['deductions']
            
            # Ensure qualifying_surviving_spouse has brackets/deductions
            # Map to married_joint if missing
            brackets_by_state_status = {}
            deductions_by_state_status = {}
            
            for bracket in brackets:
                key = (bracket['state_code'], bracket['filing_status'])
                if key not in brackets_by_state_status:
                    brackets_by_state_status[key] = []
                brackets_by_state_status[key].append(bracket)
            
            for deduction in deductions:
                key = (deduction['state_code'], deduction['filing_status'])
                deductions_by_state_status[key] = deduction
            
            # Add missing qualifying_surviving_spouse entries
            all_states = set(b['state_code'] for b in brackets)
            for state_code in all_states:
                qss_key = (state_code, 'qualifying_surviving_spouse')
                mj_key = (state_code, 'married_joint')
                
                # Add brackets if missing
                if qss_key not in brackets_by_state_status and mj_key in brackets_by_state_status:
                    for bracket in brackets_by_state_status[mj_key]:
                        brackets.append({
                            'state_code': state_code,
                            'filing_status': 'qualifying_surviving_spouse',
                            'bracket_min': bracket['bracket_min'],
                            'bracket_max': bracket['bracket_max'],
                            'tax_rate': bracket['tax_rate']
                        })
                
                # Add deductions if missing
                if qss_key not in deductions_by_state_status and mj_key in deductions_by_state_status:
                    mj_deduction = deductions_by_state_status[mj_key]
                    deductions.append({
                        'state_code': state_code,
                        'filing_status': 'qualifying_surviving_spouse',
                        'deduction_amount': mj_deduction['deduction_amount']
                    })
            
            return brackets, deductions
            
        except Exception as e:
            print(f"Error parsing state tax data: {e}")
            # Fallback to placeholder data
            return TaxDataService._get_placeholder_state_data()
    
    @staticmethod
    def _get_placeholder_state_data():
        """Fallback placeholder data if parser fails"""
        states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
        ]
        
        brackets = []
        deductions = []
        no_income_tax_states = ['AK', 'FL', 'NV', 'NH', 'SD', 'TN', 'TX', 'WA', 'WY']
        filing_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household', 'qualifying_surviving_spouse']
        
        for state in states:
            if state not in no_income_tax_states:
                for filing_status in filing_statuses:
                    brackets.append({
                        'state_code': state,
                        'filing_status': filing_status,
                        'bracket_min': 0,
                        'bracket_max': None,
                        'tax_rate': 0.05
                    })
                    deductions.append({
                        'state_code': state,
                        'filing_status': filing_status,
                        'deduction_amount': 2000
                    })
        
        return brackets, deductions
    
    @staticmethod
    def populate_tax_tables(tax_year=2026):
        """
        Populate tax brackets and standard deductions into the database.
        
        Args:
            tax_year: Tax year to populate (default 2024)
        """
        # Clear existing data for this year
        TaxBracket.query.filter_by(tax_year=tax_year).delete()
        StandardDeduction.query.filter_by(tax_year=tax_year).delete()
        
        # Fetch and populate federal brackets
        federal_brackets = TaxDataService.fetch_federal_tax_brackets(tax_year)
        for bracket_data in federal_brackets:
            bracket = TaxBracket(
                tax_type='federal',
                state_code=None,
                filing_status=bracket_data['filing_status'],
                bracket_min=bracket_data['bracket_min'],
                bracket_max=bracket_data['bracket_max'],
                tax_rate=bracket_data['tax_rate'],
                tax_year=tax_year
            )
            db.session.add(bracket)
        
        # Fetch and populate federal standard deductions
        federal_deductions = TaxDataService.fetch_federal_standard_deductions(tax_year)
        for deduction_data in federal_deductions:
            deduction = StandardDeduction(
                tax_type='federal',
                state_code=None,
                filing_status=deduction_data['filing_status'],
                deduction_amount=deduction_data['deduction_amount'],
                tax_year=tax_year
            )
            db.session.add(deduction)
        
        # Fetch and populate state tax data
        state_brackets, state_deductions = TaxDataService.fetch_state_tax_data(tax_year)
        for bracket_data in state_brackets:
            bracket = TaxBracket(
                tax_type='state',
                state_code=bracket_data['state_code'],
                filing_status=bracket_data['filing_status'],
                bracket_min=bracket_data['bracket_min'],
                bracket_max=bracket_data['bracket_max'],
                tax_rate=bracket_data['tax_rate'],
                tax_year=tax_year
            )
            db.session.add(bracket)
        
        for deduction_data in state_deductions:
            deduction = StandardDeduction(
                tax_type='state',
                state_code=deduction_data['state_code'],
                filing_status=deduction_data['filing_status'],
                deduction_amount=deduction_data['deduction_amount'],
                tax_year=tax_year
            )
            db.session.add(deduction)
        
        db.session.commit()
