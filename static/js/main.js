// Main dashboard functionality
const API_BASE = '/api';

async function loadDashboard() {
    try {
        // Load clients
        const clientsResponse = await fetch(`${API_BASE}/clients`);
        const clients = await clientsResponse.json();
        
        document.getElementById('total-clients').textContent = clients.length;
        
        // Display recent clients
        const recentClients = clients.slice(0, 5);
        const clientsList = document.getElementById('recent-clients');
        
        if (recentClients.length === 0) {
            clientsList.innerHTML = '<p class="loading">No clients yet. <a href="/clients.html">Add your first client</a></p>';
        } else {
            clientsList.innerHTML = recentClients.map(client => `
                <div class="client-card">
                    <h4>${client.first_name} ${client.last_name}</h4>
                    <p>Filing Status: ${formatFilingStatus(client.filing_status)}</p>
                    <p>Email: ${client.email || 'N/A'}</p>
                </div>
            `).join('');
        }
        
        // Load documents count (simplified - would need aggregation endpoint)
        // For now, just set to 0
        document.getElementById('total-documents').textContent = '0';
        document.getElementById('total-analyses').textContent = '0';
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
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

// Load dashboard on page load
if (document.getElementById('total-clients')) {
    loadDashboard();
}

