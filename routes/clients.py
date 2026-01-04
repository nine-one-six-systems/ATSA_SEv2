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

