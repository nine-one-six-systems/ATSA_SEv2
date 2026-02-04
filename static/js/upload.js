// Document upload functionality
const API_BASE = '/api';

let selectedFiles = [];

// Load clients and documents on page load
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    loadDocuments();

    // Setup file input
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    // Setup client selection change handler for attribution visibility
    document.getElementById('client-select').addEventListener('change', () => {
        loadDocuments();
        updateUploadButton();
        checkClientHasSpouse();
    });
});

async function loadClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`);
        const clients = await response.json();

        const select = document.getElementById('client-select');
        select.innerHTML = '<option value="">Select a client...</option>';

        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            option.textContent = `${client.first_name} ${client.last_name}`;
            // Store spouse_id as data attribute for quick lookup
            option.dataset.spouseId = client.spouse_id || '';
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

async function loadDocuments() {
    const clientId = document.getElementById('client-select').value;
    if (!clientId) {
        document.getElementById('documents-list').innerHTML = '<p class="loading">Select a client to view documents</p>';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/documents/client/${clientId}`);
        const documents = await response.json();

        const documentsList = document.getElementById('documents-list');

        if (documents.length === 0) {
            documentsList.innerHTML = '<p class="loading">No documents uploaded yet</p>';
        } else {
            documentsList.innerHTML = documents.map(doc => `
                <div class="document-item">
                    <div class="document-info">
                        <strong>${doc.filename}</strong>
                        <p>Tax Year: ${doc.tax_year || 'N/A'} | Attribution: ${formatAttribution(doc.attribution)} | Uploaded: ${new Date(doc.uploaded_at).toLocaleDateString()}</p>
                    </div>
                    <div>
                        <span class="document-status status-${doc.ocr_status}">${doc.ocr_status}</span>
                        ${doc.ocr_status === 'pending' ? `<button class="btn btn-primary" onclick="processDocument(${doc.id})" style="margin-left: 1rem;">Process</button>` : ''}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

function formatAttribution(attribution) {
    const labels = {
        'taxpayer': 'Taxpayer',
        'spouse': 'Spouse',
        'joint': 'Joint'
    };
    return labels[attribution] || attribution || 'Taxpayer';
}

// Check if selected client has a spouse and show/hide attribution selector
async function checkClientHasSpouse() {
    const clientSelect = document.getElementById('client-select');
    const selectedOption = clientSelect.options[clientSelect.selectedIndex];
    const attributionGroup = document.getElementById('attribution-group');

    if (!selectedOption || !selectedOption.value) {
        attributionGroup.style.display = 'none';
        return;
    }

    // Check data attribute first (faster)
    const spouseId = selectedOption.dataset.spouseId;
    if (spouseId) {
        attributionGroup.style.display = 'block';
        return;
    }

    // Fallback: fetch client data
    try {
        const response = await fetch(`${API_BASE}/clients/${selectedOption.value}`);
        if (response.ok) {
            const client = await response.json();
            if (client.spouse_id) {
                attributionGroup.style.display = 'block';
            } else {
                attributionGroup.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error checking spouse:', error);
        attributionGroup.style.display = 'none';
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = '#2980b9';
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = '#3498db';

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (isValidFile(file)) {
            selectedFiles.push(file);
        }
    });
    updateFileList();
    updateUploadButton();
}

function isValidFile(file) {
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    const maxSize = 16 * 1024 * 1024; // 16MB

    if (!validTypes.includes(file.type)) {
        alert(`${file.name} is not a valid file type. Please upload PDF, JPG, or PNG files.`);
        return false;
    }

    if (file.size > maxSize) {
        alert(`${file.name} is too large. Maximum file size is 16MB.`);
        return false;
    }

    return true;
}

function updateFileList() {
    const fileList = document.getElementById('file-list');

    if (selectedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }

    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span>${file.name} (${formatFileSize(file.size)})</span>
            <button class="btn btn-danger" onclick="removeFile(${index})" style="padding: 0.25rem 0.75rem; font-size: 0.85rem;">Remove</button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateUploadButton();
}

function clearFiles() {
    selectedFiles = [];
    updateFileList();
    updateUploadButton();
    document.getElementById('file-input').value = '';
}

function updateUploadButton() {
    const clientId = document.getElementById('client-select').value;
    const uploadBtn = document.getElementById('upload-btn');
    uploadBtn.disabled = !clientId || selectedFiles.length === 0;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

async function uploadFiles() {
    const clientId = document.getElementById('client-select').value;
    const taxYear = document.getElementById('tax-year').value;
    const attribution = document.getElementById('attribution-select').value;

    if (!clientId) {
        alert('Please select a client');
        return;
    }

    if (selectedFiles.length === 0) {
        alert('Please select files to upload');
        return;
    }

    const uploadBtn = document.getElementById('upload-btn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';

    try {
        for (const file of selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('client_id', clientId);
            formData.append('attribution', attribution);
            if (taxYear) {
                formData.append('tax_year', taxYear);
            }

            const response = await fetch(`${API_BASE}/documents/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
        }

        clearFiles();
        loadDocuments();
        showSuccess('Files uploaded successfully');
    } catch (error) {
        console.error('Error uploading files:', error);
        showError(error.message || 'Failed to upload files');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload Files';
        updateUploadButton();
    }
}

async function processDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}/process`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            showSuccess(`Document processed. Forms detected: ${result.forms_detected.join(', ')}`);
            loadDocuments();
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to process document');
        }
    } catch (error) {
        console.error('Error processing document:', error);
        showError('Failed to process document');
    }
}

// Tab switching functions
function showUploadTab() {
    document.getElementById('upload-tab').style.display = 'block';
    document.getElementById('manual-tab').style.display = 'none';
    document.getElementById('upload-tab-btn').classList.add('active');
    document.getElementById('manual-tab-btn').classList.remove('active');
}

function showManualTab() {
    document.getElementById('upload-tab').style.display = 'none';
    document.getElementById('manual-tab').style.display = 'block';
    document.getElementById('upload-tab-btn').classList.remove('active');
    document.getElementById('manual-tab-btn').classList.add('active');
}

// Manual entry functions
async function saveManualEntry() {
    const clientId = document.getElementById('client-select').value;
    const taxYear = document.getElementById('tax-year').value || 2026;
    const attribution = document.getElementById('attribution-select').value;

    if (!clientId) {
        alert('Please select a client first');
        return;
    }

    const incomeData = {
        wages: parseFloat(document.getElementById('manual-wages').value) || null,
        federal_withheld: parseFloat(document.getElementById('manual-federal-withheld').value) || null,
        schedule_c_income: parseFloat(document.getElementById('manual-schedule-c').value) || null,
        interest_income: parseFloat(document.getElementById('manual-interest').value) || null,
        dividend_income: parseFloat(document.getElementById('manual-dividends').value) || null
    };

    // Check if any data was entered
    const hasData = Object.values(incomeData).some(v => v !== null && v !== 0);
    if (!hasData) {
        alert('Please enter at least one income value');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/documents/manual-entry`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                tax_year: parseInt(taxYear),
                attribution: attribution,
                income_data: incomeData
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save manual entry');
        }

        const result = await response.json();
        showSuccess(`Income data saved successfully! ${result.records_created.length} records created.`);
        clearManualEntry();

    } catch (error) {
        console.error('Error saving manual entry:', error);
        showError('Error: ' + error.message);
    }
}

function clearManualEntry() {
    document.getElementById('manual-wages').value = '';
    document.getElementById('manual-federal-withheld').value = '';
    document.getElementById('manual-schedule-c').value = '';
    document.getElementById('manual-interest').value = '';
    document.getElementById('manual-dividends').value = '';
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
