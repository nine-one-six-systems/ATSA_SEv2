from models import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    filename = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_type = db.Column(db.Text, nullable=False)  # pdf, jpg, png
    tax_year = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_status = db.Column(db.Text, default='pending')  # pending, processing, completed, failed
    attribution = db.Column(db.Text, default='taxpayer', nullable=False)  # 'taxpayer', 'spouse', 'joint'

    # Relationships
    extracted_data = db.relationship('ExtractedData', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'tax_year': self.tax_year,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'ocr_status': self.ocr_status,
            'attribution': self.attribution
        }

