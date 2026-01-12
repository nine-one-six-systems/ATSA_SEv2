from models import db
from datetime import datetime

class TaxBracket(db.Model):
    """Stores federal and state tax brackets"""
    __tablename__ = 'tax_brackets'
    
    id = db.Column(db.Integer, primary_key=True)
    tax_type = db.Column(db.String(20), nullable=False)  # 'federal' or 'state'
    state_code = db.Column(db.String(2), nullable=True)  # 2-letter state code, null for federal
    filing_status = db.Column(db.String(30), nullable=False)  # single, married_joint, married_separate, head_of_household, qualifying_surviving_spouse
    bracket_min = db.Column(db.Float, nullable=False)  # Minimum income for this bracket
    bracket_max = db.Column(db.Float, nullable=True)  # Maximum income (null for top bracket)
    tax_rate = db.Column(db.Float, nullable=False)  # Tax rate as decimal (e.g., 0.22 for 22%)
    tax_year = db.Column(db.Integer, nullable=False, default=2024)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        db.Index('idx_tax_bracket_lookup', 'tax_type', 'state_code', 'filing_status', 'tax_year'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'tax_type': self.tax_type,
            'state_code': self.state_code,
            'filing_status': self.filing_status,
            'bracket_min': self.bracket_min,
            'bracket_max': self.bracket_max,
            'tax_rate': self.tax_rate,
            'tax_year': self.tax_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StandardDeduction(db.Model):
    """Stores federal and state standard deductions"""
    __tablename__ = 'standard_deductions'
    
    id = db.Column(db.Integer, primary_key=True)
    tax_type = db.Column(db.String(20), nullable=False)  # 'federal' or 'state'
    state_code = db.Column(db.String(2), nullable=True)  # 2-letter state code, null for federal
    filing_status = db.Column(db.String(30), nullable=False)  # single, married_joint, married_separate, head_of_household, qualifying_surviving_spouse
    deduction_amount = db.Column(db.Float, nullable=False)  # Standard deduction amount
    tax_year = db.Column(db.Integer, nullable=False, default=2024)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        db.Index('idx_standard_deduction_lookup', 'tax_type', 'state_code', 'filing_status', 'tax_year'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'tax_type': self.tax_type,
            'state_code': self.state_code,
            'filing_status': self.filing_status,
            'deduction_amount': self.deduction_amount,
            'tax_year': self.tax_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
