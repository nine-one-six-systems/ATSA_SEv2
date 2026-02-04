from flask import Blueprint, request, jsonify
from models import db, Client
from datetime import datetime

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients', methods=['GET'])
def get_clients():
    """Get all clients"""
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])

@clients_bp.route('/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get a specific client"""
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())

@clients_bp.route('/clients', methods=['POST'])
def create_client():
    """Create a new client"""
    data = request.get_json()
    
    required_fields = ['first_name', 'last_name', 'filing_status']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    client = Client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        ssn=data.get('ssn'),
        filing_status=data['filing_status'],
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        spouse_id=data.get('spouse_id')
    )
    
    db.session.add(client)
    db.session.commit()
    
    return jsonify(client.to_dict()), 201

@clients_bp.route('/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update a client"""
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    
    if 'first_name' in data:
        client.first_name = data['first_name']
    if 'last_name' in data:
        client.last_name = data['last_name']
    if 'ssn' in data:
        if data['ssn']:
            # Create a temporary client instance to use the encryption method
            temp_client = Client()
            client.ssn = temp_client._encrypt_ssn(data['ssn'])
        else:
            client.ssn = None
    if 'filing_status' in data:
        client.filing_status = data['filing_status']
    if 'email' in data:
        client.email = data['email']
    if 'phone' in data:
        client.phone = data['phone']
    if 'address' in data:
        client.address = data['address']
    if 'spouse_id' in data:
        client.spouse_id = data['spouse_id']
    
    client.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(client.to_dict())

@clients_bp.route('/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete a client"""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    
    return jsonify({'message': 'Client deleted successfully'}), 200

@clients_bp.route('/clients/<int:client_id>/link-spouse', methods=['POST'])
def link_spouse(client_id):
    """Link two client profiles as spouses"""
    client = Client.query.get_or_404(client_id)
    data = request.get_json()

    spouse_id = data.get('spouse_id')
    if not spouse_id:
        return jsonify({'error': 'Missing spouse_id'}), 400

    spouse = Client.query.get_or_404(spouse_id)

    # Link both ways
    client.spouse_id = spouse_id
    spouse.spouse_id = client_id

    db.session.commit()

    return jsonify({
        'message': 'Clients linked successfully',
        'client': client.to_dict(),
        'spouse': spouse.to_dict()
    }), 200


@clients_bp.route('/clients/create-couple', methods=['POST'])
def create_couple():
    """Create two linked spouse client records in a single operation"""
    data = request.get_json()

    spouse1_data = data.get('spouse1')
    spouse2_data = data.get('spouse2')

    # Validate both spouse objects exist
    if not spouse1_data or not spouse2_data:
        return jsonify({'error': 'Both spouse1 and spouse2 data are required'}), 400

    # Validate required fields for each spouse
    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if field not in spouse1_data or not spouse1_data[field]:
            return jsonify({'error': f'Missing required field for spouse1: {field}'}), 400
        if field not in spouse2_data or not spouse2_data[field]:
            return jsonify({'error': f'Missing required field for spouse2: {field}'}), 400

    # Validate filing status is married type
    valid_married_statuses = ['married_joint', 'married_separate']
    spouse1_status = spouse1_data.get('filing_status', 'married_joint')
    spouse2_status = spouse2_data.get('filing_status', 'married_joint')

    if spouse1_status not in valid_married_statuses:
        return jsonify({'error': f'Invalid filing status for spouse1: {spouse1_status}. Must be married_joint or married_separate'}), 400
    if spouse2_status not in valid_married_statuses:
        return jsonify({'error': f'Invalid filing status for spouse2: {spouse2_status}. Must be married_joint or married_separate'}), 400

    # Create spouse1 first, flush to get ID
    spouse1 = Client(
        first_name=spouse1_data['first_name'],
        last_name=spouse1_data['last_name'],
        filing_status=spouse1_status,
        email=spouse1_data.get('email'),
        phone=spouse1_data.get('phone')
    )
    db.session.add(spouse1)
    db.session.flush()  # Get spouse1.id

    # Create spouse2 linked to spouse1
    spouse2 = Client(
        first_name=spouse2_data['first_name'],
        last_name=spouse2_data['last_name'],
        filing_status=spouse2_status,
        email=spouse2_data.get('email'),
        phone=spouse2_data.get('phone'),
        spouse_id=spouse1.id
    )
    db.session.add(spouse2)
    db.session.flush()  # Get spouse2.id

    # Link spouse1 back to spouse2 (bidirectional)
    spouse1.spouse_id = spouse2.id
    db.session.commit()

    return jsonify({
        'spouse1': spouse1.to_dict(),
        'spouse2': spouse2.to_dict(),
        'joint_analysis_url': f'/joint-analysis.html?spouse1_id={spouse1.id}&spouse2_id={spouse2.id}'
    }), 201

