// Joint Analysis JavaScript
// Implements split-screen spouse comparison for MFJ vs MFS analysis

const API_BASE = '/api';
let splitInstance = null;

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Load linked spouse pairs for dropdowns
    await loadLinkedClients();

    // Initialize Split.js for desktop
    initSplit();

    // Handle window resize for responsive Split.js
    window.addEventListener('resize', debounce(handleResize, 150));

    // Bind click handler for Load Analysis button
    document.getElementById('load-analysis-btn').addEventListener('click', loadJointAnalysis);

    // Check URL parameters for pre-selected spouses
    const urlParams = new URLSearchParams(window.location.search);
    const spouse1Id = urlParams.get('spouse1_id');
    const spouse2Id = urlParams.get('spouse2_id');

    if (spouse1Id && spouse2Id) {
        document.getElementById('spouse1-select').value = spouse1Id;
        document.getElementById('spouse2-select').value = spouse2Id;
        await loadJointAnalysis();
    }
});

// ============================================================
// SPLIT.JS MANAGEMENT
// ============================================================

/**
 * Initialize Split.js only on desktop (>768px).
 * Restores saved sizes from localStorage if available.
 */
function initSplit() {
    if (typeof Split === 'undefined') {
        console.warn('Split.js not loaded');
        return;
    }

    if (window.innerWidth <= 768) {
        return; // Don't initialize on mobile
    }

    // Restore sizes from localStorage or use defaults
    let sizes = [50, 50];
    const savedSizes = localStorage.getItem('jointAnalysisSplitSizes');
    if (savedSizes) {
        try {
            sizes = JSON.parse(savedSizes);
        } catch (e) {
            console.warn('Invalid saved split sizes, using defaults');
        }
    }

    splitInstance = Split(['#spouse1-panel', '#spouse2-panel'], {
        sizes: sizes,
        minSize: 280,
        gutterSize: 10,
        cursor: 'col-resize',
        onDragEnd: function(sizes) {
            // Save sizes to localStorage on drag end
            localStorage.setItem('jointAnalysisSplitSizes', JSON.stringify(sizes));
        }
    });
}

/**
 * Handle window resize: destroy/recreate Split.js based on viewport width.
 */
function handleResize() {
    if (window.innerWidth <= 768 && splitInstance) {
        // Destroy Split.js on mobile
        splitInstance.destroy();
        splitInstance = null;
    } else if (window.innerWidth > 768 && !splitInstance) {
        // Recreate Split.js on desktop
        initSplit();
    }
}

/**
 * Debounce utility function.
 */
function debounce(fn, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
}

// ============================================================
// CLIENT LOADING
// ============================================================

/**
 * Fetch clients and populate both dropdowns.
 * Shows only clients with spouse_id set (linked spouses).
 */
async function loadLinkedClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`);
        if (!response.ok) {
            throw new Error('Failed to fetch clients');
        }
        const clients = await response.json();

        // Filter to only show clients with linked spouses
        const linkedClients = clients.filter(client => client.spouse_id);

        const spouse1Select = document.getElementById('spouse1-select');
        const spouse2Select = document.getElementById('spouse2-select');

        // Clear and repopulate dropdowns
        spouse1Select.innerHTML = '<option value="">Select Spouse 1...</option>';
        spouse2Select.innerHTML = '<option value="">Select Spouse 2...</option>';

        linkedClients.forEach(client => {
            const option1 = document.createElement('option');
            option1.value = client.id;
            option1.textContent = `${client.first_name} ${client.last_name}`;
            spouse1Select.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = client.id;
            option2.textContent = `${client.first_name} ${client.last_name}`;
            spouse2Select.appendChild(option2);
        });

        // If no linked clients, show message
        if (linkedClients.length === 0) {
            spouse1Select.innerHTML = '<option value="">No linked spouses found</option>';
            spouse2Select.innerHTML = '<option value="">No linked spouses found</option>';
        }

    } catch (error) {
        console.error('Error loading clients:', error);
        showError('Failed to load clients');
    }
}

// ============================================================
// JOINT ANALYSIS LOADING
// ============================================================

/**
 * Main function triggered by Load Analysis button.
 * Fetches joint analysis data and displays results.
 */
async function loadJointAnalysis() {
    const spouse1Id = document.getElementById('spouse1-select').value;
    const spouse2Id = document.getElementById('spouse2-select').value;

    // Validate both selected
    if (!spouse1Id || !spouse2Id) {
        showError('Please select both spouses');
        return;
    }

    if (spouse1Id === spouse2Id) {
        showError('Please select two different clients');
        return;
    }

    // Show loading state
    const btn = document.getElementById('load-analysis-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Loading...';

    document.getElementById('spouse1-content').innerHTML = '<p class="loading">Loading analysis...</p>';
    document.getElementById('spouse2-content').innerHTML = '<p class="loading">Loading analysis...</p>';
    document.getElementById('comparison-content').innerHTML = '<p class="loading">Loading comparison...</p>';

    try {
        // Fetch joint analysis data
        const analysisResponse = await fetch(`${API_BASE}/joint-analysis/${spouse1Id}/${spouse2Id}`);
        if (!analysisResponse.ok) {
            const errorData = await analysisResponse.json();
            throw new Error(errorData.error || 'Failed to load joint analysis');
        }
        const analysisData = await analysisResponse.json();

        // Fetch client details for names
        const [client1Resp, client2Resp] = await Promise.all([
            fetch(`${API_BASE}/clients/${spouse1Id}`),
            fetch(`${API_BASE}/clients/${spouse2Id}`)
        ]);

        if (!client1Resp.ok || !client2Resp.ok) {
            throw new Error('Failed to load client details');
        }

        const client1 = await client1Resp.json();
        const client2 = await client2Resp.json();

        // Extract result (API wraps response in { result: {...} })
        const result = analysisData.result;

        // Display spouse summaries
        displaySpouseSummary('spouse1', result.spouse1, client1);
        displaySpouseSummary('spouse2', result.spouse2, client2);

        // Display comparison
        displayComparison(
            result.mfj,
            result.mfs_spouse1,
            result.mfs_spouse2,
            result.comparison
        );

        showSuccess('Joint analysis loaded successfully');

    } catch (error) {
        console.error('Error loading joint analysis:', error);
        showError(error.message || 'Failed to load joint analysis');

        // Reset content areas on error
        document.getElementById('spouse1-content').innerHTML = '<p class="loading">Error loading analysis</p>';
        document.getElementById('spouse2-content').innerHTML = '<p class="loading">Error loading analysis</p>';
        document.getElementById('comparison-content').innerHTML = '<p class="loading">Error loading comparison</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// ============================================================
// SPOUSE PANEL RENDERING (REQ-19)
// ============================================================

/**
 * Render spouse summary with income breakdown.
 * @param {string} panelId - 'spouse1' or 'spouse2'
 * @param {Object} data - { summary: {...}, strategies: [...] } from API result
 * @param {Object} client - { id, first_name, last_name } for display name
 */
function displaySpouseSummary(panelId, data, client) {
    const nameEl = document.getElementById(`${panelId}-name`);
    const contentEl = document.getElementById(`${panelId}-content`);

    if (!data || !data.summary) {
        contentEl.innerHTML = '<p class="loading">No data available</p>';
        return;
    }

    const summary = data.summary;
    const fullName = `${client.first_name} ${client.last_name}`;
    nameEl.textContent = fullName;

    // Build income sources breakdown (REQ-19)
    const incomeSources = summary.income_sources || [];
    const incomeHtml = incomeSources.length > 0
        ? incomeSources.map(source => `
            <div class="income-item">
                <span class="income-label">${source.source}</span>
                <span class="income-amount">$${formatCurrency(source.amount)}</span>
            </div>
        `).join('')
        : '<div class="income-item"><span>No detailed income sources</span></div>';

    // Determine tax owed/refund status
    const taxOwed = summary.tax_owed || 0;
    const taxRefund = summary.tax_refund || 0;
    const taxStatus = taxOwed > 0 ? 'owed' : 'refund';

    contentEl.innerHTML = `
        <div class="income-breakdown">
            <h4>Income Sources</h4>
            ${incomeHtml}
            <div class="income-total">
                <span>Total Income</span>
                <span>$${formatCurrency(summary.total_income)}</span>
            </div>
        </div>

        <div class="spouse-summary-grid">
            <div class="summary-card">
                <div class="summary-label">AGI</div>
                <div class="summary-value">$${formatCurrency(summary.adjusted_gross_income)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Taxable Income</div>
                <div class="summary-value">$${formatCurrency(summary.taxable_income)}</div>
            </div>
            <div class="summary-card ${taxOwed > 0 ? 'owed' : ''}">
                <div class="summary-label">Tax Liability</div>
                <div class="summary-value">$${formatCurrency(summary.total_tax)}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Effective Rate</div>
                <div class="summary-value">${formatPercent(summary.effective_tax_rate)}%</div>
            </div>
        </div>
    `;
}

// ============================================================
// COMPARISON SECTION (REQ-18, REQ-20)
// ============================================================

/**
 * Render comparison section with MFJ vs MFS cards and table.
 * @param {Object} mfj - MFJ calculation results
 * @param {Object} mfs1 - MFS spouse 1 results
 * @param {Object} mfs2 - MFS spouse 2 results
 * @param {Object} comparison - { recommended_status, savings_amount, reason, notes }
 */
function displayComparison(mfj, mfs1, mfs2, comparison) {
    const comparisonDiv = document.getElementById('comparison-content');

    if (!mfj || !comparison) {
        comparisonDiv.innerHTML = '<p class="loading">No comparison data available</p>';
        return;
    }

    // Calculate MFS combined tax
    const mfsCombinedTax = (mfs1?.total_tax || 0) + (mfs2?.total_tax || 0);
    const recommendedStatus = comparison.recommended_status || 'MFJ';
    const savingsAmount = comparison.savings_amount || 0;
    const reason = comparison.reason || '';

    // Build comparison notes if available
    const notes = comparison.notes || [];
    const notesHtml = notes.length > 0
        ? `<div class="comparison-notes">
            <h4>Analysis Notes</h4>
            <ul>
                ${notes.map(note => `<li><strong>${formatNoteType(note.type)}:</strong> ${note.message}</li>`).join('')}
            </ul>
           </div>`
        : '';

    comparisonDiv.innerHTML = `
        <!-- REQ-18: Comparison cards with recommendation -->
        <div class="comparison-cards">
            <div class="summary-card ${recommendedStatus === 'MFJ' ? 'refund' : ''}">
                <div class="summary-label">Married Filing Jointly (MFJ)</div>
                <div class="summary-value">$${formatCurrency(mfj.total_tax)}</div>
                ${recommendedStatus === 'MFJ' ? '<span class="recommendation-badge">Recommended</span>' : ''}
            </div>
            <div class="summary-card ${recommendedStatus === 'MFS' ? 'refund' : ''}">
                <div class="summary-label">Married Filing Separately (MFS)</div>
                <div class="summary-value">$${formatCurrency(mfsCombinedTax)}</div>
                <div class="summary-sublabel">Combined: Spouse 1 + Spouse 2</div>
                ${recommendedStatus === 'MFS' ? '<span class="recommendation-badge">Recommended</span>' : ''}
            </div>
            <div class="summary-card ${savingsAmount > 0 ? 'refund' : ''}">
                <div class="summary-label">Potential Savings</div>
                <div class="summary-value">$${formatCurrency(savingsAmount)}</div>
                <div class="savings-note">${reason}</div>
            </div>
        </div>

        ${notesHtml}

        <!-- REQ-20: Four-column line-by-line breakdown -->
        <h4>Filing Status Comparison Report</h4>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Line Item</th>
                    <th>MFJ Total</th>
                    <th>MFS Spouse 1</th>
                    <th>MFS Spouse 2</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Gross Income</td>
                    <td>$${formatCurrency(mfj.combined_income)}</td>
                    <td>$${formatCurrency(mfs1?.income)}</td>
                    <td>$${formatCurrency(mfs2?.income)}</td>
                </tr>
                <tr>
                    <td>Adjusted Gross Income (AGI)</td>
                    <td>$${formatCurrency(mfj.agi)}</td>
                    <td>$${formatCurrency(mfs1?.agi)}</td>
                    <td>$${formatCurrency(mfs2?.agi)}</td>
                </tr>
                <tr>
                    <td>Standard Deduction</td>
                    <td>$${formatCurrency(mfj.standard_deduction)}</td>
                    <td>$${formatCurrency(mfs1?.standard_deduction)}</td>
                    <td>$${formatCurrency(mfs2?.standard_deduction)}</td>
                </tr>
                <tr>
                    <td>Taxable Income</td>
                    <td>$${formatCurrency(mfj.taxable_income)}</td>
                    <td>$${formatCurrency(mfs1?.taxable_income)}</td>
                    <td>$${formatCurrency(mfs2?.taxable_income)}</td>
                </tr>
                <tr class="highlight">
                    <td>Total Tax Liability</td>
                    <td>$${formatCurrency(mfj.total_tax)}</td>
                    <td>$${formatCurrency(mfs1?.total_tax)}</td>
                    <td>$${formatCurrency(mfs2?.total_tax)}</td>
                </tr>
                <tr class="highlight">
                    <td>Effective Tax Rate</td>
                    <td>${formatPercent(mfj.effective_rate)}%</td>
                    <td>${formatPercent(mfs1?.effective_rate)}%</td>
                    <td>${formatPercent(mfs2?.effective_rate)}%</td>
                </tr>
            </tbody>
        </table>
    `;
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

/**
 * Format currency with thousands separators and 2 decimal places.
 * Handles null/undefined gracefully.
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '0.00';
    return Number(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format percentage with 2 decimal places.
 * Handles null/undefined gracefully.
 */
function formatPercent(rate) {
    if (rate === null || rate === undefined) return '0.00';
    return Number(rate).toFixed(2);
}

/**
 * Format note type for display.
 */
function formatNoteType(type) {
    const typeMap = {
        'credit_restriction': 'Credit Restriction',
        'qbi_threshold': 'QBI Threshold',
        'deduction_coordination': 'Deduction Coordination',
        'salt_cap_difference': 'SALT Cap'
    };
    return typeMap[type] || type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Show error message at top of page.
 * Auto-dismisses after 5 seconds.
 */
function showError(message) {
    // Check if error element already exists
    let errorDiv = document.querySelector('.error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error error-message';
        document.body.insertBefore(errorDiv, document.body.firstChild);
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

/**
 * Show success message at top of page.
 * Auto-dismisses after 3 seconds.
 */
function showSuccess(message) {
    let successDiv = document.querySelector('.success-message');
    if (!successDiv) {
        successDiv = document.createElement('div');
        successDiv.className = 'success success-message';
        document.body.insertBefore(successDiv, document.body.firstChild);
    }
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}
