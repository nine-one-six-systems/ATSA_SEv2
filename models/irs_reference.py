from models import db
import json

class IRSReference(db.Model):
    __tablename__ = 'irs_references'
    
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.Text, nullable=False)  # e.g., "IRC Section 179"
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=True)
    applicable_forms = db.Column(db.Text, nullable=True)  # JSON array
    
    def get_applicable_forms(self):
        """Parse applicable_forms JSON string to list"""
        if self.applicable_forms:
            try:
                return json.loads(self.applicable_forms)
            except:
                return []
        return []
    
    def set_applicable_forms(self, forms_list):
        """Set applicable_forms as JSON string"""
        self.applicable_forms = json.dumps(forms_list) if forms_list else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'section': self.section,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'applicable_forms': self.get_applicable_forms()
        }

