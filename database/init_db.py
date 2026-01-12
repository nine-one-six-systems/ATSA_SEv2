from models import db, IRSReference, AnalysisSummary, TaxBracket, StandardDeduction

def init_database():
    """Initialize database tables and seed IRS references"""
    # Import all models to ensure tables are created
    from models.client import Client
    from models.document import Document
    from models.extracted_data import ExtractedData
    from models.analysis import AnalysisResult, AnalysisSummary
    from models.irs_reference import IRSReference
    from models.tax_tables import TaxBracket, StandardDeduction
    
    db.create_all()
    seed_irs_references()
    populate_tax_tables()

def seed_irs_references():
    """Seed IRS references table with common tax code sections"""
    # Check if already seeded
    if IRSReference.query.first():
        return
    
    irs_refs = [
        {
            'section': 'IRC Section 179',
            'title': 'Section 179 Deduction',
            'description': 'Allows businesses to deduct the full purchase price of qualifying equipment and/or software purchased or financed during the tax year.',
            'url': 'https://www.irs.gov/publications/p946',
            'applicable_forms': ['Schedule C', 'Form 4562']
        },
        {
            'section': 'IRC Section 401(k)',
            'title': '401(k) Retirement Plan Contributions',
            'description': 'Employer-sponsored retirement plan contributions that reduce taxable income.',
            'url': 'https://www.irs.gov/retirement-plans/401k-plans',
            'applicable_forms': ['W-2', 'Form 1040']
        },
        {
            'section': 'IRC Section 408',
            'title': 'Individual Retirement Arrangements (IRA)',
            'description': 'Contributions to traditional IRAs may be tax-deductible, reducing taxable income.',
            'url': 'https://www.irs.gov/retirement-plans/individual-retirement-arrangements-iras',
            'applicable_forms': ['Form 1040', 'Form 5498']
        },
        {
            'section': 'IRC Section 223',
            'title': 'Health Savings Accounts (HSA)',
            'description': 'Contributions to HSAs are tax-deductible and can reduce taxable income.',
            'url': 'https://www.irs.gov/publications/p969',
            'applicable_forms': ['Form 1040', 'Form 8889']
        },
        {
            'section': 'IRC Section 170',
            'title': 'Charitable Contributions',
            'description': 'Deductions for charitable contributions to qualified organizations.',
            'url': 'https://www.irs.gov/charities-non-profits/charitable-organizations',
            'applicable_forms': ['Schedule A', 'Form 1040']
        },
        {
            'section': 'IRC Section 1211',
            'title': 'Capital Loss Deduction',
            'description': 'Tax-loss harvesting: Deduct capital losses against capital gains and up to $3,000 against ordinary income.',
            'url': 'https://www.irs.gov/publications/p544',
            'applicable_forms': ['Schedule D', 'Form 1040']
        },
        {
            'section': 'IRC Section 408A',
            'title': 'Roth IRA Conversions',
            'description': 'Convert traditional IRA to Roth IRA for tax-free growth and withdrawals in retirement.',
            'url': 'https://www.irs.gov/retirement-plans/roth-iras',
            'applicable_forms': ['Form 1040', 'Form 8606']
        },
        {
            'section': 'IRC Section 199A',
            'title': 'Qualified Business Income Deduction',
            'description': '20% deduction for qualified business income from pass-through entities.',
            'url': 'https://www.irs.gov/newsroom/tax-cuts-and-jobs-act-provision-11011-section-199a-qualified-business-income-deduction',
            'applicable_forms': ['Schedule C', 'Schedule E', 'Form 1040']
        },
        {
            'section': 'IRC Section 162',
            'title': 'Business Expense Deductions',
            'description': 'Ordinary and necessary business expenses are deductible.',
            'url': 'https://www.irs.gov/publications/p535',
            'applicable_forms': ['Schedule C', 'Form 1040']
        },
        {
            'section': 'IRC Section 213',
            'title': 'Medical and Dental Expenses',
            'description': 'Deductible medical expenses exceeding 7.5% of AGI.',
            'url': 'https://www.irs.gov/publications/p502',
            'applicable_forms': ['Schedule A', 'Form 1040']
        },
        {
            'section': 'IRC Section 163',
            'title': 'Mortgage Interest Deduction',
            'description': 'Deductible interest on qualified home mortgages.',
            'url': 'https://www.irs.gov/publications/p936',
            'applicable_forms': ['Schedule A', 'Form 1040']
        },
        {
            'section': 'IRC Section 25A',
            'title': 'Education Credits',
            'description': 'American Opportunity Credit and Lifetime Learning Credit for qualified education expenses.',
            'url': 'https://www.irs.gov/credits-deductions/individuals/education-credits-aotc-llc',
            'applicable_forms': ['Form 1040', 'Form 8863']
        },
        {
            'section': 'IRC Section 25D',
            'title': 'Residential Energy Credits',
            'description': 'Tax credits for residential energy efficient property.',
            'url': 'https://www.irs.gov/credits-deductions/individuals/residential-energy-credits',
            'applicable_forms': ['Form 1040', 'Form 5695']
        },
        {
            'section': 'IRC Section 1031',
            'title': 'Like-Kind Exchanges',
            'description': 'Defer capital gains tax by exchanging like-kind property.',
            'url': 'https://www.irs.gov/publications/p544',
            'applicable_forms': ['Form 8824', 'Form 1040']
        },
        {
            'section': 'IRC Section 529',
            'title': '529 Education Savings Plans',
            'description': 'Tax-advantaged savings plans for education expenses.',
            'url': 'https://www.irs.gov/taxtopics/tc310',
            'applicable_forms': ['Form 1040']
        }
    ]
    
    for ref_data in irs_refs:
        ref = IRSReference(
            section=ref_data['section'],
            title=ref_data['title'],
            description=ref_data['description'],
            url=ref_data['url']
        )
        ref.set_applicable_forms(ref_data['applicable_forms'])
        db.session.add(ref)
    
    db.session.commit()

def populate_tax_tables():
    """Populate tax brackets and standard deductions"""
    from services.tax_data_service import TaxDataService
    
    # Check if tax tables already exist for 2026
    existing_brackets = TaxBracket.query.filter_by(tax_year=2026).first()
    if existing_brackets:
        # Check if state brackets are using placeholder data (5% flat rate)
        # Real data will have varied rates, so if we see 5% for multiple states, it's likely placeholder
        state_brackets = TaxBracket.query.filter_by(tax_type='state', tax_year=2026).all()
        if state_brackets:
            # Check if brackets have placeholder characteristics:
            # 1. All brackets have same rate (5%)
            # 2. All brackets start at 0 with no max
            # 3. Deductions are placeholder ($2000)
            
            # Sample a few brackets to check for placeholder pattern
            sample_brackets = state_brackets[:10]  # Check first 10
            has_placeholder_rate = all(b.tax_rate == 0.05 for b in sample_brackets)
            has_placeholder_structure = all(
                b.bracket_min == 0 and b.bracket_max is None 
                for b in sample_brackets
            )
            
            # Check deductions for placeholder
            sample_deductions = StandardDeduction.query.filter_by(
                tax_type='state', tax_year=2026
            ).limit(10).all()
            has_placeholder_deductions = all(
                d.deduction_amount == 2000 for d in sample_deductions
            ) if sample_deductions else False
            
            # If we detect placeholder data, repopulate
            if has_placeholder_rate and has_placeholder_structure:
                print("Detected placeholder state tax data. Repopulating with real data...")
                TaxBracket.query.filter_by(tax_year=2026).delete()
                StandardDeduction.query.filter_by(tax_year=2026).delete()
                db.session.commit()
                TaxDataService.populate_tax_tables(tax_year=2026)
                return
            
            # Check if only 'single' filing status exists (incomplete data)
            filing_statuses = set([b.filing_status for b in state_brackets])
            if filing_statuses == {'single'}:
                print("Detected incomplete state tax data (only single filing status). Repopulating...")
                TaxBracket.query.filter_by(tax_year=2026).delete()
                StandardDeduction.query.filter_by(tax_year=2026).delete()
                db.session.commit()
                TaxDataService.populate_tax_tables(tax_year=2026)
                return
        
        return  # Already populated with real data
    
    # Populate tax tables for 2026
    print("Populating tax tables for 2026...")
    TaxDataService.populate_tax_tables(tax_year=2026)
