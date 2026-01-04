from models import db, IRSReference

def init_database():
    """Initialize database tables and seed IRS references"""
    db.create_all()
    seed_irs_references()

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

