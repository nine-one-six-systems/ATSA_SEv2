import re
from models import db, ExtractedData

class TaxParser:
    """Service for parsing OCR text and extracting tax form data"""
    
    # Form detection patterns
    FORM_PATTERNS = {
        '1040': r'Form\s+1040|1040\s+U\.S\.\s+Individual\s+Income\s+Tax\s+Return',
        'W-2': r'Form\s+W-2|W-2\s+Wage\s+and\s+Tax\s+Statement',
        '1099-INT': r'Form\s+1099-INT|1099-INT\s+Interest\s+Income',
        '1099-DIV': r'Form\s+1099-DIV|1099-DIV\s+Dividends\s+and\s+Distributions',
        '1099-MISC': r'Form\s+1099-MISC|1099-MISC\s+Miscellaneous\s+Income',
        '1099-NEC': r'Form\s+1099-NEC|1099-NEC\s+Nonemployee\s+Compensation',
        'Schedule A': r'Schedule\s+A|Itemized\s+Deductions',
        'Schedule B': r'Schedule\s+B|Interest\s+and\s+Dividend\s+Income',
        'Schedule C': r'Schedule\s+C|Profit\s+or\s+Loss\s+from\s+Business',
        'Schedule D': r'Schedule\s+D|Capital\s+Gains\s+and\s+Losses',
        'Schedule E': r'Schedule\s+E|Supplemental\s+Income\s+and\s+Loss',
        'Schedule SE': r'Schedule\s+SE|Self-Employment\s+Tax',
        'Schedule 1': r'Schedule\s+1|Additional\s+Income\s+and\s+Adjustments',
        'Schedule F': r'Schedule\s+F|Farm\s+Income',
        'Form 4562': r'Form\s+4562|Depreciation\s+and\s+Amortization',
        'Form 8829': r'Form\s+8829|Expenses\s+for\s+Business\s+Use\s+of\s+Home',
        'Form 8995': r'Form\s+8995|Qualified\s+Business\s+Income\s+Deduction',
        'Form 8995-A': r'Form\s+8995-A|Qualified\s+Business\s+Income\s+Deduction',
        'Form 6765': r'Form\s+6765|Credit\s+for\s+Increasing\s+Research\s+Activities',
        'Form 5498': r'Form\s+5498|IRA\s+Contribution\s+Information',
        'Form 8949': r'Form\s+8949|Sales\s+and\s+Other\s+Dispositions\s+of\s+Capital\s+Assets',
        'Form 8994': r'Form\s+8994|Credit\s+for\s+Paid\s+Family\s+and\s+Medical\s+Leave',
        'Form 1095-A': r'Form\s+1095-A|Health\s+Insurance\s+Marketplace\s+Statement',
        'Form 8962': r'Form\s+8962|Premium\s+Tax\s+Credit',
        'K-1': r'Schedule\s+K-1|Partner\'s\s+Share\s+of\s+Income',
    }
    
    @staticmethod
    def parse_text(text, document_id, client_id):
        """
        Parse OCR text and extract tax form data
        
        Args:
            text: OCR extracted text
            document_id: ID of the document
            client_id: ID of the client
        
        Returns:
            dict: Parsed data by form type
        """
        if not text:
            return {}
        
        # Detect forms in the text
        detected_forms = TaxParser._detect_forms(text)
        
        parsed_data = {}
        
        for form_type in detected_forms:
            form_data = TaxParser._extract_form_data(text, form_type)
            parsed_data[form_type] = form_data
            
            # Store in database
            TaxParser._store_extracted_data(document_id, client_id, form_type, form_data)
        
        return parsed_data
    
    @staticmethod
    def _detect_forms(text):
        """Detect which tax forms are present in the text"""
        detected = []
        text_upper = text.upper()
        
        for form_type, pattern in TaxParser.FORM_PATTERNS.items():
            if re.search(pattern, text_upper, re.IGNORECASE):
                detected.append(form_type)
        
        return detected
    
    @staticmethod
    def _extract_form_data(text, form_type):
        """Extract data fields for a specific form type"""
        form_data = {}
        
        if form_type == '1040':
            form_data = TaxParser._extract_1040_data(text)
        elif form_type == 'W-2':
            form_data = TaxParser._extract_w2_data(text)
        elif form_type.startswith('1099'):
            form_data = TaxParser._extract_1099_data(text, form_type)
        elif form_type == 'Schedule A':
            form_data = TaxParser._extract_schedule_a_data(text)
        elif form_type == 'Schedule C':
            form_data = TaxParser._extract_schedule_c_data(text)
        elif form_type == 'Schedule SE':
            form_data = TaxParser._extract_schedule_se_data(text)
        elif form_type == 'Schedule 1':
            form_data = TaxParser._extract_schedule_1_data(text)
        elif form_type == 'Schedule E':
            form_data = TaxParser._extract_schedule_e_data(text)
        elif form_type == 'Schedule D':
            form_data = TaxParser._extract_schedule_d_data(text)
        elif form_type == 'Form 4562':
            form_data = TaxParser._extract_form_4562_data(text)
        elif form_type == 'Form 8829':
            form_data = TaxParser._extract_form_8829_data(text)
        elif form_type == 'Form 8995':
            form_data = TaxParser._extract_form_8995_data(text)
        elif form_type == 'Form 8995-A':
            form_data = TaxParser._extract_form_8995a_data(text)
        elif form_type == 'Form 6765':
            form_data = TaxParser._extract_form_6765_data(text)
        elif form_type == 'Form 5498':
            form_data = TaxParser._extract_form_5498_data(text)
        elif form_type == 'Form 8949':
            form_data = TaxParser._extract_form_8949_data(text)
        elif form_type == 'Form 8994':
            form_data = TaxParser._extract_form_8994_data(text)
        elif form_type == 'Form 1095-A':
            form_data = TaxParser._extract_form_1095a_data(text)
        elif form_type == 'K-1':
            form_data = TaxParser._extract_k1_data(text)
        
        return form_data
    
    @staticmethod
    def _extract_1040_data(text):
        """Extract key fields from Form 1040"""
        data = {}
        
        # Extract AGI (Adjusted Gross Income)
        agi_patterns = [
            r'Adjusted\s+Gross\s+Income[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'AGI[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Line\s+11[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in agi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['agi'] = TaxParser._clean_amount(match.group(1))
                break
        
        # Extract Taxable Income
        taxable_patterns = [
            r'Taxable\s+Income[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Line\s+15[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in taxable_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['taxable_income'] = TaxParser._clean_amount(match.group(1))
                break
        
        # Extract Total Tax
        tax_patterns = [
            r'Total\s+Tax[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Line\s+16[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['total_tax'] = TaxParser._clean_amount(match.group(1))
                break
        
        # Extract Wages
        wages_patterns = [
            r'Wages[,\s]+salaries[,\s]+tips[,\s]+etc\.?[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Line\s+1[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in wages_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['wages'] = TaxParser._clean_amount(match.group(1))
                break
        
        return data
    
    @staticmethod
    def _extract_w2_data(text):
        """Extract key fields from W-2"""
        data = {}
        
        # Extract Wages
        wages_match = re.search(r'Box\s+1[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if wages_match:
            data['wages'] = TaxParser._clean_amount(wages_match.group(1))
        
        # Extract Federal Tax Withheld
        fed_tax_match = re.search(r'Box\s+2[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if fed_tax_match:
            data['federal_tax_withheld'] = TaxParser._clean_amount(fed_tax_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_1099_data(text, form_type):
        """Extract key fields from 1099 forms"""
        data = {}
        
        # Extract income amount
        income_patterns = [
            r'Interest\s+income[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Dividends[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Nonemployee\s+compensation[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        for pattern in income_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['income'] = TaxParser._clean_amount(match.group(1))
                break
        
        return data
    
    @staticmethod
    def _extract_schedule_a_data(text):
        """Extract key fields from Schedule A"""
        data = {}
        
        # Extract Medical Expenses
        med_match = re.search(r'Medical\s+and\s+dental\s+expenses[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if med_match:
            data['medical_expenses'] = TaxParser._clean_amount(med_match.group(1))
        
        # Extract Charitable Contributions
        charity_match = re.search(r'Gifts\s+to\s+charity[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if charity_match:
            data['charitable_contributions'] = TaxParser._clean_amount(charity_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_schedule_c_data(text):
        """Extract key fields from Schedule C"""
        data = {}
        
        # Extract Gross Receipts
        receipts_match = re.search(r'Gross\s+receipts[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if receipts_match:
            data['gross_receipts'] = TaxParser._clean_amount(receipts_match.group(1))
        
        # Extract Net Profit
        profit_match = re.search(r'Net\s+profit[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if profit_match:
            data['net_profit'] = TaxParser._clean_amount(profit_match.group(1))
        
        # Extract R&D expenses (line 27a)
        rd_match = re.search(r'Line\s+27a[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if rd_match:
            data['rd_expenses'] = TaxParser._clean_amount(rd_match.group(1))
        
        # Extract simplified home office (line 18)
        home_office_simple_match = re.search(r'Line\s+18[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if home_office_simple_match:
            data['simplified_home_office'] = TaxParser._clean_amount(home_office_simple_match.group(1))
        
        # Extract home office deduction (line 30)
        home_office_match = re.search(r'Line\s+30[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if home_office_match:
            data['home_office_deduction'] = TaxParser._clean_amount(home_office_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_schedule_se_data(text):
        """Extract key fields from Schedule SE"""
        data = {}
        
        # Extract total SE tax (line 6)
        se_tax_match = re.search(r'Line\s+6[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if se_tax_match:
            data['total_se_tax'] = TaxParser._clean_amount(se_tax_match.group(1))
        
        # Extract net earnings
        net_earnings_match = re.search(r'Net\s+earnings[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if net_earnings_match:
            data['net_earnings'] = TaxParser._clean_amount(net_earnings_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_schedule_1_data(text):
        """Extract key fields from Schedule 1"""
        data = {}
        
        # Extract SE tax deduction (line 15)
        se_ded_match = re.search(r'Line\s+15[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if se_ded_match:
            data['se_tax_deduction'] = TaxParser._clean_amount(se_ded_match.group(1))
        
        # Extract retirement contributions (line 16)
        retirement_match = re.search(r'Line\s+16[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if retirement_match:
            data['retirement_contributions'] = TaxParser._clean_amount(retirement_match.group(1))
        
        # Extract SE health insurance (line 17)
        health_match = re.search(r'Line\s+17[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if health_match:
            data['se_health_insurance'] = TaxParser._clean_amount(health_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_schedule_e_data(text):
        """Extract key fields from Schedule E"""
        data = {}
        
        # Extract net income
        net_income_match = re.search(r'Net\s+income[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if net_income_match:
            data['net_income'] = TaxParser._clean_amount(net_income_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_schedule_d_data(text):
        """Extract key fields from Schedule D"""
        data = {}
        
        # Extract capital gains
        gains_match = re.search(r'Capital\s+gains[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if gains_match:
            data['capital_gains'] = TaxParser._clean_amount(gains_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_4562_data(text):
        """Extract key fields from Form 4562"""
        data = {}
        
        # Extract Section 179 deduction (line 12)
        section_179_match = re.search(r'Line\s+12[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if section_179_match:
            data['section_179_deduction'] = TaxParser._clean_amount(section_179_match.group(1))
        
        # Extract total cost of 179 property (line 2)
        cost_179_match = re.search(r'Line\s+2[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if cost_179_match:
            data['total_cost_179_property'] = TaxParser._clean_amount(cost_179_match.group(1))
        
        # Extract business income limitation (line 11)
        limitation_match = re.search(r'Line\s+11[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if limitation_match:
            data['business_income_limitation'] = TaxParser._clean_amount(limitation_match.group(1))
        
        # Extract bonus depreciation (line 14)
        bonus_match = re.search(r'Line\s+14[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if bonus_match:
            data['bonus_depreciation'] = TaxParser._clean_amount(bonus_match.group(1))
        
        # Extract MACRS depreciation
        macrs_match = re.search(r'MACRS\s+depreciation[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if macrs_match:
            data['macrs_depreciation'] = TaxParser._clean_amount(macrs_match.group(1))
        
        # Extract R&D amortization
        rd_amort_match = re.search(r'R&D\s+amortization[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if rd_amort_match:
            data['rd_amortization'] = TaxParser._clean_amount(rd_amort_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_8829_data(text):
        """Extract key fields from Form 8829"""
        data = {}
        
        # Extract home office deduction (line 36)
        deduction_match = re.search(r'Line\s+36[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if deduction_match:
            data['home_office_deduction'] = TaxParser._clean_amount(deduction_match.group(1))
        
        # Extract tentative deduction (line 35)
        tentative_match = re.search(r'Line\s+35[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if tentative_match:
            data['tentative_deduction'] = TaxParser._clean_amount(tentative_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_8995_data(text):
        """Extract key fields from Form 8995"""
        data = {}
        
        # Extract QBI deduction
        qbi_match = re.search(r'QBI\s+deduction[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if qbi_match:
            data['qbi_deduction'] = TaxParser._clean_amount(qbi_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_8995a_data(text):
        """Extract key fields from Form 8995-A"""
        data = {}
        
        # Extract QBI deduction
        qbi_match = re.search(r'QBI\s+deduction[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if qbi_match:
            data['qbi_deduction'] = TaxParser._clean_amount(qbi_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_6765_data(text):
        """Extract key fields from Form 6765 (R&D Credit)"""
        data = {}
        # Form 6765 presence indicates R&D activities
        data['filed'] = True
        return data
    
    @staticmethod
    def _extract_form_5498_data(text):
        """Extract key fields from Form 5498"""
        data = {}
        
        # Extract SEP contributions (box 8)
        sep_match = re.search(r'Box\s+8[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if sep_match:
            data['sep_contributions'] = TaxParser._clean_amount(sep_match.group(1))
        
        # Extract SIMPLE contributions (box 9)
        simple_match = re.search(r'Box\s+9[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if simple_match:
            data['simple_contributions'] = TaxParser._clean_amount(simple_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_8949_data(text):
        """Extract key fields from Form 8949"""
        data = {}
        
        # Extract QSBS exclusion (Code Q)
        qsbs_match = re.search(r'Code\s+Q[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if qsbs_match:
            data['qsbs_exclusion'] = TaxParser._clean_amount(qsbs_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_8994_data(text):
        """Extract key fields from Form 8994 (FMLA Credit)"""
        data = {}
        
        # Extract credit amount (line 3)
        credit_match = re.search(r'Line\s+3[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if credit_match:
            data['credit_amount'] = TaxParser._clean_amount(credit_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_form_1095a_data(text):
        """Extract key fields from Form 1095-A"""
        data = {}
        
        # Extract premiums
        premiums_match = re.search(r'Premiums[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if premiums_match:
            data['premiums'] = TaxParser._clean_amount(premiums_match.group(1))
        
        return data
    
    @staticmethod
    def _extract_k1_data(text):
        """Extract key fields from Schedule K-1"""
        data = {}
        
        # Extract QBI amount (box 20 code Z for 1065, box 17 code V for 1120-S)
        qbi_match = re.search(r'QBI[:\s]+(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
        if qbi_match:
            data['qbi_amount'] = TaxParser._clean_amount(qbi_match.group(1))
        
        return data
    
    @staticmethod
    def _clean_amount(amount_str):
        """Clean and convert amount string to float"""
        if not amount_str:
            return None
        # Remove $ and commas
        cleaned = re.sub(r'[\$,\s]', '', amount_str)
        try:
            return float(cleaned)
        except:
            return None
    
    @staticmethod
    def _store_extracted_data(document_id, client_id, form_type, form_data):
        """Store extracted data in database"""
        for field_name, field_value in form_data.items():
            if field_value is not None:
                extracted = ExtractedData(
                    document_id=document_id,
                    client_id=client_id,
                    form_type=form_type,
                    field_name=field_name,
                    field_value=str(field_value)
                )
                db.session.add(extracted)
        
        db.session.commit()

