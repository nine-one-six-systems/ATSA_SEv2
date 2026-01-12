// Tax Calculator functionality
const API_BASE = '/api';

let states = [];
let selectedStates = [];
let currentIncome = 0;
let currentFrequency = 'annual';

// Conversion factors for income frequencies
const FREQUENCY_FACTORS = {
    'annual': 1.0,
    'monthly': 12.0,
    'bi_monthly': 24.0,
    'bi_weekly': 26.0,
    'weekly': 52.0
};

document.addEventListener('DOMContentLoaded', () => {
    loadStates();
    setupEventListeners();
});

async function loadStates() {
    try {
        const response = await fetch(`${API_BASE}/calculator/states`);
        states = await response.json();
        
        // Populate state dropdowns
        const stateSelect = document.getElementById('state-select');
        const addStateSelect = document.getElementById('add-state-select');
        
        states.forEach(state => {
            const option1 = document.createElement('option');
            option1.value = state.code;
            option1.textContent = state.name;
            stateSelect.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = state.code;
            option2.textContent = state.name;
            addStateSelect.appendChild(option2);
        });
    } catch (error) {
        console.error('Error loading states:', error);
    }
}

function setupEventListeners() {
    // Income frequency toggle
    const frequencyButtons = document.querySelectorAll('.frequency-toggle .toggle-btn');
    frequencyButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            handleIncomeFrequencyChange(btn.dataset.frequency);
        });
    });
    
    // Income source dropdown
    const incomeSourceSelect = document.getElementById('income-source');
    if (incomeSourceSelect) {
        incomeSourceSelect.addEventListener('change', () => {
            handleIncomeSourceChange(incomeSourceSelect.value);
        });
    }
    
    // Filing status toggle
    const statusButtons = document.querySelectorAll('.filing-status-toggle .toggle-btn');
    statusButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            handleFilingStatusChange(btn.dataset.status);
        });
    });
    
    // Multiple states checkbox
    const multipleStatesCheckbox = document.getElementById('multiple-states');
    multipleStatesCheckbox.addEventListener('change', () => {
        handleMultipleStatesChange(multipleStatesCheckbox.checked);
    });
    
    // Add state button
    const addStateBtn = document.getElementById('add-state-btn');
    addStateBtn.addEventListener('click', () => {
        addSelectedState();
    });
    
    // Income field - recalculate distributions on change
    const incomeInput = document.getElementById('income-amount');
    if (incomeInput) {
        incomeInput.addEventListener('input', () => {
            const incomeSource = document.getElementById('income-source').value;
            if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
                calculateDistributions();
            }
        });
        incomeInput.addEventListener('change', () => {
            const incomeSource = document.getElementById('income-source').value;
            if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
                calculateDistributions();
            }
        });
    }
    
    // Salary field - recalculate distributions on change
    const salaryInput = document.getElementById('salary-amount');
    if (salaryInput) {
        salaryInput.addEventListener('input', () => {
            const incomeSource = document.getElementById('income-source').value;
            if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
                calculateDistributions();
            }
        });
        salaryInput.addEventListener('change', () => {
            const incomeSource = document.getElementById('income-source').value;
            if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
                calculateDistributions();
            }
        });
    }
    
    // Form submission
    const form = document.getElementById('calculator-form');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        calculateTax();
    });
}

function handleIncomeFrequencyChange(frequency) {
    const incomeInput = document.getElementById('income-amount');
    const incomeValue = parseFloat(incomeInput.value) || 0;
    
    if (incomeValue > 0 && currentFrequency !== frequency) {
        // Convert current income to annual
        const annualIncome = incomeValue * FREQUENCY_FACTORS[currentFrequency];
        // Convert annual to new frequency
        const newIncome = annualIncome / FREQUENCY_FACTORS[frequency];
        incomeInput.value = Math.round(newIncome * 100) / 100;
    }
    
    // Update active button
    document.querySelectorAll('.frequency-toggle .toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.frequency === frequency) {
            btn.classList.add('active');
        }
    });
    
    document.getElementById('income-frequency').value = frequency;
    currentFrequency = frequency;
    
    // Recalculate distributions if S-Corp type is selected
    const incomeSource = document.getElementById('income-source').value;
    if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
        calculateDistributions();
    }
}

function calculateDistributions() {
    const incomeSource = document.getElementById('income-source').value;
    
    // Only calculate for S-Corp types
    if (incomeSource !== 'llc_s_corp' && incomeSource !== 's_corp') {
        return;
    }
    
    const incomeInput = document.getElementById('income-amount');
    const salaryInput = document.getElementById('salary-amount');
    const distributionsInput = document.getElementById('distributions-amount');
    const frequency = document.getElementById('income-frequency').value;
    
    const income = parseFloat(incomeInput.value) || 0;
    const salary = parseFloat(salaryInput.value) || 0;
    
    // Convert income to annual
    const annualIncome = income * FREQUENCY_FACTORS[frequency];
    
    // Calculate distributions (cannot be negative)
    const distributions = Math.max(0, annualIncome - salary);
    
    // Update display
    distributionsInput.value = distributions.toFixed(2);
}

function handleIncomeSourceChange(incomeSource) {
    const salaryDistributionsGroup = document.getElementById('salary-distributions-group');
    const salaryInput = document.getElementById('salary-amount');
    const distributionsInput = document.getElementById('distributions-amount');
    
    // Show Salary/Distributions fields for S-Corp types
    if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
        salaryDistributionsGroup.style.display = 'block';
        salaryInput.required = true;
        distributionsInput.required = false; // Distributions is calculated, not required input
        // Calculate distributions immediately when S-Corp type is selected
        calculateDistributions();
    } else {
        salaryDistributionsGroup.style.display = 'none';
        salaryInput.required = false;
        distributionsInput.required = false;
        salaryInput.value = '';
        distributionsInput.value = '';
    }
}

function handleFilingStatusChange(status) {
    document.querySelectorAll('.filing-status-toggle .toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.status === status) {
            btn.classList.add('active');
        }
    });
    document.getElementById('filing-status').value = status;
}

function handleMultipleStatesChange(enabled) {
    const multipleStatesGroup = document.getElementById('multiple-states-group');
    const stateSelect = document.getElementById('state-select');
    
    if (enabled) {
        multipleStatesGroup.style.display = 'block';
        stateSelect.disabled = true;
        selectedStates = [];
        updateSelectedStatesList();
    } else {
        multipleStatesGroup.style.display = 'none';
        stateSelect.disabled = false;
        selectedStates = [];
        updateSelectedStatesList();
    }
}

function addSelectedState() {
    const addStateSelect = document.getElementById('add-state-select');
    const stateCode = addStateSelect.value;
    
    if (!stateCode || selectedStates.includes(stateCode)) {
        return;
    }
    
    selectedStates.push(stateCode);
    updateSelectedStatesList();
    addStateSelect.value = '';
}

function removeSelectedState(stateCode) {
    selectedStates = selectedStates.filter(s => s !== stateCode);
    updateSelectedStatesList();
}

function updateSelectedStatesList() {
    const listDiv = document.getElementById('selected-states-list');
    if (selectedStates.length === 0) {
        listDiv.innerHTML = '<p style="color: #6c757d; font-size: 0.9rem;">No states selected</p>';
        return;
    }
    
    listDiv.innerHTML = selectedStates.map(stateCode => {
        const state = states.find(s => s.code === stateCode);
        return `
            <span class="state-tag">
                ${state ? state.name : stateCode}
                <button type="button" class="remove-state-btn" onclick="removeSelectedState('${stateCode}')">×</button>
            </span>
        `;
    }).join('');
}

async function calculateTax() {
    const incomeInput = document.getElementById('income-amount');
    const income = parseFloat(incomeInput.value);
    const frequency = document.getElementById('income-frequency').value;
    const incomeSource = document.getElementById('income-source').value;
    const filingStatus = document.getElementById('filing-status').value;
    // Number of qualifying children (ages 17 and under) for Child Tax Credit
    const dependents = parseInt(document.getElementById('dependents').value) || 0;
    const multipleStates = document.getElementById('multiple-states').checked;
    const stateSelect = document.getElementById('state-select');
    const stateCode = multipleStates ? null : stateSelect.value;
    
    // Get salary and distributions for S-Corp types
    const salaryInput = document.getElementById('salary-amount');
    const distributionsInput = document.getElementById('distributions-amount');
    
    // Recalculate distributions if S-Corp type (to ensure it's up to date)
    if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
        calculateDistributions();
    }
    
    const salary = parseFloat(salaryInput.value) || 0;
    const distributions = parseFloat(distributionsInput.value) || 0;
    
    // Validation
    if (incomeSource === 'llc_s_corp' || incomeSource === 's_corp') {
        // For S-Corp types, validate salary (distributions is calculated automatically)
        if (!salary || salary <= 0) {
            alert('Please enter a valid salary amount');
            return;
        }
        // Validate that salary doesn't exceed annual income
        const annualIncome = income * FREQUENCY_FACTORS[frequency];
        if (salary > annualIncome) {
            alert('Salary cannot exceed total annual income');
            return;
        }
    } else {
        // For W2/LLC, validate main income field
        if (!income || income <= 0) {
            alert('Please enter a valid income amount');
            return;
        }
    }
    
    if (!multipleStates && !stateCode) {
        // State is optional for calculation, but warn user
        if (!confirm('No state selected. Only federal tax will be calculated. Continue?')) {
            return;
        }
    }
    
    if (multipleStates && selectedStates.length === 0) {
        alert('Please select at least one state');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/calculator/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                income: income,
                income_frequency: frequency,
                income_source: incomeSource,
                salary: salary,
                distributions: distributions,
                filing_status: filingStatus,
                dependents: dependents,
                state_code: stateCode,
                multiple_states: multipleStates,
                selected_states: selectedStates,
                tax_year: 2026
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            alert('Error calculating tax: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error calculating tax:', error);
        alert('Failed to calculate tax. Please try again.');
    }
}

function displayResults(result) {
    const resultsDiv = document.getElementById('calculator-results');
    resultsDiv.style.display = 'block';
    
    const federal = result.federal;
    const stateResults = result.state || [];
    const totals = result.totals;
    
    let html = `
        <div class="results-header">
            <h3>Tax Calculation Results</h3>
            <p class="annual-income-display">Annual Income: <strong>${formatCurrency(result.annual_income)}</strong></p>
        </div>
        
        <div class="results-grid">
            <!-- Federal Tax Section -->
            <div class="result-card federal-card">
                <h4>Federal Tax</h4>
                <div class="result-summary">
                    ${federal.salary !== undefined ? `
                        <!-- S-Corp Type: Separate Salary and Distributions -->
                        <div class="result-item" style="font-weight: 600; margin-top: 0.5rem;">
                            <span>Salary (Ordinary Income):</span>
                            <span>${formatCurrency(federal.salary)}</span>
                        </div>
                        ${federal.qbi_amount !== undefined && federal.qbi_amount > 0 ? `
                            <div class="result-item" style="color: #3498db;">
                                <span>QBI Amount (Distributions):</span>
                                <span>${formatCurrency(federal.qbi_amount)}</span>
                            </div>
                            <div class="result-item" style="color: #27ae60;">
                                <span>QBI Deduction (20%):</span>
                                <span>-${formatCurrency(federal.qbi_deduction)}</span>
                            </div>
                        ` : ''}
                        ${federal.salary_taxable_before_qbi !== undefined ? `
                            <div class="result-item">
                                <span>Salary Taxable (Before QBI):</span>
                                <span>${formatCurrency(federal.salary_taxable_before_qbi)}</span>
                            </div>
                        ` : ''}
                        <div class="result-item">
                            <span>Salary Taxable Income:</span>
                            <span>${formatCurrency(federal.salary_taxable || federal.salary)}</span>
                        </div>
                        ${federal.ordinary_income_tax_before_credit !== undefined ? `
                            <div class="result-item">
                                <span>Ordinary Income Tax (Before Credit):</span>
                                <span>${formatCurrency(federal.ordinary_income_tax_before_credit)}</span>
                            </div>
                            ${federal.child_tax_credit > 0 ? `
                                <div class="result-item" style="color: #27ae60;">
                                    <span>Child Tax Credit (Applied to Ordinary Income):</span>
                                    <span>-${formatCurrency(federal.child_tax_credit_applied || federal.child_tax_credit)}</span>
                                </div>
                            ` : ''}
                            <div class="result-item">
                                <span>Ordinary Income Tax (After Credit):</span>
                                <span>${formatCurrency(federal.ordinary_income_tax_after_credit)}</span>
                            </div>
                        ` : ''}
                        
                        <div class="result-item" style="font-weight: 600; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;">
                            <span>Distributions (Capital Gains):</span>
                            <span>${formatCurrency(federal.distributions)}</span>
                        </div>
                        <div class="result-item">
                            <span>Distributions Taxable:</span>
                            <span>${formatCurrency(federal.distributions_taxable || federal.distributions)}</span>
                        </div>
                        ${federal.capital_gains_tax !== undefined ? `
                            <div class="result-item">
                                <span>Capital Gains Tax Rate:</span>
                                <span>${formatPercentage(federal.capital_gains_rate_applied)}%</span>
                            </div>
                            <div class="result-item">
                                <span>Capital Gains Tax:</span>
                                <span>${formatCurrency(federal.capital_gains_tax)}</span>
                            </div>
                        ` : ''}
                        
                        <div class="result-item" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;">
                            <span>Standard Deduction:</span>
                            <span>${formatCurrency(federal.standard_deduction)}</span>
                        </div>
                        <div class="result-item">
                            <span>Total Taxable Income:</span>
                            <span>${formatCurrency(federal.total_taxable_income || federal.taxable_income)}</span>
                        </div>
                    ` : `
                        <!-- Non-S-Corp Type: Standard Display -->
                        <div class="result-item">
                            <span>Gross Income:</span>
                            <span>${formatCurrency(federal.gross_income)}</span>
                        </div>
                        ${federal.qbi_amount !== undefined && federal.qbi_amount > 0 ? `
                            <div class="result-item" style="color: #3498db;">
                                <span>QBI Amount:</span>
                                <span>${formatCurrency(federal.qbi_amount)}</span>
                            </div>
                            <div class="result-item" style="color: #27ae60;">
                                <span>QBI Deduction (20%):</span>
                                <span>-${formatCurrency(federal.qbi_deduction)}</span>
                            </div>
                        ` : ''}
                        <div class="result-item">
                            <span>Standard Deduction:</span>
                            <span>${formatCurrency(federal.standard_deduction)}</span>
                        </div>
                        ${federal.taxable_income_before_qbi !== undefined ? `
                            <div class="result-item">
                                <span>Taxable Income (Before QBI):</span>
                                <span>${formatCurrency(federal.taxable_income_before_qbi)}</span>
                            </div>
                        ` : ''}
                        <div class="result-item">
                            <span>Taxable Income:</span>
                            <span>${formatCurrency(federal.taxable_income)}</span>
                        </div>
                        ${federal.income_tax_before_credit !== undefined ? `
                            <div class="result-item">
                                <span>Income Tax (Before Credit):</span>
                                <span>${formatCurrency(federal.income_tax_before_credit)}</span>
                            </div>
                            ${federal.child_tax_credit > 0 ? `
                                <div class="result-item" style="color: #27ae60;">
                                    <span>Child Tax Credit:</span>
                                    <span>-${formatCurrency(federal.child_tax_credit_applied || federal.child_tax_credit)}</span>
                                </div>
                            ` : ''}
                            <div class="result-item">
                                <span>Income Tax (After Credit):</span>
                                <span>${formatCurrency(federal.income_tax_after_credit || federal.income_tax)}</span>
                            </div>
                        ` : `
                            <div class="result-item">
                                <span>Income Tax:</span>
                                <span>${formatCurrency(federal.income_tax || federal.total_tax)}</span>
                            </div>
                        `}
                    `}
                    ${federal.fica_tax > 0 ? `
                        <div class="result-item">
                            <span>FICA Tax (on Salary):</span>
                            <span>${formatCurrency(federal.fica_tax)}</span>
                        </div>
                    ` : ''}
                    ${federal.se_tax > 0 ? `
                        <div class="result-item">
                            <span>Self-Employment Tax:</span>
                            <span>${formatCurrency(federal.se_tax)}</span>
                        </div>
                    ` : ''}
                    <div class="result-item highlight">
                        <span>Total Federal Tax:</span>
                        <span>${formatCurrency(federal.total_tax)}</span>
                    </div>
                    <div class="result-item">
                        <span>Effective Rate:</span>
                        <span>${formatPercentage(federal.effective_tax_rate)}%</span>
                    </div>
                    <div class="result-item">
                        <span>Marginal Rate:</span>
                        <span>${formatPercentage(federal.marginal_tax_rate)}%</span>
                    </div>
                </div>
                
                ${federal.capital_gains_breakdown && federal.capital_gains_breakdown.length > 0 ? `
                    <div class="capital-gains-breakdown">
                        <h5>Capital Gains Tax Breakdown:</h5>
                        <div class="result-summary">
                            ${federal.capital_gains_breakdown.map(bracket => `
                                <div class="result-item">
                                    <span>${formatCurrency(bracket.threshold_min)} - ${bracket.threshold_max ? formatCurrency(bracket.threshold_max) : '∞'} @ ${formatPercentage(bracket.rate * 100)}%:</span>
                                    <span>${formatCurrency(bracket.tax)}</span>
                                </div>
                            `).join('')}
                            <div class="result-item highlight">
                                <span>Total Capital Gains Tax:</span>
                                <span>${formatCurrency(federal.capital_gains_tax)}</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${federal.fica_tax_breakdown ? `
                    <div class="fica-breakdown">
                        <h5>FICA Tax Breakdown:</h5>
                        <div class="result-summary">
                            <div class="result-item">
                                <span>Social Security Tax:</span>
                                <span>${formatCurrency(federal.fica_tax_breakdown.social_security_tax)}</span>
                            </div>
                            <div class="result-item">
                                <span>Medicare Tax:</span>
                                <span>${formatCurrency(federal.fica_tax_breakdown.medicare_tax)}</span>
                            </div>
                            ${federal.fica_tax_breakdown.medicare_surtax > 0 ? `
                                <div class="result-item">
                                    <span>Medicare Surtax:</span>
                                    <span>${formatCurrency(federal.fica_tax_breakdown.medicare_surtax)}</span>
                                </div>
                            ` : ''}
                            <div class="result-item highlight">
                                <span>Total FICA Tax:</span>
                                <span>${formatCurrency(federal.fica_tax_breakdown.total_fica_tax)}</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${federal.se_tax_breakdown ? `
                    <div class="se-tax-breakdown">
                        <h5>Self-Employment Tax Breakdown:</h5>
                        <div class="result-summary">
                            <div class="result-item">
                                <span>Gross SE Tax:</span>
                                <span>${formatCurrency(federal.se_tax_breakdown.gross_se_tax)}</span>
                            </div>
                            <div class="result-item">
                                <span>Employer Portion Deduction:</span>
                                <span>${formatCurrency(federal.se_tax_breakdown.employer_portion_deduction)}</span>
                            </div>
                            <div class="result-item highlight">
                                <span>Net SE Tax:</span>
                                <span>${formatCurrency(federal.se_tax_breakdown.net_se_tax)}</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                <div class="bracket-breakdown">
                    <h5>Tax by Bracket:</h5>
                    <table class="bracket-table">
                        <thead>
                            <tr>
                                <th>Bracket</th>
                                <th>Rate</th>
                                <th>Taxable Amount</th>
                                <th>Tax</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${federal.bracket_breakdown.map(bracket => `
                                <tr>
                                    <td>${formatCurrency(bracket.bracket_min)} - ${bracket.bracket_max ? formatCurrency(bracket.bracket_max) : '∞'}</td>
                                    <td>${formatPercentage(bracket.tax_rate * 100)}%</td>
                                    <td>${formatCurrency(bracket.taxable_in_bracket)}</td>
                                    <td>${formatCurrency(bracket.tax_in_bracket)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- State Tax Section(s) -->
            ${stateResults.length > 0 ? stateResults.map(state => `
                <div class="result-card state-card">
                    <h4>State Tax - ${state.state_code || 'N/A'}</h4>
                    ${state.no_income_tax ? `
                        <p class="no-tax-message">This state has no income tax.</p>
                    ` : `
                        <div class="result-summary">
                            <div class="result-item">
                                <span>Gross Income:</span>
                                <span>${formatCurrency(state.gross_income)}</span>
                            </div>
                            <div class="result-item">
                                <span>Standard Deduction:</span>
                                <span>${formatCurrency(state.standard_deduction)}</span>
                            </div>
                            <div class="result-item">
                                <span>Taxable Income:</span>
                                <span>${formatCurrency(state.taxable_income)}</span>
                            </div>
                            <div class="result-item highlight">
                                <span>State Tax:</span>
                                <span>${formatCurrency(state.total_tax)}</span>
                            </div>
                            <div class="result-item">
                                <span>Effective Rate:</span>
                                <span>${formatPercentage(state.effective_tax_rate)}%</span>
                            </div>
                            <div class="result-item">
                                <span>Marginal Rate:</span>
                                <span>${formatPercentage(state.marginal_tax_rate)}%</span>
                            </div>
                        </div>
                        
                        ${state.bracket_breakdown && state.bracket_breakdown.length > 0 ? `
                            <div class="bracket-breakdown">
                                <h5>Tax by Bracket:</h5>
                                <table class="bracket-table">
                                    <thead>
                                        <tr>
                                            <th>Bracket</th>
                                            <th>Rate</th>
                                            <th>Taxable Amount</th>
                                            <th>Tax</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${state.bracket_breakdown.map(bracket => `
                                            <tr>
                                                <td>${formatCurrency(bracket.bracket_min)} - ${bracket.bracket_max ? formatCurrency(bracket.bracket_max) : '∞'}</td>
                                                <td>${formatPercentage(bracket.tax_rate * 100)}%</td>
                                                <td>${formatCurrency(bracket.taxable_in_bracket)}</td>
                                                <td>${formatCurrency(bracket.tax_in_bracket)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : ''}
                    `}
                </div>
            `).join('') : ''}
            
            <!-- Totals Section -->
            <div class="result-card totals-card">
                <h4>Total Tax Liability</h4>
                <div class="result-summary">
                    <div class="result-item">
                        <span>Federal Tax:</span>
                        <span>${formatCurrency(totals.federal_tax)}</span>
                    </div>
                    <div class="result-item">
                        <span>State Tax:</span>
                        <span>${formatCurrency(totals.state_tax)}</span>
                    </div>
                    <div class="result-item highlight large">
                        <span>Total Tax:</span>
                        <span>${formatCurrency(totals.total_tax)}</span>
                    </div>
                    <div class="result-item">
                        <span>Effective Tax Rate:</span>
                        <span>${formatPercentage(totals.effective_tax_rate)}%</span>
                    </div>
                    <div class="result-item">
                        <span>Marginal Tax Rate:</span>
                        <span>${formatPercentage(totals.marginal_tax_rate)}%</span>
                    </div>
                    <div class="result-item">
                        <span>After-Tax Income:</span>
                        <span>${formatCurrency(result.annual_income - totals.total_tax)}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    
    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatPercentage(value) {
    return value.toFixed(2);
}
