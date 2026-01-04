from models import db, IRSReference

class IRSReferenceService:
    """Service for managing IRS code references"""
    
    @staticmethod
    def get_reference_by_section(section):
        """Get IRS reference by section name"""
        return IRSReference.query.filter_by(section=section).first()
    
    @staticmethod
    def get_all_references():
        """Get all IRS references"""
        return IRSReference.query.all()
    
    @staticmethod
    def get_references_for_forms(form_types):
        """Get IRS references applicable to specific forms"""
        all_refs = IRSReference.query.all()
        applicable = []
        
        for ref in all_refs:
            ref_forms = ref.get_applicable_forms()
            if any(form in ref_forms for form in form_types):
                applicable.append(ref)
        
        return applicable
    
    @staticmethod
    def create_reference(section, title, description, url, applicable_forms=None):
        """Create a new IRS reference"""
        ref = IRSReference(
            section=section,
            title=title,
            description=description,
            url=url
        )
        if applicable_forms:
            ref.set_applicable_forms(applicable_forms)
        
        db.session.add(ref)
        db.session.commit()
        return ref

