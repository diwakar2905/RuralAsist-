// Use global config if available, fallback to direct values
const API_BASE_URL = window.AppConfig?.API_BASE_URL;
const MAX_FILE_SIZE = window.AppConfig?.MAX_FILE_SIZE || 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = window.AppConfig?.ALLOWED_FILE_TYPES || ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];

const fileInput = document.getElementById("ocr-file");
const uploadBtn = document.getElementById("ocr-btn");
const resultBox = document.getElementById("ocr-output");
const loader = document.getElementById("ocr-loader");
const copyBtn = document.getElementById("copy-btn");

if (uploadBtn) uploadBtn.addEventListener("click", startOCR);
if (copyBtn) copyBtn.addEventListener("click", copyToClipboard);
if (fileInput) fileInput.addEventListener("change", handleFileSelect);

// File selection handler with preview
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
        showNotification(validation.error, 'error');
        fileInput.value = '';
        return;
    }

    showNotification(`File selected: ${file.name} (${formatFileSize(file.size)})`, 'success');
}

// File validation
function validateFile(file) {
    if (!file) {
        return { valid: false, error: 'No file selected' };
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
        return { 
            valid: false, 
            error: 'Invalid file type. Please upload JPG, PNG, or PDF files only.' 
        };
    }

    if (file.size > MAX_FILE_SIZE) {
        return { 
            valid: false, 
            error: `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.` 
        };
    }

    return { valid: true };
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Show notification
function showNotification(message, type = 'info') {
    if (typeof Swal !== 'undefined') {
        const icons = { success: 'success', error: 'error', info: 'info', warning: 'warning' };
        Swal.fire({
            icon: icons[type] || 'info',
            text: message,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        alert(message);
    }
}

function resetUI() {
    if (loader) loader.style.display = "none";
    if (resultBox) resultBox.value = "";
}

async function startOCR() {
    const file = fileInput?.files?.[0];

    if (!file) {
        showNotification('Please select a file first!', 'warning');
        return;
    }

    // Validate file again before upload
    const validation = validateFile(file);
    if (!validation.valid) {
        showNotification(validation.error, 'error');
        return;
    }

    resetUI();
    if (loader) {
        loader.style.display = "block";
        loader.innerHTML = `
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
            <span>Processing ${file.name}... This may take a moment.</span>
        `;
    }
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_BASE_URL}/ocr/extract`, {
            method: "POST",
            body: formData,
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || `HTTP error ${res.status}`);
        }

        const data = await res.json();
        
        if (loader) loader.style.display = "none";
        if (resultBox) {
            resultBox.value = data.text || "No text found in the document.";
        }

        // Log OCR activity
        logOCRActivity(file.name);

        showNotification('✅ Text extracted successfully!', 'success');

    } catch (err) {
        if (loader) loader.style.display = "none";
        if (resultBox) resultBox.value = "";
        
        console.error('OCR Error:', err);
        showNotification(
            `❌ OCR failed: ${err.message}. Please check if the backend server is running.`, 
            'error'
        );
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="bi bi-search me-2"></i><span data-lang-en="Extract Text" data-lang-hi="टेक्स्ट निकालें">Extract Text</span>';
        }
    }
}

function copyToClipboard() {
    if (!resultBox || !resultBox.value) {
        showNotification('No text to copy!', 'warning');
        return;
    }
    
    resultBox.select();
    navigator.clipboard.writeText(resultBox.value)
        .then(() => {
            showNotification('✅ Copied to clipboard!', 'success');
        })
        .catch(() => {
            // Fallback for older browsers
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        });
}

// Log OCR activity to profile
async function logOCRActivity(filename) {
    const token = localStorage.getItem('ruralassist_token');
    if (!token) return;

    try {
        await fetch(`${API_BASE_URL}/profile/activity`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                type: 'ocr',
                description: `Scanned document: ${filename}`
            })
        });
    } catch (e) {
        // Silent fail for analytics
    }
}
