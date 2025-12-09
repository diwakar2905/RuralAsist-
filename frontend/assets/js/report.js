// Use global config if available, fallback to direct URL

// Shared HTML escape utility
function escapeHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
const API_BASE_URL = window.AppConfig?.API_BASE_URL;

document.addEventListener('DOMContentLoaded', () => {
    const reportForm = document.getElementById('reportForm');
    const scamDescription = document.getElementById('scamDescription');
    const analysisCard = document.getElementById('analysis-card');
    const analysisSpinner = document.getElementById('analysis-spinner');
    const analysisResult = document.getElementById('analysis-result');

    // Load common scams on page load
    loadCommonScams();

    // Handle form submission
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const description = scamDescription.value.trim();
        if (!description) {
            Swal.fire('Error', 'Please describe the suspicious activity', 'error');
            return;
        }

        // Show analysis card with spinner
        analysisCard.classList.remove('d-none');
        analysisSpinner.classList.remove('d-none');
        analysisResult.innerHTML = '';

        try {
            // Call analyze endpoint
            const analyzeRes = await fetch(`${API_BASE_URL}/scam/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description: description,
                    scam_type: document.getElementById('scamType').value || null,
                    location: document.getElementById('location').value || null,
                    anonymous: document.getElementById('anonymousCheck').checked
                })
            });

            const analysis = await analyzeRes.json();
            if (!analyzeRes.ok) throw new Error(analysis.detail || 'Analysis failed');

            // Display risk assessment
            displayRiskAssessment(analysis);

            // Submit report
            await submitReport(description);

        } catch (error) {
            console.error('Error:', error);
            analysisResult.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${escapeHTML(error.message).replace(/\n/g, "<br>")}
                </div>
            `;
        } finally {
            analysisSpinner.classList.add('d-none');
        }
    });

    function displayRiskAssessment(analysis) {
        const { risk_level, risk_score, keywords_detected, analysis_text } = analysis;
        
        // Determine color and emoji based on risk level
        let riskColor, riskEmoji;
        if (risk_level === 'High') {
            riskColor = 'danger';
            riskEmoji = '🚨';
        } else if (risk_level === 'Medium') {
            riskColor = 'warning';
            riskEmoji = '⚠️';
        } else {
            riskColor = 'success';
            riskEmoji = '✅';
        }

        let html = `
            <div class="alert alert-${riskColor} mb-3">
                <h5 class="mb-3">
                    ${riskEmoji} Risk Level: <strong>${risk_level}</strong>
                </h5>
                <div class="progress mb-3" style="height: 8px;">
                    <div class="progress-bar progress-bar-${riskColor}" 
                         role="progressbar" 
                         style="width: ${risk_score}%;" 
                         aria-valuenow="${risk_score}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
                <small>Risk Score: ${risk_score.toFixed(1)}/100</small>
            </div>

            <div class="alert alert-info mb-3">
                <h6 class="fw-bold mb-2">⚠️ Assessment:</h6>
                <p class="mb-0">${escapeHTML(analysis_text).replace(/\n/g, "<br>")}</p>
            </div>
        `;

        if (keywords_detected && keywords_detected.length > 0) {
            html += `
                <div class="mb-3">
                    <h6 class="fw-bold">🔍 Keywords Detected:</h6>
                    <div>
                        ${keywords_detected.map(kw => 
                            `<span class="badge bg-warning me-2 mb-2">${kw}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        analysisResult.innerHTML = html;
    }

    async function submitReport(description) {
        try {
            const submitRes = await fetch(`${API_BASE_URL}/scam/report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description: description,
                    scam_type: document.getElementById('scamType').value || null,
                    location: document.getElementById('location').value || null,
                    anonymous: document.getElementById('anonymousCheck').checked
                })
            });

            const result = await submitRes.json();
            if (!submitRes.ok) throw new Error(result.detail || 'Submission failed');

            Swal.fire({
                icon: 'success',
                title: 'Report Submitted!',
                html: `
                    <p>Thank you for helping protect the community.</p>
                    <p><strong>Report ID:</strong> ${result.report_id}</p>
                    <p><strong>Risk Level:</strong> ${result.risk_level}</p>
                `,
                confirmButtonText: 'OK'
            });

            // Reset form
            reportForm.reset();
        } catch (error) {
            console.error('Submit error:', error);
        }
    }

    async function loadCommonScams() {
        try {
            const res = await fetch(`${API_BASE_URL}/scam/common-scams`);
            const data = await res.json();

            const commonScamsDiv = document.getElementById('common-scams-section');
            if (!commonScamsDiv) return;

            let html = '<h4 class="mt-5 mb-3">🚨 Common Scam Types</h4><div class="row">';

            data.common_scams.forEach((scam, idx) => {
                html += `
                    <div class="col-md-6 mb-3">
                        <div class="card h-100 border-left-danger" style="border-left: 4px solid #dc3545;">
                            <div class="card-body">
                                <h6 class="card-title fw-bold">${escapeHTML(scam.type)}</h6>
                                <p class="card-text small mb-2">${escapeHTML(scam.description).replace(/\n/g, "<br>")}</p>
                                <div class="alert alert-sm alert-warning py-2 px-3 mb-2">
                                    <small><strong>${escapeHTML(scam.warning)}</strong></small>
                                </div>
                                <small class="text-muted">
                                    <strong>Examples:</strong><br>
                                    ${scam.examples.map(ex => `• ${escapeHTML(ex)}`).join('<br>')}
                                </small>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            commonScamsDiv.innerHTML = html;
        } catch (error) {
            console.error('Error loading common scams:', error);
        }
    }
});
