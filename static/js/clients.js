// Client management functionality
const API_BASE = '/api';

let currentClientId = null;

// Attach event listener function (callable after dropdown is populated)
function attachClientSelectListener() {
    const clientSelect = document.getElementById('client-select');
    if (!clientSelect) {
        return;
    }
    
    // Use onchange property (simpler and more reliable than addEventListener for this case)
    clientSelect.onchange = function() {
        loadClientAnalysis();
    };
}

// Load clients on page load
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    // Note: attachClientSelectListener will be called after dropdown is populated
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
        
        // Also populate dropdown
        populateClientDropdown(clients);
    } catch (error) {
        console.error('Error loading clients:', error);
        showError('Failed to load clients');
    }
}

async function populateClientDropdown(clients = null) {
    const clientSelect = document.getElementById('client-select');
    if (!clientSelect) {
        console.error('client-select element not found in populateClientDropdown');
        return;
    }
    
    // If clients not provided, fetch them
    if (!clients) {
        try {
            const response = await fetch(`${API_BASE}/clients`);
            clients = await response.json();
        } catch (error) {
            console.error('Error loading clients for dropdown:', error);
            return;
        }
    }
    
    // Clear existing options by removing all child nodes (preserves event listeners)
    while (clientSelect.firstChild) {
        clientSelect.removeChild(clientSelect.firstChild);
    }
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a client...';
    clientSelect.appendChild(defaultOption);
    
    // Populate dropdown
    clients.forEach(client => {
        const option = document.createElement('option');
        option.value = client.id;
        option.textContent = `${client.first_name} ${client.last_name}`;
        clientSelect.appendChild(option);
    });
    
    // Attach event listener after dropdown is populated (only once)
    attachClientSelectListener();
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
            await loadClients();
            populateClientDropdown();
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
            await loadClients();
            populateClientDropdown();
            // Reset dropdown if deleted client was selected
            const clientSelect = document.getElementById('client-select');
            if (clientSelect && clientSelect.value == clientId) {
                clientSelect.value = '';
                loadClientAnalysis();
            }
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
    const clientModal = document.getElementById('client-modal');
    const coupleModal = document.getElementById('couple-modal');
    if (event.target === clientModal) {
        closeClientModal();
    }
    if (event.target === coupleModal) {
        closeCoupleModal();
    }
}

// ============================================================================
// Couple Creation Functions
// ============================================================================

function showCoupleModal() {
    document.getElementById('couple-modal').style.display = 'block';
    // Reset form
    document.getElementById('couple-form').reset();
}

function closeCoupleModal() {
    document.getElementById('couple-modal').style.display = 'none';
}

async function createCouple(event) {
    event.preventDefault();

    const filingStatus = document.getElementById('couple-filing-status').value;

    const coupleData = {
        spouse1: {
            first_name: document.getElementById('spouse1-first-name').value,
            last_name: document.getElementById('spouse1-last-name').value,
            email: document.getElementById('spouse1-email').value || null,
            phone: document.getElementById('spouse1-phone').value || null,
            filing_status: filingStatus
        },
        spouse2: {
            first_name: document.getElementById('spouse2-first-name').value,
            last_name: document.getElementById('spouse2-last-name').value,
            email: document.getElementById('spouse2-email').value || null,
            phone: document.getElementById('spouse2-phone').value || null,
            filing_status: filingStatus
        }
    };

    try {
        const response = await fetch('/api/clients/create-couple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(coupleData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create couple');
        }

        const result = await response.json();

        // Redirect to joint analysis page
        window.location.href = result.joint_analysis_url;

    } catch (error) {
        console.error('Error creating couple:', error);
        alert('Error creating couple: ' + error.message);
    }
}

// ============================================================================
// Analysis Display Functions (adapted from analysis.js)
// ============================================================================

async function loadClientAnalysis() {
    const clientSelect = document.getElementById('client-select');
    if (!clientSelect) {
        return;
    }
    
    const clientId = clientSelect.value;
    const analysisResultsDiv = document.getElementById('client-analysis-results');
    
    if (!clientId) {
        // Hide analysis results when no client selected
        if (analysisResultsDiv) {
            analysisResultsDiv.style.display = 'none';
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/analysis/client/${clientId}`);
        const result = await response.json();
        const analyses = result.analyses || [];
        const summary = result.summary;
        const analysisStatus = result.analysis_status || null;
        
        // Show analysis results section
        if (analysisResultsDiv) {
            analysisResultsDiv.style.display = 'block';
        }
        
        // Display summary if available
        if (summary) {
            displayClientSummary(summary, analysisStatus);
        } else {
            // No summary available
            if (analysisResultsDiv) {
                analysisResultsDiv.innerHTML = `
                    <div class="summary-section">
                        <div class="summary-card warning">
                            <h3>⚠️ No Tax Data Available</h3>
                            <p>Please upload and process tax documents for this client to see a summary.</p>
                            ${analysisStatus ? `<p style="font-size: 0.85rem; margin-top: 0.5rem; color: #6c757d;">Analysis will run automatically after processing documents.</p>` : ''}
                        </div>
                    </div>
                `;
            }
            return;
        }
        
        // Get strategies-section AFTER displaySummary() creates it
        const strategiesSection = document.getElementById('client-strategies-section');
        
        // Display strategies
        if (strategiesSection) {
            if (analyses.length === 0) {
                strategiesSection.innerHTML = `
                    <div class="loading">
                        <p>No tax strategies available. Run analysis to generate recommendations.</p>
                    </div>
                `;
            } else {
                // Calculate total potential savings
                const totalSavings = analyses.reduce((sum, a) => sum + (a.potential_savings || 0), 0);
                
                strategiesSection.innerHTML = `
                    <div class="section">
                        <h3>Tax Strategy Recommendations</h3>
                        <p class="total-savings">Total Potential Savings: <strong>$${totalSavings.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong></p>
                        <p style="font-size: 0.85rem; color: #6c757d; margin-top: 0.5rem;">📊 Enhanced Analysis v2.0 - Showing detailed strategy status, benefits, and forms analyzed</p>
                    </div>
                    ${analyses.map(analysis => renderClientStrategyCard(analysis)).join('')}
                `;
            }
        }
    } catch (error) {
        console.error('Error loading analysis:', error);
        showError('Failed to load analysis results');
    }
}

function displayClientSummary(summary, analysisStatus) {
    const resultsDiv = document.getElementById('client-analysis-results');
    
    if (!summary || summary.total_income === 0) {
        resultsDiv.innerHTML = `
            <div class="summary-section">
                <div class="summary-card warning">
                    <h3>⚠️ No Tax Data Available</h3>
                    <p>Please upload and process tax documents for this client to see a summary.</p>
                </div>
            </div>
        `;
        return;
    }
    
    const taxStatus = summary.tax_owed > 0 ? 'owed' : 'refund';
    const taxAmount = summary.tax_owed > 0 ? summary.tax_owed : summary.tax_refund;
    
    // Build analysis status info
    let analysisStatusHtml = '';
    if (analysisStatus && analysisStatus.last_analyzed_at) {
        const lastAnalyzed = new Date(analysisStatus.last_analyzed_at);
        analysisStatusHtml = `
            <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 1rem; padding: 0.5rem; background: #f8f9fa; border-radius: 4px;">
                <strong>Analysis Status:</strong> Last analyzed on ${lastAnalyzed.toLocaleString()}
                ${analysisStatus.data_version_hash ? ' • Analysis is up to date' : ''}
            </div>
        `;
    }
    
    // Build income sources breakdown HTML
    const incomeSourcesHtml = summary.income_sources && summary.income_sources.length > 0
        ? summary.income_sources.map(source => `
            <div class="income-source-item">
                <span class="income-source-name">${source.source}</span>
                <span class="income-source-amount">$${formatCurrency(source.amount)}</span>
            </div>
        `).join('')
        : '<div class="income-source-item"><span>No income sources identified</span></div>';
    
    resultsDiv.innerHTML = `
        <div class="summary-section">
            ${analysisStatusHtml}
            <h3>Tax Summary Overview</h3>
            <div class="summary-grid">
                <div class="summary-card income-card" id="client-total-income-card">
                    <div class="summary-label">Total Income</div>
                    <div class="summary-value">$${formatCurrency(summary.total_income)}</div>
                    <div class="income-tooltip" id="client-income-tooltip">
                        <div class="tooltip-header">Income Sources Breakdown</div>
                        <div class="tooltip-content">
                            ${incomeSourcesHtml}
                            <div class="income-source-total">
                                <span class="income-source-name"><strong>Total</strong></span>
                                <span class="income-source-amount"><strong>$${formatCurrency(summary.total_income)}</strong></span>
                            </div>
                        </div>
                        <div class="tooltip-arrow"></div>
                    </div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Adjusted Gross Income (AGI)</div>
                    <div class="summary-value">$${formatCurrency(summary.adjusted_gross_income)}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Taxable Income</div>
                    <div class="summary-value">$${formatCurrency(summary.taxable_income)}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Total Tax Liability</div>
                    <div class="summary-value tax-liability">$${formatCurrency(summary.total_tax)}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Tax Withheld</div>
                    <div class="summary-value">$${formatCurrency(summary.tax_withheld)}</div>
                </div>
                <div class="summary-card ${taxStatus === 'owed' ? 'owed' : 'refund'}">
                    <div class="summary-label">${taxStatus === 'owed' ? 'Tax Owed' : 'Tax Refund'}</div>
                    <div class="summary-value">$${formatCurrency(taxAmount)}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Effective Tax Rate</div>
                    <div class="summary-value">${summary.effective_tax_rate.toFixed(2)}%</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Marginal Tax Rate</div>
                    <div class="summary-value">${summary.marginal_tax_rate}%</div>
                </div>
            </div>
        </div>
        <div id="client-strategies-section" style="margin-top: 2rem;">
            <!-- Strategies will be loaded here -->
        </div>
    `;
    
    // Add hover event listeners for income tooltip
    setupClientIncomeTooltip();
}

function setupClientIncomeTooltip() {
    const incomeCard = document.getElementById('client-total-income-card');
    const tooltip = document.getElementById('client-income-tooltip');
    
    if (!incomeCard || !tooltip) return;
    
    let tooltipTimeout;
    
    incomeCard.addEventListener('mouseenter', () => {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = setTimeout(() => {
            tooltip.classList.add('visible');
        }, 300);
    });
    
    incomeCard.addEventListener('mouseleave', () => {
        clearTimeout(tooltipTimeout);
        tooltip.classList.remove('visible');
    });
    
    incomeCard.addEventListener('mousemove', (e) => {
        if (tooltip.classList.contains('visible')) {
            positionClientTooltip(e, tooltip, incomeCard);
        }
    });
}

function positionClientTooltip(e, tooltip, card) {
    const rect = card.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    
    let left = rect.left + scrollX + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top + scrollY - tooltipRect.height - 10;
    
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - tooltipRect.width - 10;
    }
    if (top < 10) {
        top = rect.bottom + scrollY + 10;
    }
    
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
}

function renderClientStrategyCard(analysis) {
    const status = analysis.status || 'UNKNOWN';
    const statusClass = getClientStatusClass(status);
    const statusLabel = getClientStatusLabel(status);
    
    const flags = analysis.flags || [];
    const recommendations = analysis.recommendations || [];
    const formsAnalyzed = analysis.forms_analyzed || [];
    
    const currentBenefit = analysis.current_benefit || 0;
    const potentialBenefit = analysis.potential_benefit || analysis.potential_savings || 0;
    const unusedCapacity = analysis.unused_capacity || 0;
    
    let flagsHtml = '';
    if (flags.length > 0) {
        flagsHtml = `
            <div class="strategy-flags">
                <strong>Flags:</strong>
                <ul>
                    ${flags.map(flag => `<li class="flag-item">${flag}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    let recommendationsHtml = '';
    if (recommendations.length > 0) {
        recommendationsHtml = `
            <div class="strategy-recommendations">
                <strong>Recommendations:</strong>
                <ul>
                    ${recommendations.map(rec => `<li class="recommendation-item">${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    let formsHtml = '';
    if (formsAnalyzed.length > 0) {
        formsHtml = `
            <div class="strategy-forms">
                <strong>Forms Analyzed:</strong>
                <span class="forms-list">${formsAnalyzed.join(', ')}</span>
            </div>
        `;
    }
    
    let benefitsHtml = '';
    if (currentBenefit > 0 || potentialBenefit > 0) {
        benefitsHtml = `
            <div class="strategy-benefits">
                ${currentBenefit > 0 ? `<div class="benefit-item"><span class="benefit-label">Current Benefit:</span> <span class="benefit-value">$${formatCurrency(currentBenefit)}</span></div>` : ''}
                ${potentialBenefit > currentBenefit ? `<div class="benefit-item"><span class="benefit-label">Potential Benefit:</span> <span class="benefit-value">$${formatCurrency(potentialBenefit)}</span></div>` : ''}
                ${unusedCapacity > 0 ? `<div class="benefit-item"><span class="benefit-label">Unused Capacity:</span> <span class="benefit-value unused">$${formatCurrency(unusedCapacity)}</span></div>` : ''}
            </div>
        `;
    }
    
    return `
        <div class="strategy-card priority-${analysis.priority} status-${statusClass}">
            <div class="strategy-header">
                <div class="strategy-name">${analysis.strategy_name}</div>
                <div class="strategy-status-badge ${statusClass}">${statusLabel}</div>
            </div>
            <div class="strategy-content">
                ${benefitsHtml}
                ${flagsHtml}
                ${recommendationsHtml}
                ${formsHtml}
                <div class="irs-reference">
                    <strong>IRS Reference:</strong> 
                    <a href="${analysis.irs_url || '#'}" target="_blank">${analysis.irs_section}</a>
                    ${analysis.irs_code ? ` (${analysis.irs_code})` : ''}
                </div>
            </div>
        </div>
    `;
}

function getClientStatusClass(status) {
    const statusMap = {
        'FULLY_UTILIZED': 'success',
        'PARTIALLY_UTILIZED': 'warning',
        'NOT_UTILIZED': 'error',
        'NOT_APPLICABLE': 'neutral',
        'ERROR_DETECTED': 'error',
        'POTENTIALLY_MISSED': 'warning',
        'SUBOPTIMAL': 'warning',
        'COMPLIANT_PRE_OBBBA': 'info'
    };
    return statusMap[status] || 'neutral';
}

function getClientStatusLabel(status) {
    const labelMap = {
        'FULLY_UTILIZED': '✓ Fully Utilized',
        'PARTIALLY_UTILIZED': '⚠ Partially Utilized',
        'NOT_UTILIZED': '✗ Not Utilized',
        'NOT_APPLICABLE': '— Not Applicable',
        'ERROR_DETECTED': '⚠ Error Detected',
        'POTENTIALLY_MISSED': '⚠ Potentially Missed',
        'SUBOPTIMAL': '⚠ Suboptimal',
        'COMPLIANT_PRE_OBBBA': 'ℹ Compliant (Pre-OBBBA)'
    };
    return labelMap[status] || status;
}

function formatCurrency(amount) {
    if (!amount) return '0.00';
    return amount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

