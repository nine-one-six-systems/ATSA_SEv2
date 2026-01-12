"""
Parser for state_tax_reference.md to extract tax brackets, deductions, and surtax information.
"""

import re
from typing import Dict, List, Optional, Tuple


class StateTaxParser:
    """Parse state tax data from markdown reference file"""
    
    # Filing status mapping from abbreviations to full names
    FILING_STATUS_MAP = {
        'Single': 'single',
        'Mfj': 'married_joint',
        'Mfs': 'married_separate',
        'Hoh': 'head_of_household',
        'All': 'all'  # Special case - applies to all filing statuses
    }
    
    # All filing statuses we need to support
    ALL_FILING_STATUSES = ['single', 'married_joint', 'married_separate', 'head_of_household', 'qualifying_surviving_spouse']
    
    @staticmethod
    def parse_markdown_file(filepath: str) -> Dict:
        """
        Parse the markdown reference file and extract all state tax data.
        
        Args:
            filepath: Path to state_tax_reference.md
            
        Returns:
            dict: {
                'states': {state_code: {metadata}},
                'brackets': [{state_code, filing_status, bracket_min, bracket_max, tax_rate}],
                'deductions': [{state_code, filing_status, deduction_amount}],
                'surtaxes': [{state_code, threshold, rate, description}]
            }
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by state sections (## StateName)
        state_sections = re.split(r'\n## ', content)
        
        # Skip the header section (everything before first ##)
        if state_sections:
            state_sections = state_sections[1:]
        
        states_data = {}
        brackets = []
        deductions = []
        surtaxes = []
        
        for section in state_sections:
            state_data = StateTaxParser._parse_state_section(section)
            if state_data:
                state_code = state_data['state_code']
                states_data[state_code] = state_data['metadata']
                
                # Add brackets
                for bracket in state_data['brackets']:
                    brackets.append(bracket)
                
                # Add deductions
                for deduction in state_data['deductions']:
                    deductions.append(deduction)
                
                # Add surtaxes
                for surtax in state_data['surtaxes']:
                    surtaxes.append(surtax)
        
        return {
            'states': states_data,
            'brackets': brackets,
            'deductions': deductions,
            'surtaxes': surtaxes
        }
    
    @staticmethod
    def _parse_state_section(section: str) -> Optional[Dict]:
        """Parse a single state section"""
        lines = section.split('\n')
        if not lines:
            return None
        
        # Extract state name (first line)
        state_name = lines[0].strip()
        
        # Extract metadata
        metadata = StateTaxParser._extract_metadata(section)
        state_code = metadata.get('state_abbreviation', '').upper()
        
        if not state_code:
            return None
        
        # Check if state has income tax
        has_income_tax = metadata.get('has_income_tax', '').lower() == 'yes'
        
        if not has_income_tax:
            # No income tax state - return empty brackets/deductions
            return {
                'state_code': state_code,
                'metadata': metadata,
                'brackets': [],
                'deductions': [],
                'surtaxes': []
            }
        
        # Extract brackets
        brackets = StateTaxParser._extract_brackets(section, state_code)
        
        # Extract deductions
        deductions = StateTaxParser._extract_deductions(section, state_code)
        
        # Extract surtaxes
        surtaxes = StateTaxParser._extract_surtaxes(section, state_code)
        
        return {
            'state_code': state_code,
            'metadata': metadata,
            'brackets': brackets,
            'deductions': deductions,
            'surtaxes': surtaxes
        }
    
    @staticmethod
    def _extract_metadata(section: str) -> Dict:
        """Extract state metadata"""
        metadata = {}
        
        # Tax System
        tax_system_match = re.search(r'\*\*Tax System\*\*:\s*(\w+)', section)
        if tax_system_match:
            metadata['tax_system'] = tax_system_match.group(1).lower()
        
        # State Abbreviation
        abbr_match = re.search(r'\*\*State Abbreviation\*\*:\s*(\w+)', section)
        if abbr_match:
            metadata['state_abbreviation'] = abbr_match.group(1).upper()
        
        # Has Income Tax
        has_tax_match = re.search(r'\*\*Has Income Tax\*\*:\s*(\w+)', section)
        if has_tax_match:
            metadata['has_income_tax'] = has_tax_match.group(1)
        
        return metadata
    
    @staticmethod
    def _extract_brackets(section: str, state_code: str) -> List[Dict]:
        """Extract tax brackets from section"""
        brackets = []
        
        # Find Tax Brackets section
        brackets_match = re.search(r'### Tax Brackets \(2026\)(.*?)(?=###|$)', section, re.DOTALL)
        if not brackets_match:
            return brackets
        
        brackets_section = brackets_match.group(1)
        
        # Find all filing status sections (Single, Mfj, Mfs, Hoh, All)
        filing_status_pattern = r'\*\*(Single|Mfj|Mfs|Hoh|All)\*\*:(.*?)(?=\*\*|$)'
        filing_status_matches = re.finditer(filing_status_pattern, brackets_section, re.DOTALL)
        
        for match in filing_status_matches:
            filing_status_abbr = match.group(1)
            bracket_table = match.group(2)
            
            # Map filing status
            filing_status = StateTaxParser.FILING_STATUS_MAP.get(filing_status_abbr, filing_status_abbr.lower())
            
            # Parse bracket table
            parsed_brackets = StateTaxParser._parse_bracket_table(bracket_table, state_code, filing_status)
            brackets.extend(parsed_brackets)
        
        return brackets
    
    @staticmethod
    def _parse_bracket_table(table_text: str, state_code: str, filing_status: str) -> List[Dict]:
        """Parse a bracket table into bracket dictionaries"""
        brackets = []
        
        # Pattern to match bracket rows: $X - $Y or $X - and above
        # Also handles: $X - $Y,XXX.XX format
        # Examples: "$0 - $500.0 | 2.0%" or "$3,001 - and above | 5.0%"
        bracket_pattern = r'\|\s*\$\s*([\d,]+(?:\.\d+)?)\s*-\s*(?:and above|\$\s*([\d,]+(?:\.\d+)?))\s*\|\s*([\d.]+)%'
        
        for match in re.finditer(bracket_pattern, table_text):
            bracket_min_str = match.group(1).replace(',', '')
            bracket_max_str = match.group(2) if match.group(2) else None
            rate_str = match.group(3)
            
            bracket_min = float(bracket_min_str)
            bracket_max = float(bracket_max_str.replace(',', '')) if bracket_max_str else None
            tax_rate = float(rate_str) / 100.0  # Convert percentage to decimal
            
            # Handle "All" filing status - duplicate for all filing statuses
            if filing_status == 'all':
                for fs in StateTaxParser.ALL_FILING_STATUSES:
                    brackets.append({
                        'state_code': state_code,
                        'filing_status': fs,
                        'bracket_min': bracket_min,
                        'bracket_max': bracket_max,
                        'tax_rate': tax_rate
                    })
            else:
                # Map to standard filing status name
                brackets.append({
                    'state_code': state_code,
                    'filing_status': filing_status,
                    'bracket_min': bracket_min,
                    'bracket_max': bracket_max,
                    'tax_rate': tax_rate
                })
        
        return brackets
    
    @staticmethod
    def _extract_deductions(section: str, state_code: str) -> List[Dict]:
        """Extract standard deductions from section"""
        deductions = []
        
        # Find Standard Deductions section
        deductions_match = re.search(r'### Standard Deductions \(2026\)(.*?)(?=###|$)', section, re.DOTALL)
        if not deductions_match:
            return deductions
        
        deductions_section = deductions_match.group(1)
        
        # Pattern to match deduction table rows
        # Format: | Filing Status | Amount |
        #         | Single | $X,XXX |
        deduction_pattern = r'\|\s*(Single|Mfj|Mfs|Hoh|Qualifying Surviving Spouse)\s*\|\s*\$\s*([\d,]+)\s*\|'
        
        for match in re.finditer(deduction_pattern, deductions_section):
            filing_status_str = match.group(1)
            amount_str = match.group(2).replace(',', '')
            
            # Map filing status
            filing_status_map = {
                'Single': 'single',
                'Mfj': 'married_joint',
                'Mfs': 'married_separate',
                'Hoh': 'head_of_household',
                'Qualifying Surviving Spouse': 'qualifying_surviving_spouse'
            }
            filing_status = filing_status_map.get(filing_status_str, filing_status_str.lower())
            
            deduction_amount = float(amount_str)
            
            deductions.append({
                'state_code': state_code,
                'filing_status': filing_status,
                'deduction_amount': deduction_amount
            })
        
        return deductions
    
    @staticmethod
    def _extract_surtaxes(section: str, state_code: str) -> List[Dict]:
        """Extract surtax information from Special Provisions section"""
        surtaxes = []
        
        # Find Special Provisions section
        provisions_match = re.search(r'### Special Provisions(.*?)(?=###|$)', section, re.DOTALL)
        if not provisions_match:
            return surtaxes
        
        provisions_text = provisions_match.group(1)
        
        # Pattern for California Behavioral Health Services Tax
        # "1% Behavioral Health Services Tax applies to taxable income over $1,000,000"
        ca_pattern = r'(\d+(?:\.\d+)?)%\s+Behavioral Health Services Tax.*?over\s+\$\s*([\d,]+)'
        ca_match = re.search(ca_pattern, provisions_text, re.IGNORECASE)
        if ca_match and state_code == 'CA':
            rate = float(ca_match.group(1)) / 100.0
            threshold = float(ca_match.group(2).replace(',', ''))
            surtaxes.append({
                'state_code': state_code,
                'threshold': threshold,
                'rate': rate,
                'description': 'Behavioral Health Services Tax'
            })
        
        # Pattern for other surtaxes (e.g., "additional X% tax on income over $Y")
        # This is a general pattern that might catch other surtaxes
        general_pattern = r'(\d+(?:\.\d+)?)%\s+(?:additional|surtax|tax).*?(?:over|above|exceeding)\s+\$\s*([\d,]+)'
        general_matches = re.finditer(general_pattern, provisions_text, re.IGNORECASE)
        for match in general_matches:
            # Skip if already captured as CA surtax
            if state_code == 'CA' and 'Behavioral Health' in provisions_text:
                continue
            
            rate = float(match.group(1)) / 100.0
            threshold = float(match.group(2).replace(',', ''))
            surtaxes.append({
                'state_code': state_code,
                'threshold': threshold,
                'rate': rate,
                'description': 'Additional surtax'
            })
        
        return surtaxes


def get_state_tax_data(filepath: str = None) -> Dict:
    """
    Get parsed state tax data.
    
    Args:
        filepath: Path to state_tax_reference.md. If None, uses default location.
        
    Returns:
        dict: Parsed state tax data
    """
    if filepath is None:
        # Default to Downloads folder
        import os
        filepath = os.path.join(
            os.path.expanduser('~'),
            'Downloads',
            'files',
            'state_tax_reference.md'
        )
    
    parser = StateTaxParser()
    return parser.parse_markdown_file(filepath)
