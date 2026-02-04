from models import db
from datetime import datetime
import json


class JointAnalysisSummary(db.Model):
    __tablename__ = 'joint_analysis_summaries'

    id = db.Column(db.Integer, primary_key=True)
    spouse1_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    spouse2_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=True)

    # MFJ scenario
    mfj_combined_income = db.Column(db.Float, default=0)
    mfj_agi = db.Column(db.Float, default=0)
    mfj_taxable_income = db.Column(db.Float, default=0)
    mfj_total_tax = db.Column(db.Float, default=0)
    mfj_effective_rate = db.Column(db.Float, default=0)
    mfj_standard_deduction = db.Column(db.Float, default=0)

    # MFS scenario - spouse 1
    mfs_spouse1_income = db.Column(db.Float, default=0)
    mfs_spouse1_agi = db.Column(db.Float, default=0)
    mfs_spouse1_taxable_income = db.Column(db.Float, default=0)
    mfs_spouse1_tax = db.Column(db.Float, default=0)

    # MFS scenario - spouse 2
    mfs_spouse2_income = db.Column(db.Float, default=0)
    mfs_spouse2_agi = db.Column(db.Float, default=0)
    mfs_spouse2_taxable_income = db.Column(db.Float, default=0)
    mfs_spouse2_tax = db.Column(db.Float, default=0)

    # MFS combined
    mfs_combined_tax = db.Column(db.Float, default=0)
    mfs_effective_rate = db.Column(db.Float, default=0)
    mfs_standard_deduction = db.Column(db.Float, default=0)

    # Comparison
    recommended_status = db.Column(db.String(20))  # 'MFJ' or 'MFS'
    savings_amount = db.Column(db.Float, default=0)  # Positive = recommended saves money
    comparison_notes = db.Column(db.Text, nullable=True)  # JSON array of notes

    # Caching
    data_version_hash = db.Column(db.String(64))  # Combined hash from both spouses
    last_analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('spouse1_id', 'spouse2_id', name='unique_spouse_pair'),
    )

    def to_dict(self):
        """Convert to nested dictionary for API response"""
        notes_list = []
        if self.comparison_notes:
            try:
                notes_list = json.loads(self.comparison_notes)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            'id': self.id,
            'spouse1_id': self.spouse1_id,
            'spouse2_id': self.spouse2_id,
            'tax_year': self.tax_year,
            'mfj': {
                'combined_income': self.mfj_combined_income,
                'agi': self.mfj_agi,
                'taxable_income': self.mfj_taxable_income,
                'total_tax': self.mfj_total_tax,
                'effective_rate': self.mfj_effective_rate,
                'standard_deduction': self.mfj_standard_deduction,
            },
            'mfs': {
                'spouse1': {
                    'income': self.mfs_spouse1_income,
                    'agi': self.mfs_spouse1_agi,
                    'taxable_income': self.mfs_spouse1_taxable_income,
                    'tax': self.mfs_spouse1_tax,
                },
                'spouse2': {
                    'income': self.mfs_spouse2_income,
                    'agi': self.mfs_spouse2_agi,
                    'taxable_income': self.mfs_spouse2_taxable_income,
                    'tax': self.mfs_spouse2_tax,
                },
                'combined_tax': self.mfs_combined_tax,
                'effective_rate': self.mfs_effective_rate,
                'standard_deduction': self.mfs_standard_deduction,
            },
            'comparison': {
                'recommended_status': self.recommended_status,
                'savings_amount': self.savings_amount,
                'notes': notes_list,
            },
            'data_version_hash': self.data_version_hash,
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
