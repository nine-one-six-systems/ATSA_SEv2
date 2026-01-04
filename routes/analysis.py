from flask import Blueprint, request, jsonify
from models import db, AnalysisResult, Client, ExtractedData
from services.analysis_engine import AnalysisEngine

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/analyze/<int:client_id>', methods=['POST'])
def analyze_client(client_id):
    """Run tax analysis for a client"""
    client = Client.query.get_or_404(client_id)
    
    # Delete existing analyses for this client
    AnalysisResult.query.filter_by(client_id=client_id).delete()
    db.session.commit()
    
    # Run analysis
    strategies, summary = AnalysisEngine.analyze_client(client_id)
    
    return jsonify({
        'message': 'Analysis completed',
        'client_id': client_id,
        'strategies_count': len(strategies),
        'strategies': [s.to_dict() for s in strategies],
        'summary': summary
    }), 200

@analysis_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get a specific analysis result"""
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    return jsonify(analysis.to_dict())

@analysis_bp.route('/analysis/client/<int:client_id>', methods=['GET'])
def get_client_analyses(client_id):
    """Get all analyses for a client"""
    analyses = AnalysisResult.query.filter_by(client_id=client_id).order_by(
        AnalysisResult.priority.asc(),
        AnalysisResult.potential_savings.desc()
    ).all()
    
    # Also get summary if data exists
    extracted_data = ExtractedData.query.filter_by(client_id=client_id).all()
    summary = None
    if extracted_data:
        # Organize data by form type
        data_by_form = {}
        for data in extracted_data:
            if data.form_type not in data_by_form:
                data_by_form[data.form_type] = {}
            data_by_form[data.form_type][data.field_name] = data.field_value
        
        client = Client.query.get(client_id)
        if client:
            summary = AnalysisEngine._calculate_summary(data_by_form, client)
    
    return jsonify({
        'analyses': [a.to_dict() for a in analyses],
        'summary': summary
    })

