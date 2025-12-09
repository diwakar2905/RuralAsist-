// Use global config if available, fallback to production URL
const API_BASE_URL = window.AppConfig?.API_BASE_URL;
const STORAGE_KEYS = window.AppConfig?.STORAGE_KEYS || {
    TOKEN: 'ruralassist_token',
    USER_EMAIL: 'user_email',
    USER_NAME: 'ruralassist_name',
    LOGIN_REDIRECT: 'login_redirect_target',
    LOGGED_IN: 'ruralassist_logged_in'
};

const emailInput = document.getElementById("email");
const otpInput = document.getElementById("otp");
const sendOtpBtn = document.getElementById("send-otp-btn");
const verifyOtpBtn = document.getElementById("verify-otp-btn");
const resendOtpBtn = document.getElementById("resend-otp-btn");
const statusText = document.getElementById("login-status");

let otpSentTime = 0;
let resendTimer = null;

sendOtpBtn?.addEventListener("click", sendOTP);
verifyOtpBtn?.addEventListener("click", verifyOTP);
resendOtpBtn?.addEventListener("click", resendOTP);

// Enable Enter key for email input
emailInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendOTP();
});

// Enable Enter key for OTP input
otpInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") verifyOTP();
});

async function sendOTP() {
    const email = emailInput.value.trim();
    if (!email) {
        updateStatus("⚠️ Please enter your email first.", "warning");
        return;
    }

    // Validate email format
    const emailRegex = /^[\w\.-]+@[\w\.-]+\.[\w-]+$/;
    if (!emailRegex.test(email)) {
        updateStatus("❌ Please enter a valid email address.", "error");
        return;
    }

    sendOtpBtn.disabled = true;
    updateStatus("📧 Sending OTP to your email...", "info");

    try {
        const res = await fetch(`${API_BASE_URL}/auth/send-email-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        const data = await res.json();

        if (data.success) {
            updateStatus(data.message, "success");
            otpSentTime = Date.now();
            
            // Show OTP input field
            if (otpInput) {
                otpInput.disabled = false;
                otpInput.focus();
            }
            if (verifyOtpBtn) verifyOtpBtn.disabled = false;
            
            // Enable resend button after 30 seconds
            startResendTimer();
            
            // Show helpful message
            setTimeout(() => {
                updateStatus("✅ OTP sent! Check your email inbox (and spam folder).", "success");
            }, 2000);
        } else {
            updateStatus(data.message || "❌ Failed to send OTP.", "error");
            sendOtpBtn.disabled = false;
        }

    } catch (err) {
        console.error("Send OTP error:", err);
        updateStatus("❌ Error sending OTP. Check if backend is running on port 8000.", "error");
        sendOtpBtn.disabled = false;
    }
}

async function verifyOTP() {
    const email = emailInput.value.trim();
    const otp = otpInput.value.trim();

    if (!email || !otp) {
        updateStatus("⚠️ Please enter both email and OTP.", "warning");
        return;
    }

    if (otp.length !== 6 || !/^\d{6}$/.test(otp)) {
        updateStatus("❌ OTP must be 6 digits.", "error");
        return;
    }

    verifyOtpBtn.disabled = true;
    updateStatus("🔐 Verifying OTP...", "info");

    try {
        const res = await fetch(`${API_BASE_URL}/auth/verify-email-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, otp })
        });

        const data = await res.json();

        if (data.success && data.token) {
            updateStatus("✅ Login successful! Redirecting...", "success");
            
            // Store auth data
            try {
                localStorage.setItem(STORAGE_KEYS.TOKEN, data.token);
                localStorage.setItem(STORAGE_KEYS.LOGGED_IN, "true");
                localStorage.setItem(STORAGE_KEYS.USER_EMAIL, email);
                
                // Ask for name if not set
                if (!localStorage.getItem(STORAGE_KEYS.USER_NAME)) {
                    const name = prompt("Welcome! What's your name? (optional):");
                    if (name && name.trim()) {
                        localStorage.setItem(STORAGE_KEYS.USER_NAME, name.trim());
                    }
                }
            } catch (storageErr) {
                console.error("Storage error:", storageErr);
            }

            // Log activity
            logLoginActivity(email);

            // Redirect to intended page or home
            const target = localStorage.getItem(STORAGE_KEYS.LOGIN_REDIRECT);
            if (target) {
                try { localStorage.removeItem(STORAGE_KEYS.LOGIN_REDIRECT); } catch {}
                setTimeout(() => { window.location.href = target; }, 600);
            } else {
                setTimeout(() => { window.location.href = "index.html"; }, 600);
            }
        } else {
            updateStatus(data.message || "❌ OTP verification failed.", "error");
            verifyOtpBtn.disabled = false;
            
            // Clear OTP input for retry
            if (otpInput) otpInput.value = "";
            if (otpInput) otpInput.focus();
        }

    } catch (err) {
        console.error("Verify OTP error:", err);
        updateStatus("❌ Error verifying OTP. Please try again.", "error");
        verifyOtpBtn.disabled = false;
    }
}

async function resendOTP() {
    const email = emailInput.value.trim();
    if (!email) {
        updateStatus("⚠️ Please enter your email first.", "warning");
        return;
    }

    // Check if enough time has passed (30 seconds)
    const timeSinceLastOtp = Date.now() - otpSentTime;
    if (timeSinceLastOtp < 30000) {
        const remainingSeconds = Math.ceil((30000 - timeSinceLastOtp) / 1000);
        updateStatus(`⏰ Please wait ${remainingSeconds} seconds before resending.`, "warning");
        return;
    }

    resendOtpBtn.disabled = true;
    updateStatus("📧 Resending OTP...", "info");

    try {
        const res = await fetch(`${API_BASE_URL}/auth/resend-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        const data = await res.json();

        if (data.success) {
            updateStatus("✅ New OTP sent to your email!", "success");
            otpSentTime = Date.now();
            
            // Clear old OTP
            if (otpInput) {
                otpInput.value = "";
                otpInput.focus();
            }
            
            startResendTimer();
        } else {
            updateStatus(data.message || "❌ Failed to resend OTP.", "error");
            resendOtpBtn.disabled = false;
        }

    } catch (err) {
        console.error("Resend OTP error:", err);
        updateStatus("❌ Error resending OTP.", "error");
        resendOtpBtn.disabled = false;
    }
}

function startResendTimer() {
    if (resendOtpBtn) resendOtpBtn.disabled = true;
    
    let countdown = 30;
    if (resendOtpBtn) {
        resendOtpBtn.textContent = `Resend OTP (${countdown}s)`;
    }
    
    resendTimer = setInterval(() => {
        countdown--;
        if (resendOtpBtn) {
            resendOtpBtn.textContent = `Resend OTP (${countdown}s)`;
        }
        
        if (countdown <= 0) {
            clearInterval(resendTimer);
            if (resendOtpBtn) {
                resendOtpBtn.disabled = false;
                resendOtpBtn.textContent = "Resend OTP";
            }
        }
    }, 1000);
}

function updateStatus(message, type = "info") {
    if (!statusText) return;
    
    statusText.textContent = message;
    statusText.className = `status-text status-${type}`;
    
    // Auto-clear non-error messages after 5 seconds
    if (type !== "error") {
        setTimeout(() => {
            if (statusText.textContent === message) {
                statusText.textContent = "";
            }
        }, 5000);
    }
}

// Log login activity to profile
async function logLoginActivity(email) {
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    if (!token) return;

    try {
        await fetch(`${API_BASE_URL}/profile/activity`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                type: "login",
                description: `Logged in via OTP`
            })
        });
    } catch (e) {
        // Silent fail for analytics
    }
}