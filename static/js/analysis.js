// Tax analysis functionality
const API_BASE = '/api';

// Load clients on page load
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    
    // Check for client_id in URL
    const urlParams = new URLSearchParams(window.location.search);
    const clientId = urlParams.get('client_id');
    if (clientId) {
        document.getElementById('analysis-client-select').value = clientId;
        loadAnalyses();
    }
});

async function loadClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`);
        const clients = await response.json();
        
        const select = document.getElementById('analysis-client-select');
        select.innerHTML = '<option value="">Select a client...</option>';
        
        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            option.textContent = `${client.first_name} ${client.last_name}`;
            select.appendChild(option);
        });
        
        // Set selected value if from URL
        const urlParams = new URLSearchParams(window.location.search);
        const clientId = urlParams.get('client_id');
        if (clientId) {
            select.value = clientId;
        }
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

async function runAnalysis() {
    const clientId = document.getElementById('analysis-client-select').value;
    
    if (!clientId) {
        alert('Please select a client');
        return;
    }
    
    const btn = document.getElementById('run-analysis-btn');
    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    
    try {
        const response = await fetch(`${API_BASE}/analysis/analyze/${clientId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess(`Analysis completed. Found ${result.strategies_count} strategies.`);
            displaySummary(result.summary);
            loadAnalyses();
        } else {
            const error = await response.json();
            showError(error.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Error running analysis:', error);
        showError('Failed to run analysis');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Run Analysis';
    }
}

function displaySummary(summary) {
    const resultsDiv = document.getElementById('analysis-results');
    
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
            <h3>Tax Summary Overview</h3>
            <div class="summary-grid">
                <div class="summary-card income-card" id="total-income-card">
                    <div class="summary-label">Total Income</div>
                    <div class="summary-value">$${formatCurrency(summary.total_income)}</div>
                    <div class="income-tooltip" id="income-tooltip">
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
        <div id="strategies-section" style="margin-top: 2rem;">
            <!-- Strategies will be loaded here -->
        </div>
    `;
    
    // Add hover event listeners for income tooltip
    setupIncomeTooltip();
}

function setupIncomeTooltip() {
    const incomeCard = document.getElementById('total-income-card');
    const tooltip = document.getElementById('income-tooltip');
    
    if (!incomeCard || !tooltip) return;
    
    let tooltipTimeout;
    
    incomeCard.addEventListener('mouseenter', () => {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = setTimeout(() => {
            tooltip.classList.add('visible');
        }, 300); // Small delay for better UX
    });
    
    incomeCard.addEventListener('mouseleave', () => {
        clearTimeout(tooltipTimeout);
        tooltip.classList.remove('visible');
    });
    
    // Position tooltip on mouse move
    incomeCard.addEventListener('mousemove', (e) => {
        if (tooltip.classList.contains('visible')) {
            positionTooltip(e, tooltip, incomeCard);
        }
    });
}

function positionTooltip(e, tooltip, card) {
    const rect = card.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    
    // Position tooltip above the card, centered
    let left = rect.left + scrollX + (rect.width / 2) - (tooltipRect.width / 2);
    let top = rect.top + scrollY - tooltipRect.height - 10;
    
    // Adjust if tooltip goes off screen
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - tooltipRect.width - 10;
    }
    if (top < 10) {
        // Show below if not enough space above
        top = rect.bottom + scrollY + 10;
    }
    
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
}

async function loadAnalyses() {
    const clientId = document.getElementById('analysis-client-select').value;
    
    if (!clientId) {
        const resultsDiv = document.getElementById('analysis-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<p class="loading">Select a client to view analysis results</p>';
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/analysis/client/${clientId}`);
        const result = await response.json();
        const analyses = result.analyses || [];
        const summary = result.summary;
        
        const resultsDiv = document.getElementById('analysis-results');
        
        // Display summary if available (this creates the strategies-section div)
        if (summary) {
            displaySummary(summary);
        } else if (resultsDiv) {
            // No summary available, show message
            resultsDiv.innerHTML = `
                <div class="summary-section">
                    <div class="summary-card warning">
                        <h3>⚠️ No Tax Data Available</h3>
                        <p>Please upload and process tax documents for this client to see a summary.</p>
                    </div>
                </div>
            `;
        }
        
        // Get strategies-section AFTER displaySummary() creates it
        const strategiesSection = document.getElementById('strategies-section');
        
        // Display strategies
        if (strategiesSection) {
            // Update strategies section if it exists
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
                    ${analyses.map(analysis => renderStrategyCard(analysis)).join('')}
                `;
            }
        } else if (resultsDiv) {
            // No strategies-section exists (no summary was displayed), show strategies in main results div
            if (analyses.length === 0) {
                if (!summary) {
                    resultsDiv.innerHTML = `
                        <div class="loading">
                            <p>No analysis results yet. Click "Run Analysis" to generate tax strategies.</p>
                        </div>
                    `;
                }
            } else {
                // Calculate total potential savings
                const totalSavings = analyses.reduce((sum, a) => sum + (a.potential_savings || 0), 0);
                
                // Append or replace content in resultsDiv
                if (summary) {
                    // Summary was displayed, append strategies section
                    const existingContent = resultsDiv.innerHTML;
                    resultsDiv.innerHTML = existingContent + `
                        <div id="strategies-section" style="margin-top: 2rem;">
                            <div class="section">
                                <h3>Tax Strategy Recommendations</h3>
                                <p class="total-savings">Total Potential Savings: <strong>$${totalSavings.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong></p>
                                <p style="font-size: 0.85rem; color: #6c757d; margin-top: 0.5rem;">📊 Enhanced Analysis v2.0 - Showing detailed strategy status, benefits, and forms analyzed</p>
                            </div>
                            ${analyses.map(analysis => renderStrategyCard(analysis)).join('')}
                        </div>
                    `;
                } else {
                    // No summary, replace entire content
                    resultsDiv.innerHTML = `
                        <div class="section">
                            <h3>Total Potential Savings: $${totalSavings.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h3>
                            <p style="font-size: 0.85rem; color: #6c757d; margin-top: 0.5rem;">📊 Enhanced Analysis v2.0 - Showing detailed strategy status, benefits, and forms analyzed</p>
                        </div>
                        ${analyses.map(analysis => renderStrategyCard(analysis)).join('')}
                    `;
                }
            }
        }
    } catch (error) {
        console.error('Error loading analyses:', error);
        showError('Failed to load analysis results');
    }
}

function renderStrategyCard(analysis) {
    const status = analysis.status || 'UNKNOWN';
    const statusClass = getStatusClass(status);
    const statusLabel = getStatusLabel(status);
    
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
    
    const html = `
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
    
    return html;
}

function getStatusClass(status) {
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

function getStatusLabel(status) {
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

