from models import db
from datetime import datetime
import json


class ItemizedDeduction(db.Model):
    """
    Stores itemized deduction data (Schedule A) per client per tax year.

    Used for MFS compliance (REQ-09, REQ-10, REQ-11):
    - Tracks raw amounts before caps/thresholds
    - Stores allocation metadata for shared expenses between spouses
    - Enables SALT cap enforcement by filing status
    """
    __tablename__ = 'itemized_deductions'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)

    # Schedule A categories (raw amounts before caps/thresholds)
    medical_expenses = db.Column(db.Float, default=0)
    state_local_taxes = db.Column(db.Float, default=0)  # Before SALT cap
    mortgage_interest = db.Column(db.Float, default=0)
    charitable_contributions = db.Column(db.Float, default=0)

    # Allocation metadata for shared expenses (JSON)
    # Example: {"mortgage_interest": {"method": "both", "taxpayer_pct": 60, "spouse_pct": 40},
    #           "state_local_taxes": {"method": "joint", "taxpayer_pct": 50, "spouse_pct": 50}}
    allocation_metadata = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship('Client', backref=db.backref('itemized_deductions', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('client_id', 'tax_year', name='unique_client_year_itemized'),
    )

    def get_allocation(self, expense_type):
        """Parse allocation metadata for a specific expense type."""
        if not self.allocation_metadata:
            return {'method': 'joint', 'taxpayer_pct': 50, 'spouse_pct': 50}
        try:
            metadata = json.loads(self.allocation_metadata)
            return metadata.get(expense_type, {'method': 'joint', 'taxpayer_pct': 50, 'spouse_pct': 50})
        except (json.JSONDecodeError, TypeError):
            return {'method': 'joint', 'taxpayer_pct': 50, 'spouse_pct': 50}

    def to_dict(self):
        allocation = None
        if self.allocation_metadata:
            try:
                allocation = json.loads(self.allocation_metadata)
            except (json.JSONDecodeError, TypeError):
                allocation = None

        return {
            'id': self.id,
            'client_id': self.client_id,
            'tax_year': self.tax_year,
            'medical_expenses': self.medical_expenses,
            'state_local_taxes': self.state_local_taxes,
            'mortgage_interest': self.mortgage_interest,
            'charitable_contributions': self.charitable_contributions,
            'allocation_metadata': allocation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
