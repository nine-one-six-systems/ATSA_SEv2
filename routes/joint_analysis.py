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


@joint_analysis_bp.route('/validate-deduction-method', methods=['POST'])
def validate_deduction_method():
    """
    Validate deduction method change for MFS coordination (REQ-09).

    Request body: {"client_id": int, "new_method": "standard" or "itemized"}
    Response: {"allowed": bool, "message": str, "action": str, ...}
    """
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        new_method = data.get('new_method')

        if not client_id or not new_method:
            return jsonify({'error': 'client_id and new_method required'}), 400

        if new_method not in ['standard', 'itemized']:
            return jsonify({'error': 'new_method must be "standard" or "itemized"'}), 400

        result = JointAnalysisService.validate_deduction_method_change(client_id, new_method)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
