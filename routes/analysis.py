from flask import Blueprint, request, jsonify
from models import db, AnalysisResult, AnalysisSummary, Client, ExtractedData
from services.analysis_engine import AnalysisEngine

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/analyze/<int:client_id>', methods=['POST'])
def analyze_client(client_id):
    """Run tax analysis for a client (force refresh)"""
    client = Client.query.get_or_404(client_id)
    
    # Run analysis with force_refresh=True to ensure fresh analysis
    strategies, summary = AnalysisEngine.analyze_client(client_id, force_refresh=True)
    
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
    """Get all analyses for a client (returns stored results from database)"""
    analyses = AnalysisResult.query.filter_by(client_id=client_id).order_by(
        AnalysisResult.priority.asc(),
        AnalysisResult.potential_savings.desc()
    ).all()
    
    # Get stored summary from database instead of recalculating
    analysis_summary = AnalysisSummary.query.filter_by(client_id=client_id).first()
    summary = None
    if analysis_summary:
        summary_dict = analysis_summary.to_dict()
        # Remove internal fields from summary dict
        summary_dict.pop('id', None)
        summary_dict.pop('client_id', None)
        summary_dict.pop('data_version_hash', None)
        summary_dict.pop('last_analyzed_at', None)
        summary_dict.pop('created_at', None)
        summary_dict.pop('updated_at', None)
        summary = summary_dict
    
    # Get analysis status info
    analysis_status = None
    if analysis_summary:
        analysis_status = {
            'last_analyzed_at': analysis_summary.last_analyzed_at.isoformat() if analysis_summary.last_analyzed_at else None,
            'data_version_hash': analysis_summary.data_version_hash
        }
    
    return jsonify({
        'analyses': [a.to_dict() for a in analyses],
        'summary': summary,
        'analysis_status': analysis_status
    })

