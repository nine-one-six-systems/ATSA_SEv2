from flask import Blueprint
from routes.clients import clients_bp
from routes.documents import documents_bp
from routes.analysis import analysis_bp
from routes.calculator import calculator_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register all route blueprints
api_bp.register_blueprint(clients_bp)
api_bp.register_blueprint(documents_bp)
api_bp.register_blueprint(analysis_bp)
api_bp.register_blueprint(calculator_bp)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'ok', 'message': 'ATSA API is running'}

