const API_URL = 'http://localhost:8000';

// Color scheme matching the CSS variables
const clusterColors = [
    { bg: 'rgba(99, 102, 241, 0.7)',  border: '#6366f1', label: 'Cluster 0' },
    { bg: 'rgba(16, 185, 129, 0.7)',  border: '#10b981', label: 'Cluster 1' },
    { bg: 'rgba(239, 68, 68, 0.7)',   border: '#ef4444', label: 'Cluster 2' },
    { bg: 'rgba(245, 158, 11, 0.7)',  border: '#f59e0b', label: 'Cluster 3' },
    { bg: 'rgba(59, 130, 246, 0.7)',  border: '#3b82f6', label: 'Cluster 4' },
    { bg: 'rgba(139, 92, 246, 0.7)', border: '#8b5cf6', label: 'Cluster 5' },
];

let scatterChart = null;
let isLoading = false;
let batchResults = null;
let selectedFile = null;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadCustomerData();
    setupModeSwitch();
    setupForm();
    setupBatch();
    setupExport();
});

// ─────────────────────────────────────────────────────────────────────────────
// MODE SWITCHING
// ─────────────────────────────────────────────────────────────────────────────

function setupModeSwitch() {
    const modeTabs = document.querySelectorAll('.mode-tab');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.getAttribute('data-mode');
            switchMode(mode);
        });
    });
}

function switchMode(mode) {
    // Update active tab
    document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');

    // Update active content
    document.querySelectorAll('.mode-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${mode}Mode`).classList.add('active');

    // Reset form when switching to single mode
    if (mode === 'single') {
        clearFormErrors();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// FORM VALIDATION & ERROR HANDLING
// ─────────────────────────────────────────────────────────────────────────────

const validationRules = {
    income: (val) => {
        if (isNaN(val)) return 'Must be a number';
        if (val <= 0 || val > 1_000_000) return 'Must be between 1 and 1,000,000';
        return null;
    },
    spendingScore: (val) => {
        if (isNaN(val)) return 'Must be a number';
        if (val < 1 || val > 100) return 'Must be between 1 and 100';
        return null;
    },
    frequency: (val) => {
        if (isNaN(val)) return 'Must be a number';
        if (val < 0 || val > 365) return 'Must be between 0 and 365';
        return null;
    },
    recency: (val) => {
        if (isNaN(val)) return 'Must be a number';
        if (val < 0) return 'Cannot be negative';
        return null;
    },
    monetary: (val) => {
        if (isNaN(val)) return 'Must be a number';
        if (val < 0) return 'Cannot be negative';
        return null;
    },
};

function validateField(fieldName, value) {
    const rule = validationRules[fieldName];
    if (!rule) return null;
    return rule(value);
}

function clearFormErrors() {
    Object.keys(validationRules).forEach(field => {
        const errorEl = document.getElementById(`${field}Error`);
        if (errorEl) errorEl.textContent = '';
    });
    const errorSummary = document.getElementById('errorSummary');
    if (errorSummary) errorSummary.style.display = 'none';
}

function showFieldError(fieldName, message) {
    const errorEl = document.getElementById(`${fieldName}Error`);
    if (errorEl) errorEl.textContent = message || '';
}

function updateErrorSummary(errors) {
    const errorSummary = document.getElementById('errorSummary');
    const errorList = document.getElementById('errorList');
    
    if (Object.keys(errors).length === 0) {
        errorSummary.style.display = 'none';
        return;
    }

    errorList.innerHTML = '';
    Object.values(errors).forEach(error => {
        const li = document.createElement('li');
        li.textContent = error;
        errorList.appendChild(li);
    });
    errorSummary.style.display = 'block';
}

// ─────────────────────────────────────────────────────────────────────────────
// SINGLE-CUSTOMER FORM
// ─────────────────────────────────────────────────────────────────────────────

function setupForm() {
    const form = document.getElementById('segmentForm');
    const inputs = form.querySelectorAll('input');

    // Real-time validation on blur
    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            const error = validateField(input.id, input.value);
            showFieldError(input.id, error);
        });

        // Clear error on input
        input.addEventListener('input', () => {
            const error = validateField(input.id, input.value);
            showFieldError(input.id, error);
        });
    });

    form.addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    if (isLoading) return;

    const formData = {
        Income:       parseFloat(document.getElementById('income').value),
        SpendingScore:parseFloat(document.getElementById('spendingScore').value),
        Frequency:    parseFloat(document.getElementById('frequency').value),
        Recency:      parseFloat(document.getElementById('recency').value),
        Monetary:     parseFloat(document.getElementById('monetary').value),
    };

    // Validate all fields
    const errors = {};
    Object.keys(formData).forEach(key => {
        const fieldId = key.charAt(0).toLowerCase() + key.slice(1);
        const error = validateField(fieldId, formData[key]);
        if (error) errors[fieldId] = error;
    });

    if (Object.keys(errors).length > 0) {
        updateErrorSummary(errors);
        Object.entries(errors).forEach(([field, error]) => {
            showFieldError(field, error);
        });
        return;
    }

    clearFormErrors();
    setLoading(true);

    try {
        const response = await fetch(`${API_URL}/segment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Invalid input – please check your values');
        }

        displayResults(await response.json());
    } catch (err) {
        updateErrorSummary({ 'api': err.message || 'Failed to analyse customer. Ensure the backend is running.' });
    } finally {
        setLoading(false);
    }
}

function displayResults(result) {
    // Update result values
    document.getElementById('segmentValue').textContent = result.segment;
    document.getElementById('patternValue').textContent  = result.pattern;
    document.getElementById('clusterValue').textContent  = `Cluster ${result.cluster}`;
    document.getElementById('insightValue').textContent  = result.insight;

    // Update segment badge styling
    const badge = document.getElementById('segmentBadge');
    badge.className = 'segment-badge';
    const sl = result.segment.toLowerCase();
    if (sl.includes('vip') || sl.includes('active affluent'))  badge.classList.add('premium');
    else if (sl.includes('churn') || sl.includes('declining')) badge.classList.add('at-risk');
    else if (sl.includes('regular') || sl.includes('standard'))badge.classList.add('standard');
    else badge.classList.add('new');

    // Show live results, hide skeleton
    document.getElementById('skeletonState').style.display = 'none';
    document.getElementById('liveResults').style.display = 'block';
}

// ─────────────────────────────────────────────────────────────────────────────
// BATCH UPLOAD
// ─────────────────────────────────────────────────────────────────────────────

function setupBatch() {
    const fileInput   = document.getElementById('csvFileInput');
    const dropZone    = document.getElementById('dropZone');
    const submitBtn   = document.getElementById('batchSubmitBtn');
    const batchExport = document.getElementById('batchExportBtn');

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) selectFile(fileInput.files[0]);
    });

    // Click on drop-zone triggers file picker
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'LABEL') fileInput.click();
    });

    // Drag & drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) selectFile(file);
    });

    // Run batch
    submitBtn.addEventListener('click', runBatch);

    // Download batch results
    batchExport.addEventListener('click', downloadBatchResultsCSV);
}

function selectFile(file) {
    selectedFile = file;
    document.getElementById('dropFileName').textContent = file.name;
    document.getElementById('batchSubmitBtn').disabled = false;
}

async function runBatch() {
    if (!selectedFile) return;

    const btn      = document.getElementById('batchSubmitBtn');
    const btnText  = btn.querySelector('.btn-text');
    const btnIcon  = btn.querySelector('.btn-icon');
    const spinner  = btn.querySelector('.loading-spinner');

    btn.disabled = true;
    btnText.textContent = 'Processing…';
    btnIcon.style.display = 'none';
    spinner.style.display = 'inline';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch(`${API_URL}/batch`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error ${response.status}`);
        }

        batchResults = await response.json();
        renderBatchResults(batchResults);
    } catch (err) {
        alert(err.message || 'Batch segmentation failed.');
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Run Segmentation';
        btnIcon.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

function renderBatchResults(data) {
    // Summary
    const summary = document.getElementById('batchSummary');
    summary.innerHTML = `
        <span class="summary-pill total">Total: ${data.total}</span>
        <span class="summary-pill success">✓ ${data.successful} succeeded</span>
        ${data.failed ? `<span class="summary-pill fail">✗ ${data.failed} failed</span>` : ''}
    `;

    // Table
    const tbody = document.getElementById('batchTableBody');
    tbody.innerHTML = '';
    data.results.forEach((row, i) => {
        const tr = document.createElement('tr');
        if (row.error) tr.classList.add('row-error');
        tr.innerHTML = `
            <td>${i + 1}</td>
            <td>${row.CustomerID ?? '—'}</td>
            <td>${row.segment  ?? '—'}</td>
            <td>${row.cluster  != null ? `Cluster ${row.cluster}` : '—'}</td>
            <td>${row.pattern  ?? '—'}</td>
            <td>${row.error    ? `<span class="error-badge">${row.error}</span>` : '<span class="ok-badge">OK</span>'}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('batchResultsArea').style.display = 'block';
}

function downloadBatchResultsCSV() {
    if (!batchResults) return;
    const headers = ['row_index','CustomerID','Income','SpendingScore','Frequency','Recency','Monetary','cluster','segment','pattern','insight','error'];
    const rows = batchResults.results.map(r => headers.map(h => r[h] ?? '').join(','));
    const csv  = [headers.join(','), ...rows].join('\n');
    triggerDownload(csv, 'batch_results.csv');
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPORT ALL SEGMENTS
// ─────────────────────────────────────────────────────────────────────────────

function setupExport() {
    document.getElementById('exportBtn')?.addEventListener('click', exportAllSegments);
}

async function exportAllSegments() {
    const btn = document.getElementById('exportBtn');
    btn.textContent = 'Downloading…';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/export`);
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        const csv = await response.text();
        triggerDownload(csv, 'customer_segments.csv');
    } catch (err) {
        alert(err.message || 'Export failed. Ensure the backend is running.');
    } finally {
        btn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Export All Segments (CSV)`;
        btn.disabled = false;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

function triggerDownload(csvContent, filename) {
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function setLoading(loading) {
    isLoading = loading;
    const btn     = document.getElementById('submitBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnIcon = btn.querySelector('.btn-icon');
    const spinner = btn.querySelector('.loading-spinner');

    if (loading) {
        btn.disabled = true;
        btnText.textContent = 'Analyzing…';
        btnIcon.style.display = 'none';
        spinner.style.display = 'inline';
    } else {
        btn.disabled = false;
        btnText.textContent = 'Analyze';
        btnIcon.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SCATTER CHART
// ─────────────────────────────────────────────────────────────────────────────

async function loadCustomerData() {
    try {
        const response = await fetch(`${API_URL}/data`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.length) { 
            createScatterChart(data);
            createChartLegend();
        }
    } catch (err) {
        console.error('Error loading data:', err);
    }
}

function createScatterChart(data) {
    const groups = {};
    data.forEach(c => { (groups[c.Cluster] ??= []).push(c); });

    const datasets = Object.keys(groups).map(id => {
        const n = parseInt(id);
        const col = clusterColors[n % clusterColors.length];
        return {
            label: col.label,
            data: groups[id].map(c => ({ x: c.Income, y: c.SpendingScore, customer: c })),
            backgroundColor: col.bg,
            borderColor: col.border,
            borderWidth: 2,
            pointRadius: 7,
            pointHoverRadius: 10,
            pointHoverBorderWidth: 3,
        };
    });

    const ctx = document.getElementById('scatterChart').getContext('2d');
    if (scatterChart) scatterChart.destroy();

    scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeOutQuart' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    cornerRadius: 0,
                    padding: 12,
                    callbacks: {
                        title: ctx => `Customer ${ctx[0].raw.customer.CustomerID}`,
                        label: ctx => [
                            `Income: ${ctx.raw.x.toFixed(1)}`,
                            `Spending Score: ${ctx.raw.y.toFixed(1)}`,
                            `Cluster: ${ctx.raw.customer.Cluster}`,
                        ],
                    },
                },
            },
            scales: {
                x: {
                    title: { display: true, text: 'Income', font: { size: 14, weight: '600' }, color: '#9ca3af' },
                    grid:  { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#6b7280', font: { size: 12 } },
                },
                y: {
                    title: { display: true, text: 'Spending Score', font: { size: 14, weight: '600' }, color: '#9ca3af' },
                    grid:  { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#6b7280', font: { size: 12 } },
                },
            },
        },
    });
}

function createChartLegend() {
    const el = document.getElementById('chartLegend');
    el.innerHTML = '';
    clusterColors.forEach(({ border, label }) => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `<span class="legend-color" style="background:${border}"></span><span>${label}</span>`;
        el.appendChild(item);
    });
}
