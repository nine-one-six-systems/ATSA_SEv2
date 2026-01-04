// Client management functionality
const API_BASE = '/api';

let currentClientId = null;

// Load clients on page load
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
});

async function loadClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`);
        const clients = await response.json();
        
        const clientsList = document.getElementById('clients-list');
        
        if (clients.length === 0) {
            clientsList.innerHTML = '<p class="loading">No clients yet. Click "Add New Client" to get started.</p>';
        } else {
            clientsList.innerHTML = clients.map(client => `
                <div class="client-card">
                    <h4>${client.first_name} ${client.last_name}</h4>
                    <p><strong>Filing Status:</strong> ${formatFilingStatus(client.filing_status)}</p>
                    <p><strong>Email:</strong> ${client.email || 'N/A'}</p>
                    <p><strong>Phone:</strong> ${client.phone || 'N/A'}</p>
                    ${client.spouse_id ? `<p><strong>Spouse ID:</strong> ${client.spouse_id}</p>` : ''}
                    <div class="client-actions">
                        <button class="btn btn-primary" onclick="editClient(${client.id})">Edit</button>
                        <button class="btn btn-secondary" onclick="viewAnalysis(${client.id})">View Analysis</button>
                        <button class="btn btn-danger" onclick="deleteClient(${client.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading clients:', error);
        showError('Failed to load clients');
    }
}

function formatFilingStatus(status) {
    const statusMap = {
        'single': 'Single',
        'married_joint': 'Married Filing Jointly',
        'married_separate': 'Married Filing Separately',
        'head_of_household': 'Head of Household'
    };
    return statusMap[status] || status;
}

function showClientModal(clientId = null) {
    currentClientId = clientId;
    const modal = document.getElementById('client-modal');
    const form = document.getElementById('client-form');
    const title = document.getElementById('modal-title');
    
    if (clientId) {
        title.textContent = 'Edit Client';
        loadClientData(clientId);
    } else {
        title.textContent = 'Add New Client';
        form.reset();
        document.getElementById('client-id').value = '';
    }
    
    modal.style.display = 'block';
}

function closeClientModal() {
    document.getElementById('client-modal').style.display = 'none';
    currentClientId = null;
}

async function loadClientData(clientId) {
    try {
        const response = await fetch(`${API_BASE}/clients/${clientId}`);
        const client = await response.json();
        
        document.getElementById('client-id').value = client.id;
        document.getElementById('first-name').value = client.first_name;
        document.getElementById('last-name').value = client.last_name;
        document.getElementById('filing-status').value = client.filing_status;
        document.getElementById('email').value = client.email || '';
        document.getElementById('phone').value = client.phone || '';
        document.getElementById('address').value = client.address || '';
        document.getElementById('spouse-id').value = client.spouse_id || '';
    } catch (error) {
        console.error('Error loading client:', error);
        showError('Failed to load client data');
    }
}

async function saveClient(event) {
    event.preventDefault();
    
    const clientId = document.getElementById('client-id').value;
    const data = {
        first_name: document.getElementById('first-name').value,
        last_name: document.getElementById('last-name').value,
        filing_status: document.getElementById('filing-status').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        address: document.getElementById('address').value,
        spouse_id: document.getElementById('spouse-id').value || null
    };
    
    try {
        let response;
        if (clientId) {
            // Update existing client
            response = await fetch(`${API_BASE}/clients/${clientId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        } else {
            // Create new client
            response = await fetch(`${API_BASE}/clients`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            closeClientModal();
            loadClients();
            showSuccess(clientId ? 'Client updated successfully' : 'Client created successfully');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to save client');
        }
    } catch (error) {
        console.error('Error saving client:', error);
        showError('Failed to save client');
    }
}

async function editClient(clientId) {
    showClientModal(clientId);
}

async function deleteClient(clientId) {
    if (!confirm('Are you sure you want to delete this client? This will also delete all associated documents and analyses.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/clients/${clientId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadClients();
            showSuccess('Client deleted successfully');
        } else {
            showError('Failed to delete client');
        }
    } catch (error) {
        console.error('Error deleting client:', error);
        showError('Failed to delete client');
    }
}

function viewAnalysis(clientId) {
    window.location.href = `/analysis.html?client_id=${clientId}`;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.body.insertBefore(errorDiv, document.body.firstChild);
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    document.body.insertBefore(successDiv, document.body.firstChild);
    setTimeout(() => successDiv.remove(), 5000);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('client-modal');
    if (event.target == modal) {
        closeClientModal();
    }
}

