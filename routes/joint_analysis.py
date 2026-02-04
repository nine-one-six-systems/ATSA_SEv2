from flask import Blueprint, request, jsonify
from models import db, Client, JointAnalysisSummary
from services.joint_analysis_service import JointAnalysisService

joint_analysis_bp = Blueprint('joint_analysis', __name__)


@joint_analysis_bp.route('/joint-analysis/<int:spouse1_id>/<int:spouse2_id>', methods=['POST'])
def run_joint_analysis(spouse1_id, spouse2_id):
    """Trigger joint analysis for two linked spouses (force refresh)"""
    try:
        result = JointAnalysisService.analyze_joint(
            spouse1_id, spouse2_id, force_refresh=True
        )

        return jsonify({
            'message': 'Joint analysis completed',
            'spouse1_id': spouse1_id,
            'spouse2_id': spouse2_id,
            'result': result
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@joint_analysis_bp.route('/joint-analysis/<int:spouse1_id>/<int:spouse2_id>', methods=['GET'])
def get_joint_analysis(spouse1_id, spouse2_id):
    """Get joint analysis results (returns cached if available, otherwise calculates)"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'

        result = JointAnalysisService.analyze_joint(
            spouse1_id, spouse2_id, force_refresh=force_refresh
        )

        return jsonify({
            'spouse1_id': spouse1_id,
            'spouse2_id': spouse2_id,
            'result': result
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@joint_analysis_bp.route('/joint-analysis/<int:spouse1_id>/<int:spouse2_id>/comparison', methods=['GET'])
def get_comparison_summary(spouse1_id, spouse2_id):
    """Get concise MFJ vs MFS comparison summary"""
    try:
        summary = JointAnalysisService.get_comparison_summary(spouse1_id, spouse2_id)

        return jsonify({
            'spouse1_id': spouse1_id,
            'spouse2_id': spouse2_id,
            'comparison': summary
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500
