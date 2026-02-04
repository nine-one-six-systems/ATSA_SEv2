from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Document, Client, ExtractedData
from services.ocr_service import OCRService
from services.tax_parser import TaxParser
from services.analysis_engine import AnalysisEngine
import os
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}

@documents_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    """Upload a tax document with optional attribution"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    client_id = request.form.get('client_id', type=int)
    tax_year = request.form.get('tax_year', type=int)
    attribution = request.form.get('attribution', 'taxpayer')

    if not client_id:
        return jsonify({'error': 'Missing client_id'}), 400

    # Validate attribution value
    if attribution not in ['taxpayer', 'spouse', 'joint']:
        return jsonify({'error': 'Invalid attribution. Must be taxpayer, spouse, or joint'}), 400

    # If attribution is 'spouse', validate client has spouse_id
    if attribution == 'spouse':
        client = Client.query.get(client_id)
        if not client or not client.spouse_id:
            return jsonify({'error': 'Cannot use spouse attribution - no spouse linked'}), 400

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

    # Create document record with attribution
    document = Document(
        client_id=client_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        tax_year=tax_year,
        attribution=attribution,
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
        
        # Automatically trigger analysis after successful extraction
        analysis_triggered = False
        analysis_error = None
        try:
            strategies, summary = AnalysisEngine.analyze_client(document.client_id)
            analysis_triggered = True
        except Exception as analysis_ex:
            # Log error but don't fail the document processing
            analysis_error = str(analysis_ex)
            current_app.logger.error(f'Analysis failed for client {document.client_id}: {analysis_error}')
        
        response_data = {
            'message': 'Document processed successfully',
            'document': document.to_dict(),
            'forms_detected': list(parsed_data.keys()),
            'parsed_data': parsed_data,
            'analysis_triggered': analysis_triggered
        }
        
        if analysis_error:
            response_data['analysis_error'] = analysis_error
        
        return jsonify(response_data), 200
    
    except Exception as e:
        document.ocr_status = 'failed'
        db.session.commit()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@documents_bp.route('/documents/client/<int:client_id>', methods=['GET'])
def get_client_documents(client_id):
    """Get all documents for a client"""
    documents = Document.query.filter_by(client_id=client_id).all()
    return jsonify([doc.to_dict() for doc in documents])


@documents_bp.route('/documents/manual-entry', methods=['POST'])
def manual_entry():
    """Create extracted data from manual income entry"""
    data = request.get_json()

    client_id = data.get('client_id')
    tax_year = data.get('tax_year', 2026)
    attribution = data.get('attribution', 'taxpayer')
    income_data = data.get('income_data', {})

    if not client_id:
        return jsonify({'error': 'Missing client_id'}), 400

    # Validate attribution value
    if attribution not in ['taxpayer', 'spouse', 'joint']:
        return jsonify({'error': 'Invalid attribution. Must be taxpayer, spouse, or joint'}), 400

    # Determine target client based on attribution
    target_client_id = client_id
    if attribution == 'spouse':
        client = Client.query.get(client_id)
        if not client or not client.spouse_id:
            return jsonify({'error': 'Cannot use spouse attribution - no spouse linked'}), 400
        target_client_id = client.spouse_id

    # Create ExtractedData records for each income field
    created_records = []

    # W-2 wages
    if income_data.get('wages'):
        record = ExtractedData(
            document_id=None,  # No document for manual entry
            client_id=target_client_id,
            form_type='W-2',
            field_name='wages',
            field_value=str(income_data['wages']),
            tax_year=tax_year
        )
        db.session.add(record)
        created_records.append({'form': 'W-2', 'field': 'wages', 'value': income_data['wages']})

    if income_data.get('federal_withheld'):
        record = ExtractedData(
            document_id=None,
            client_id=target_client_id,
            form_type='W-2',
            field_name='federal_tax_withheld',
            field_value=str(income_data['federal_withheld']),
            tax_year=tax_year
        )
        db.session.add(record)
        created_records.append({'form': 'W-2', 'field': 'federal_tax_withheld', 'value': income_data['federal_withheld']})

    # Schedule C (self-employment)
    if income_data.get('schedule_c_income'):
        record = ExtractedData(
            document_id=None,
            client_id=target_client_id,
            form_type='Schedule C',
            field_name='net_profit',
            field_value=str(income_data['schedule_c_income']),
            tax_year=tax_year
        )
        db.session.add(record)
        created_records.append({'form': 'Schedule C', 'field': 'net_profit', 'value': income_data['schedule_c_income']})

    # Interest income
    if income_data.get('interest_income'):
        record = ExtractedData(
            document_id=None,
            client_id=target_client_id,
            form_type='1099-INT',
            field_name='interest',
            field_value=str(income_data['interest_income']),
            tax_year=tax_year
        )
        db.session.add(record)
        created_records.append({'form': '1099-INT', 'field': 'interest', 'value': income_data['interest_income']})

    # Dividend income
    if income_data.get('dividend_income'):
        record = ExtractedData(
            document_id=None,
            client_id=target_client_id,
            form_type='1099-DIV',
            field_name='dividends',
            field_value=str(income_data['dividend_income']),
            tax_year=tax_year
        )
        db.session.add(record)
        created_records.append({'form': '1099-DIV', 'field': 'dividends', 'value': income_data['dividend_income']})

    db.session.commit()

    # Trigger analysis for the target client
    analysis_triggered = False
    try:
        AnalysisEngine.analyze_client(target_client_id)
        analysis_triggered = True
    except Exception as e:
        current_app.logger.error(f'Analysis failed after manual entry: {str(e)}')

    return jsonify({
        'message': 'Manual entry saved successfully',
        'client_id': target_client_id,
        'records_created': created_records,
        'analysis_triggered': analysis_triggered
    }), 201

