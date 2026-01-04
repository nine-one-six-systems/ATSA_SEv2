from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Document
from services.ocr_service import OCRService
from services.tax_parser import TaxParser
import os
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}

@documents_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    """Upload a tax document"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    client_id = request.form.get('client_id', type=int)
    tax_year = request.form.get('tax_year', type=int)
    
    if not client_id:
        return jsonify({'error': 'Missing client_id'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, JPG, PNG'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    file_type = 'pdf' if file_ext == 'pdf' else ('jpg' if file_ext in ['jpg', 'jpeg'] else 'png')
    
    # Create unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{client_id}_{timestamp}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    
    file.save(file_path)
    
    # Create document record
    document = Document(
        client_id=client_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        tax_year=tax_year,
        ocr_status='pending'
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify(document.to_dict()), 201

@documents_bp.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get document details"""
    document = Document.query.get_or_404(document_id)
    return jsonify(document.to_dict())

@documents_bp.route('/documents/<int:document_id>/process', methods=['POST'])
def process_document(document_id):
    """Process document with OCR and extract tax data"""
    document = Document.query.get_or_404(document_id)
    
    # Update status
    document.ocr_status = 'processing'
    db.session.commit()
    
    try:
        # Extract text using OCR
        text = OCRService.extract_text(document.file_path, document.file_type)
        
        # Parse tax data
        parsed_data = TaxParser.parse_text(text, document.id, document.client_id)
        
        # Update status
        document.ocr_status = 'completed'
        db.session.commit()
        
        return jsonify({
            'message': 'Document processed successfully',
            'document': document.to_dict(),
            'forms_detected': list(parsed_data.keys()),
            'parsed_data': parsed_data
        }), 200
    
    except Exception as e:
        document.ocr_status = 'failed'
        db.session.commit()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@documents_bp.route('/documents/client/<int:client_id>', methods=['GET'])
def get_client_documents(client_id):
    """Get all documents for a client"""
    documents = Document.query.filter_by(client_id=client_id).all()
    return jsonify([doc.to_dict() for doc in documents])

