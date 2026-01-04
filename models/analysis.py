from models import db
from datetime import datetime

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'strategy_name': self.strategy_name,
            'strategy_description': self.strategy_description,
            'potential_savings': self.potential_savings,
            'irs_section': self.irs_section,
            'irs_code': self.irs_code,
            'irs_url': self.irs_url,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

