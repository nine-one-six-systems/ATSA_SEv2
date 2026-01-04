from models import db
from datetime import datetime

class ExtractedData(db.Model):
    __tablename__ = 'extracted_data'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    form_type = db.Column(db.Text, nullable=False)  # 1040, W2, 1099-INT, etc.
    field_name = db.Column(db.Text, nullable=False)
    field_value = db.Column(db.Text, nullable=True)
    extracted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'client_id': self.client_id,
            'form_type': self.form_type,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None
        }

