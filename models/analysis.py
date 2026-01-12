from models import db
from datetime import datetime
import json
import hashlib

class AnalysisSummary(db.Model):
    __tablename__ = 'analysis_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, unique=True)
    tax_year = db.Column(db.Integer, nullable=True)
    total_income = db.Column(db.Float, default=0)
    adjusted_gross_income = db.Column(db.Float, default=0)
    taxable_income = db.Column(db.Float, default=0)
    total_tax = db.Column(db.Float, default=0)
    tax_withheld = db.Column(db.Float, default=0)
    tax_owed = db.Column(db.Float, default=0)
    tax_refund = db.Column(db.Float, default=0)
    effective_tax_rate = db.Column(db.Float, default=0)
    marginal_tax_rate = db.Column(db.Integer, default=0)
    income_sources = db.Column(db.Text)  # JSON array
    data_version_hash = db.Column(db.String(64))  # SHA-256 hash
    last_analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        income_sources_list = []
        if self.income_sources:
            try:
                income_sources_list = json.loads(self.income_sources)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            'id': self.id,
            'client_id': self.client_id,
            'tax_year': self.tax_year,
            'total_income': self.total_income,
            'adjusted_gross_income': self.adjusted_gross_income,
            'taxable_income': self.taxable_income,
            'total_tax': self.total_tax,
            'tax_withheld': self.tax_withheld,
            'tax_owed': self.tax_owed,
            'tax_refund': self.tax_refund,
            'effective_tax_rate': self.effective_tax_rate,
            'marginal_tax_rate': self.marginal_tax_rate,
            'income_sources': income_sources_list,
            'data_version_hash': self.data_version_hash,
            'last_analyzed_at': self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    strategy_name = db.Column(db.Text, nullable=False)
    strategy_description = db.Column(db.Text, nullable=False)
    potential_savings = db.Column(db.Float, nullable=True)
    irs_section = db.Column(db.Text, nullable=False)
    irs_code = db.Column(db.Text, nullable=True)
    irs_url = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Integer, default=3)  # 1-5, 1 being highest priority
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_detailed_info(self):
        """Parse detailed strategy information from strategy_description JSON"""
        try:
            return json.loads(self.strategy_description)
        except (json.JSONDecodeError, TypeError):
            # Fallback for old format or non-JSON descriptions
            return {
                'status': 'UNKNOWN',
                'current_benefit': 0,
                'potential_benefit': self.potential_savings or 0,
                'unused_capacity': 0,
                'flags': [],
                'recommendations': [],
                'forms_analyzed': []
            }
    
    def to_dict(self):
        """Convert to dictionary with detailed information"""
        detailed_info = self.get_detailed_info()
        
        result = {
            'id': self.id,
            'client_id': self.client_id,
            'strategy_name': self.strategy_name,
            'strategy_description': self.strategy_description,
            'potential_savings': self.potential_savings,
            'irs_section': self.irs_section,
            'irs_code': self.irs_code,
            'irs_url': self.irs_url,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Detailed information
            'strategy_id': detailed_info.get('strategy_id', ''),
            'status': detailed_info.get('status', 'UNKNOWN'),
            'current_benefit': detailed_info.get('current_benefit', 0),
            'potential_benefit': detailed_info.get('potential_benefit', self.potential_savings or 0),
            'unused_capacity': detailed_info.get('unused_capacity', 0),
            'flags': detailed_info.get('flags', []),
            'recommendations': detailed_info.get('recommendations', []),
            'forms_analyzed': detailed_info.get('forms_analyzed', [])
        }
        
        return result

