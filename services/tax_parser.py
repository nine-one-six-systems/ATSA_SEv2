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

