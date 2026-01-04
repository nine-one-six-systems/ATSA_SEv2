from models import db
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib
import os

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    ssn = db.Column(db.Text, nullable=True)  # Encrypted
    filing_status = db.Column(db.Text, nullable=False)  # single, married_joint, married_separate, head_of_household
    email = db.Column(db.Text, nullable=True)
    phone = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    spouse_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    spouse = db.relationship('Client', remote_side=[id], backref='linked_spouse')
    documents = db.relationship('Document', backref='client', lazy=True, cascade='all, delete-orphan')
    extracted_data = db.relationship('ExtractedData', backref='client', lazy=True, cascade='all, delete-orphan')
    analyses = db.relationship('AnalysisResult', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        ssn_value = kwargs.pop('ssn', None)
        super(Client, self).__init__(**kwargs)
        if ssn_value:
            self.ssn = self._encrypt_ssn(ssn_value)
    
    def _get_encryption_key(self):
        """Get or create encryption key for SSN"""
        key_env = os.environ.get('SSN_ENCRYPTION_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        # For development, use a default key (should be changed in production)
        key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        return hashlib.sha256(key.encode()).digest()[:32]
    
    def _encrypt_ssn(self, ssn):
        """Encrypt SSN before storing"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(base64.urlsafe_b64encode(key))
            return fernet.encrypt(ssn.encode()).decode()
        except Exception:
            # Fallback to hashing if encryption fails
            return hashlib.sha256(ssn.encode()).hexdigest()
    
    def get_ssn(self):
        """Decrypt SSN for display (use with caution)"""
        if not self.ssn:
            return None
        try:
            key = self._get_encryption_key()
            fernet = Fernet(base64.urlsafe_b64encode(key))
            return fernet.decrypt(self.ssn.encode()).decode()
        except Exception:
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'filing_status': self.filing_status,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'spouse_id': self.spouse_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

