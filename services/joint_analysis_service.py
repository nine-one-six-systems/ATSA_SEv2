"""
Joint Analysis Service - Dual-Filer MFJ vs MFS Comparison

Orchestrates dual-filer tax analysis by coordinating existing AnalysisEngine
and TaxCalculator components. Does NOT rewrite tax calculation logic -- calls
existing methods with correct filing statuses.

Key Features:
- REQ-01: MFJ calculation using married_joint brackets and $32,200 standard deduction
- REQ-02: MFS calculation using married_separate brackets and $16,100 per spouse
- REQ-03: Three-column comparison (MFJ, MFS spouse1, MFS spouse2) with recommendation
- REQ-05: Credit eligibility filtering (MFS ineligible for EITC, student loan, education)
- REQ-06: QBI threshold enforcement (MFS $197,300, MFJ $394,600)
- REQ-08: Bidirectional cache invalidation via combined hash

Filing Status Values:
- 'married_joint' for MFJ calculations
- 'married_separate' for MFS calculations

Anti-Patterns Avoided:
- Do NOT modify TaxCalculator (already handles all filing statuses correctly)
- Do NOT use 'married' as filing status (ambiguous)
- Do NOT calculate MFJ as sum of two MFS (different brackets, different deductions)
"""

from models import db, Client, JointAnalysisSummary
from services.analysis_engine import AnalysisEngine
from services.tax_calculator import TaxCalculator
from services.itemized_deduction_service import ItemizedDeductionService
import hashlib
import json
from datetime import datetime


class JointAnalysisService:
    """Service for dual-filer MFJ vs MFS analysis"""

    # 2026 Tax Year Constants (for reference and testing)
    STANDARD_DEDUCTIONS_2026 = {
        'married_joint': 32200,
        'married_separate': 16100,
        'single': 16100,
        'head_of_household': 23650
    }

    QBI_THRESHOLDS_2026 = {
        'married_joint': 394600,
        'married_separate': 197300,
        'single': 197300,
        'head_of_household': 197300
    }

    # REQ-05: Credit eligibility by filing status
    # MFS filers are INELIGIBLE (not phased out) for these credits
    CREDIT_ELIGIBILITY = {
        'EITC': {
            'single': True,
            'married_joint': True,
            'married_separate': False,
            'head_of_household': True
        },
        'student_loan_interest': {
            'single': True,
            'married_joint': True,
            'married_separate': False,
            'head_of_household': True
        },
        'education_credits': {
            'single': True,
            'married_joint': True,
            'married_separate': False,
            'head_of_household': True
        },
        'adoption_credit': {
            'single': True,
            'married_joint': True,
            'married_separate': False,
            'head_of_household': True
        }
    }

    @staticmethod
    def _calculate_joint_hash(spouse1_id, spouse2_id):
        """
        Calculate combined hash from both spouses' individual hashes.
        If either spouse's data changes, joint hash changes.

        Returns:
            str: SHA-256 hash combining both spouse hashes
        """
        spouse1_hash = AnalysisEngine._calculate_data_version_hash(spouse1_id)
        spouse2_hash = AnalysisEngine._calculate_data_version_hash(spouse2_id)

        # Combine in consistent order (lower ID first for symmetry)
        ordered_ids = sorted([spouse1_id, spouse2_id])
        combined_string = f"{spouse1_hash}|{spouse2_hash}|{ordered_ids[0]}|{ordered_ids[1]}"

        return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()

    @staticmethod
    def _identify_credit_type(strategy_name):
        """
        Map strategy name to credit eligibility key.

        Returns:
            str or None: Credit type key, or None if not a restricted credit
        """
        name_lower = strategy_name.lower()

        if 'eitc' in name_lower or 'earned income' in name_lower:
            return 'EITC'
        elif 'student loan' in name_lower:
            return 'student_loan_interest'
        elif 'education credit' in name_lower or 'american opportunity' in name_lower or 'lifetime learning' in name_lower:
            return 'education_credits'
        elif 'adoption' in name_lower:
            return 'adoption_credit'
        return None

    @staticmethod
    def _filter_strategies_by_filing_status(strategies, filing_status):
        """
        Remove strategies ineligible for filing status (REQ-05).

        Args:
            strategies: List of AnalysisResult objects
            filing_status: Filing status string

        Returns:
            tuple: (filtered_strategies, removed_credit_names)
        """
        filtered = []
        removed = []

        for strategy in strategies:
            credit_type = JointAnalysisService._identify_credit_type(strategy.strategy_name)

            if credit_type and credit_type in JointAnalysisService.CREDIT_ELIGIBILITY:
                eligible = JointAnalysisService.CREDIT_ELIGIBILITY[credit_type].get(filing_status, False)
                if eligible:
                    filtered.append(strategy)
                else:
                    removed.append(strategy.strategy_name)
            else:
                filtered.append(strategy)

        return filtered, removed

    @staticmethod
    def _check_qbi_impact(income, filing_status, tax_year=2026):
        """
        Check if income exceeds QBI threshold for filing status (REQ-06).

        MFS uses $197,300 threshold (same as single), not $383,900 (MFJ).

        Returns:
            dict: {'exceeds_threshold': bool, 'threshold': float, 'note': str or None}
        """
        try:
            threshold = TaxCalculator.get_qbi_income_thresholds(
                filing_status=filing_status,
                tax_year=tax_year
            )
            # get_qbi_income_thresholds returns a float directly
            if isinstance(threshold, dict):
                threshold = threshold.get('phase_out_start', 0)
        except (AttributeError, TypeError):
            threshold_map = {
                'single': 197300,
                'married_joint': 394600,
                'married_separate': 197300,
                'head_of_household': 197300
            }
            threshold = threshold_map.get(filing_status, 197300)

        exceeds = income > threshold

        note = None
        if exceeds:
            note = f"Income ${income:,.0f} exceeds QBI threshold (${threshold:,.0f}) — QBI deduction may be limited"

        return {
            'exceeds_threshold': exceeds,
            'threshold': threshold,
            'note': note
        }

    @staticmethod
    def validate_deduction_method_change(client_id, new_method):
        """
        Validate deduction method change for MFS coordination (REQ-09).

        IRS rule: if one MFS spouse itemizes, both must itemize.

        Returns:
            dict: {allowed, message, action, required_method (if blocked), cascade_to_spouse (if cascade)}
        """
        client = Client.query.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        if client.filing_status != 'married_separate':
            return {'allowed': True, 'message': 'No coordination required', 'action': 'allow'}

        if not client.spouse_id:
            return {'allowed': True, 'message': 'No spouse linked', 'action': 'allow'}

        spouse = Client.query.get(client.spouse_id)
        if not spouse:
            return {'allowed': True, 'message': 'Spouse not found', 'action': 'allow'}

        # If spouse is itemizing and client wants standard, block
        if spouse.deduction_method == 'itemized' and new_method == 'standard':
            return {
                'allowed': False,
                'message': 'Cannot use standard deduction - spouse is itemizing. '
                           'Both spouses must use the same deduction method when filing separately.',
                'action': 'block',
                'required_method': 'itemized'
            }

        # If client wants to itemize and spouse is on standard, warn about cascade
        if new_method == 'itemized' and spouse.deduction_method == 'standard':
            return {
                'allowed': True,
                'message': 'Changing to itemized deductions will require spouse to also itemize.',
                'action': 'confirm_cascade',
                'cascade_to_spouse': True
            }

        return {'allowed': True, 'message': 'Coordination satisfied', 'action': 'allow'}

    @staticmethod
    def check_mfs_deduction_coordination(spouse1_id, spouse2_id):
        """
        Verify both MFS spouses use the same deduction method (REQ-09).

        Called during joint analysis to ensure coordination before calculation.

        Returns:
            dict: {valid, spouse1_method, spouse2_method, error}
        """
        spouse1 = Client.query.get(spouse1_id)
        spouse2 = Client.query.get(spouse2_id)

        if not spouse1 or not spouse2:
            return {
                'valid': False,
                'spouse1_method': None,
                'spouse2_method': None,
                'error': 'One or both spouses not found'
            }

        # Coordination only applies to MFS
        if spouse1.filing_status != 'married_separate' or spouse2.filing_status != 'married_separate':
            # MFJ doesn't require coordination -- both use same return
            return {
                'valid': True,
                'spouse1_method': getattr(spouse1, 'deduction_method', 'standard'),
                'spouse2_method': getattr(spouse2, 'deduction_method', 'standard'),
                'error': None
            }

        spouse1_method = getattr(spouse1, 'deduction_method', 'standard')
        spouse2_method = getattr(spouse2, 'deduction_method', 'standard')

        if spouse1_method != spouse2_method:
            return {
                'valid': False,
                'spouse1_method': spouse1_method,
                'spouse2_method': spouse2_method,
                'error': 'IRS requires both spouses to use the same deduction method '
                         '(standard or itemized) when filing separately'
            }

        return {
            'valid': True,
            'spouse1_method': spouse1_method,
            'spouse2_method': spouse2_method,
            'error': None
        }

    @staticmethod
    def _format_cached_result(cached, spouse1_id, spouse2_id):
        """Format cached JointAnalysisSummary into return structure"""
        spouse1_strategies, spouse1_summary = AnalysisEngine.analyze_client(spouse1_id)
        spouse2_strategies, spouse2_summary = AnalysisEngine.analyze_client(spouse2_id)

        notes_list = []
        if cached.comparison_notes:
            try:
                notes_list = json.loads(cached.comparison_notes)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            'spouse1': {
                'summary': spouse1_summary,
                'strategies': [s.to_dict() for s in spouse1_strategies]
            },
            'spouse2': {
                'summary': spouse2_summary,
                'strategies': [s.to_dict() for s in spouse2_strategies]
            },
            'mfj': {
                'combined_income': cached.mfj_combined_income,
                'agi': cached.mfj_agi,
                'standard_deduction': cached.mfj_standard_deduction,
                'taxable_income': cached.mfj_taxable_income,
                'total_tax': cached.mfj_total_tax,
                'effective_rate': cached.mfj_effective_rate,
            },
            'mfs_spouse1': {
                'income': cached.mfs_spouse1_income,
                'agi': cached.mfs_spouse1_agi,
                'standard_deduction': cached.mfs_standard_deduction,
                'taxable_income': cached.mfs_spouse1_taxable_income,
                'total_tax': cached.mfs_spouse1_tax,
                'effective_rate': (cached.mfs_spouse1_tax / cached.mfs_spouse1_income * 100) if cached.mfs_spouse1_income > 0 else 0,
            },
            'mfs_spouse2': {
                'income': cached.mfs_spouse2_income,
                'agi': cached.mfs_spouse2_agi,
                'standard_deduction': cached.mfs_standard_deduction,
                'taxable_income': cached.mfs_spouse2_taxable_income,
                'total_tax': cached.mfs_spouse2_tax,
                'effective_rate': (cached.mfs_spouse2_tax / cached.mfs_spouse2_income * 100) if cached.mfs_spouse2_income > 0 else 0,
            },
            'comparison': {
                'recommended_status': cached.recommended_status,
                'savings_amount': cached.savings_amount,
                'mfj_total_tax': cached.mfj_total_tax,
                'mfs_total_tax': cached.mfs_combined_tax,
                'reason': f"{cached.recommended_status} saves ${cached.savings_amount:,.2f}",
                'notes': notes_list,
            }
        }

    @staticmethod
    def analyze_joint(spouse1_id, spouse2_id, force_refresh=False):
        """
        Orchestrate joint analysis: MFJ scenario, MFS scenario, comparison.

        Args:
            spouse1_id: First spouse client ID
            spouse2_id: Second spouse client ID
            force_refresh: Skip cache and recalculate

        Returns:
            dict with keys: spouse1, spouse2, mfj, mfs_spouse1, mfs_spouse2, comparison
        """
        # Step 1: Validate spouses are linked
        spouse1 = Client.query.get(spouse1_id)
        spouse2 = Client.query.get(spouse2_id)

        if not spouse1 or not spouse2:
            raise ValueError("Both spouse IDs must be valid")

        if spouse1.spouse_id != spouse2_id or spouse2.spouse_id != spouse1_id:
            raise ValueError("Clients must be linked as spouses")

        # Validate filing statuses
        for spouse, label in [(spouse1, 'Spouse 1'), (spouse2, 'Spouse 2')]:
            if spouse.filing_status not in ['married_joint', 'married_separate']:
                raise ValueError(
                    f"{label} filing status must be married_joint or married_separate, "
                    f"got: {spouse.filing_status}"
                )

        # REQ-09: Check deduction method coordination for MFS
        coordination = JointAnalysisService.check_mfs_deduction_coordination(spouse1_id, spouse2_id)
        if not coordination['valid']:
            raise ValueError(f"Deduction coordination error: {coordination['error']}")

        deduction_method = coordination['spouse1_method']  # Same for both (coordination enforced)

        # Step 2: Calculate combined hash
        joint_hash = JointAnalysisService._calculate_joint_hash(spouse1_id, spouse2_id)

        # Step 3: Check cache
        cached = JointAnalysisSummary.query.filter_by(
            spouse1_id=spouse1_id,
            spouse2_id=spouse2_id
        ).first()

        if cached and cached.data_version_hash == joint_hash and not force_refresh:
            return JointAnalysisService._format_cached_result(cached, spouse1_id, spouse2_id)

        # Step 4: Analyze each spouse individually
        spouse1_strategies, spouse1_summary = AnalysisEngine.analyze_client(spouse1_id)
        spouse2_strategies, spouse2_summary = AnalysisEngine.analyze_client(spouse2_id)

        # Step 5: Calculate MFJ scenario (REQ-01, REQ-07)
        tax_year = spouse1_summary.get('tax_year') or 2026
        spouse1_income = spouse1_summary.get('total_income', 0)
        spouse2_income = spouse2_summary.get('total_income', 0)
        combined_income = spouse1_income + spouse2_income

        mfj_std_deduction = TaxCalculator.get_standard_deduction(
            filing_status='married_joint',
            tax_type='federal',
            tax_year=tax_year
        )

        # Determine MFJ deduction (standard or itemized)
        if deduction_method == 'itemized':
            # Calculate combined itemized deductions for MFJ
            spouse1_itemized = ItemizedDeductionService.calculate_itemized_deductions(spouse1_id, tax_year)
            spouse2_itemized = ItemizedDeductionService.calculate_itemized_deductions(spouse2_id, tax_year)

            # Combine raw amounts and recalculate with MFJ SALT cap
            combined_salt_raw = (spouse1_itemized['breakdown']['state_local_taxes']['raw'] +
                                 spouse2_itemized['breakdown']['state_local_taxes']['raw'])
            combined_medical_raw = (spouse1_itemized['breakdown']['medical_expenses']['raw'] +
                                    spouse2_itemized['breakdown']['medical_expenses']['raw'])
            combined_mortgage = (spouse1_itemized['breakdown']['mortgage_interest'] +
                                 spouse2_itemized['breakdown']['mortgage_interest'])
            combined_charitable = (spouse1_itemized['breakdown']['charitable_contributions'] +
                                   spouse2_itemized['breakdown']['charitable_contributions'])

            # Apply MFJ SALT cap ($40,400) to combined SALT
            mfj_salt = ItemizedDeductionService.calculate_salt_deduction(
                state_local_taxes=combined_salt_raw,
                filing_status='married_joint',
                magi=combined_income,
                tax_year=tax_year
            )

            # Medical threshold uses combined AGI for MFJ
            medical_threshold = combined_income * 0.075
            medical_deductible = max(0, combined_medical_raw - medical_threshold)

            mfj_itemized_total = round(
                medical_deductible +
                mfj_salt['deduction_allowed'] +
                combined_mortgage +
                combined_charitable,
                2
            )

            mfj_deduction = max(mfj_itemized_total, mfj_std_deduction)
        else:
            mfj_deduction = mfj_std_deduction

        mfj_taxable = TaxCalculator.calculate_taxable_income(
            gross_income=combined_income,
            standard_deduction=mfj_deduction
        )

        mfj_brackets = TaxCalculator.get_tax_brackets(
            tax_type='federal',
            filing_status='married_joint',
            tax_year=tax_year
        )

        mfj_tax_result = TaxCalculator.calculate_tax_by_brackets(
            taxable_income=mfj_taxable,
            brackets=mfj_brackets
        )

        mfj_result = {
            'combined_income': combined_income,
            'agi': combined_income,
            'standard_deduction': mfj_deduction,
            'taxable_income': mfj_taxable,
            'total_tax': mfj_tax_result['total_tax'],
            'marginal_rate': mfj_tax_result['marginal_rate'],
            'effective_rate': (mfj_tax_result['total_tax'] / combined_income * 100) if combined_income > 0 else 0
        }

        # Step 6: Calculate MFS scenario (REQ-02, REQ-07, REQ-09, REQ-10)
        mfs_std_deduction = TaxCalculator.get_standard_deduction(
            filing_status='married_separate',
            tax_type='federal',
            tax_year=tax_year
        )

        mfs_brackets = TaxCalculator.get_tax_brackets(
            tax_type='federal',
            filing_status='married_separate',
            tax_year=tax_year
        )

        # Determine MFS deductions per spouse (standard or itemized)
        if deduction_method == 'itemized':
            # Each spouse calculates itemized separately with MFS SALT cap ($20k each)
            spouse1_itemized_result = ItemizedDeductionService.calculate_itemized_deductions(spouse1_id, tax_year)
            mfs_spouse1_deduction = spouse1_itemized_result['itemized_total']

            spouse2_itemized_result = ItemizedDeductionService.calculate_itemized_deductions(spouse2_id, tax_year)
            mfs_spouse2_deduction = spouse2_itemized_result['itemized_total']
        else:
            mfs_spouse1_deduction = mfs_std_deduction
            mfs_spouse2_deduction = mfs_std_deduction

        # Spouse 1 MFS
        mfs_spouse1_taxable = TaxCalculator.calculate_taxable_income(
            gross_income=spouse1_income,
            standard_deduction=mfs_spouse1_deduction
        )
        mfs_spouse1_tax_result = TaxCalculator.calculate_tax_by_brackets(
            taxable_income=mfs_spouse1_taxable,
            brackets=mfs_brackets
        )

        mfs_spouse1_result = {
            'income': spouse1_income,
            'agi': spouse1_income,
            'standard_deduction': mfs_spouse1_deduction,
            'taxable_income': mfs_spouse1_taxable,
            'total_tax': mfs_spouse1_tax_result['total_tax'],
            'marginal_rate': mfs_spouse1_tax_result['marginal_rate'],
            'effective_rate': (mfs_spouse1_tax_result['total_tax'] / spouse1_income * 100) if spouse1_income > 0 else 0
        }

        # Spouse 2 MFS
        mfs_spouse2_taxable = TaxCalculator.calculate_taxable_income(
            gross_income=spouse2_income,
            standard_deduction=mfs_spouse2_deduction
        )
        mfs_spouse2_tax_result = TaxCalculator.calculate_tax_by_brackets(
            taxable_income=mfs_spouse2_taxable,
            brackets=mfs_brackets
        )

        mfs_spouse2_result = {
            'income': spouse2_income,
            'agi': spouse2_income,
            'standard_deduction': mfs_spouse2_deduction,
            'taxable_income': mfs_spouse2_taxable,
            'total_tax': mfs_spouse2_tax_result['total_tax'],
            'marginal_rate': mfs_spouse2_tax_result['marginal_rate'],
            'effective_rate': (mfs_spouse2_tax_result['total_tax'] / spouse2_income * 100) if spouse2_income > 0 else 0
        }

        mfs_combined_tax = mfs_spouse1_result['total_tax'] + mfs_spouse2_result['total_tax']

        # Step 6b: Filter strategies for MFS (REQ-05)
        mfs_spouse1_strategies, removed_spouse1 = JointAnalysisService._filter_strategies_by_filing_status(
            spouse1_strategies, 'married_separate'
        )
        mfs_spouse2_strategies, removed_spouse2 = JointAnalysisService._filter_strategies_by_filing_status(
            spouse2_strategies, 'married_separate'
        )
        removed_credits = list(set(removed_spouse1 + removed_spouse2))

        # Step 6c: Check QBI impact (REQ-06)
        qbi_spouse1 = JointAnalysisService._check_qbi_impact(
            income=spouse1_income, filing_status='married_separate', tax_year=tax_year
        )
        qbi_spouse2 = JointAnalysisService._check_qbi_impact(
            income=spouse2_income, filing_status='married_separate', tax_year=tax_year
        )
        qbi_mfj = JointAnalysisService._check_qbi_impact(
            income=combined_income, filing_status='married_joint', tax_year=tax_year
        )

        # Step 7: Generate comparison and recommendation (REQ-03)
        savings = mfs_combined_tax - mfj_result['total_tax']
        recommended_status = 'MFJ' if savings > 0 else 'MFS'

        comparison_notes = []
        if removed_credits:
            comparison_notes.append({
                'type': 'credit_restriction',
                'message': f"MFS ineligible for: {', '.join(removed_credits)}",
                'impact': 'MFS tax may be higher due to unavailable credits'
            })

        if qbi_spouse1['exceeds_threshold'] and not qbi_mfj['exceeds_threshold']:
            comparison_notes.append({
                'type': 'qbi_threshold',
                'message': f"Spouse 1 exceeds MFS QBI threshold (${qbi_spouse1['threshold']:,.0f}), but combined income under MFJ threshold (${qbi_mfj['threshold']:,.0f})",
                'impact': 'MFJ may preserve full QBI deduction'
            })

        if qbi_spouse2['exceeds_threshold'] and not qbi_mfj['exceeds_threshold']:
            comparison_notes.append({
                'type': 'qbi_threshold',
                'message': f"Spouse 2 exceeds MFS QBI threshold (${qbi_spouse2['threshold']:,.0f}), but combined income under MFJ threshold (${qbi_mfj['threshold']:,.0f})",
                'impact': 'MFJ may preserve full QBI deduction'
            })

        # REQ-09/REQ-10: Add itemized deduction notes
        if deduction_method == 'itemized':
            comparison_notes.append({
                'type': 'deduction_coordination',
                'message': 'Both spouses itemizing (IRS requirement for MFS)',
                'impact': f'MFJ deduction: ${mfj_deduction:,.2f} | MFS: ${mfs_spouse1_deduction:,.2f} + ${mfs_spouse2_deduction:,.2f}'
            })
            comparison_notes.append({
                'type': 'salt_cap_difference',
                'message': 'SALT cap differs by filing status (2026 OBBBA)',
                'impact': 'MFJ cap: $40,400 | MFS cap: $20,000 per spouse'
            })

        comparison = {
            'recommended_status': recommended_status,
            'savings_amount': abs(savings),
            'mfj_total_tax': mfj_result['total_tax'],
            'mfs_total_tax': mfs_combined_tax,
            'reason': f"{'MFJ' if savings > 0 else 'MFS'} saves ${abs(savings):,.2f}",
            'notes': comparison_notes,
        }

        # Step 8: Store result in cache
        if cached:
            cached.tax_year = tax_year
            cached.mfj_combined_income = mfj_result['combined_income']
            cached.mfj_agi = mfj_result['agi']
            cached.mfj_taxable_income = mfj_result['taxable_income']
            cached.mfj_total_tax = mfj_result['total_tax']
            cached.mfj_effective_rate = mfj_result['effective_rate']
            cached.mfj_standard_deduction = mfj_result['standard_deduction']
            cached.mfs_spouse1_income = mfs_spouse1_result['income']
            cached.mfs_spouse1_agi = mfs_spouse1_result['agi']
            cached.mfs_spouse1_taxable_income = mfs_spouse1_result['taxable_income']
            cached.mfs_spouse1_tax = mfs_spouse1_result['total_tax']
            cached.mfs_spouse2_income = mfs_spouse2_result['income']
            cached.mfs_spouse2_agi = mfs_spouse2_result['agi']
            cached.mfs_spouse2_taxable_income = mfs_spouse2_result['taxable_income']
            cached.mfs_spouse2_tax = mfs_spouse2_result['total_tax']
            cached.mfs_combined_tax = mfs_combined_tax
            cached.mfs_effective_rate = (mfs_combined_tax / combined_income * 100) if combined_income > 0 else 0
            cached.mfs_standard_deduction = mfs_spouse1_deduction
            cached.recommended_status = recommended_status
            cached.savings_amount = abs(savings)
            cached.comparison_notes = json.dumps(comparison_notes)
            cached.data_version_hash = joint_hash
            cached.last_analyzed_at = datetime.utcnow()
        else:
            cached = JointAnalysisSummary(
                spouse1_id=spouse1_id,
                spouse2_id=spouse2_id,
                tax_year=tax_year,
                mfj_combined_income=mfj_result['combined_income'],
                mfj_agi=mfj_result['agi'],
                mfj_taxable_income=mfj_result['taxable_income'],
                mfj_total_tax=mfj_result['total_tax'],
                mfj_effective_rate=mfj_result['effective_rate'],
                mfj_standard_deduction=mfj_result['standard_deduction'],
                mfs_spouse1_income=mfs_spouse1_result['income'],
                mfs_spouse1_agi=mfs_spouse1_result['agi'],
                mfs_spouse1_taxable_income=mfs_spouse1_result['taxable_income'],
                mfs_spouse1_tax=mfs_spouse1_result['total_tax'],
                mfs_spouse2_income=mfs_spouse2_result['income'],
                mfs_spouse2_agi=mfs_spouse2_result['agi'],
                mfs_spouse2_taxable_income=mfs_spouse2_result['taxable_income'],
                mfs_spouse2_tax=mfs_spouse2_result['total_tax'],
                mfs_combined_tax=mfs_combined_tax,
                mfs_effective_rate=(mfs_combined_tax / combined_income * 100) if combined_income > 0 else 0,
                mfs_standard_deduction=mfs_spouse1_deduction,
                recommended_status=recommended_status,
                savings_amount=abs(savings),
                comparison_notes=json.dumps(comparison_notes),
                data_version_hash=joint_hash,
            )
            db.session.add(cached)

        db.session.commit()

        # Step 9: Return structured result
        return {
            'spouse1': {
                'summary': spouse1_summary,
                'strategies': [s.to_dict() for s in spouse1_strategies]
            },
            'spouse2': {
                'summary': spouse2_summary,
                'strategies': [s.to_dict() for s in spouse2_strategies]
            },
            'mfj': mfj_result,
            'mfs_spouse1': mfs_spouse1_result,
            'mfs_spouse2': mfs_spouse2_result,
            'comparison': comparison,
        }

    @staticmethod
    def get_comparison_summary(spouse1_id, spouse2_id):
        """
        Get concise comparison summary (for testing/debugging).

        Returns:
            dict: {mfj_tax, mfs_tax, recommended, savings}
        """
        result = JointAnalysisService.analyze_joint(spouse1_id, spouse2_id)
        return {
            'mfj_tax': result['mfj']['total_tax'],
            'mfs_tax': result['comparison']['mfs_total_tax'],
            'recommended': result['comparison']['recommended_status'],
            'savings': result['comparison']['savings_amount']
        }
