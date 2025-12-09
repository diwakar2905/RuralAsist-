const API_BASE_URL = window.AppConfig?.API_BASE_URL || "https://rural-asist.onrender.com";
const LANG_KEY = 'ruralasist_language';
const INIT_RETRY_DELAY = 100; // ms
const MAX_INIT_RETRIES = 20;

let floatBtn, chatPopup, closeBtn, box, input, sendBtn;
let isOnline = true;
let lastSentAt = 0;
let offlineMessageShown = false;
let initialized = false;
let initRetries = 0;

// Get current language
function getCurrentLang() {
    return localStorage.getItem(LANG_KEY) || 'en';
}

// Global handler for inline events - defined early so it's available for inline handlers
window.chatSendMessage = function() {
    sendMessage();
};

window.chatKeyPress = function(e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
};

function initChatElements() {
    floatBtn = document.getElementById("chat-float-btn");
    chatPopup = document.getElementById("chat-popup");
    closeBtn = document.getElementById("chat-close-btn");
    box = document.getElementById("chat-popup-box");
    input = document.getElementById("chat-popup-input");
    sendBtn = document.getElementById("chat-popup-send");
    
    return (floatBtn && chatPopup && closeBtn && box && input && sendBtn);
}

function safeInit() {
    if (initialized) return true;
    
    const hasElements = initChatElements();
    
    if (!hasElements) {
        // Retry initialization
        if (initRetries < MAX_INIT_RETRIES) {
            initRetries++;
            setTimeout(safeInit, INIT_RETRY_DELAY);
            return false;
        }
        console.warn("Chatbot: Could not initialize after", MAX_INIT_RETRIES, "retries");
        return false;
    }

    console.log("✅ Chatbot: Initializing (attempt", initRetries + 1, ")");
    initialized = true;

    // Open Popup - using addEventListener for better compatibility
    floatBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("Chatbot: Float button clicked");
        chatPopup.classList.add("active");
        chatPopup.style.display = "flex";
        if (!box.dataset.greeted) greet();
    });
    
    // Close Popup
    closeBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log("Chatbot: Close button clicked");
        chatPopup.classList.remove("active");
        chatPopup.style.display = "none";
    });

    // Send on Enter
    input.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send button
    sendBtn.addEventListener("click", function(e) {
        e.preventDefault();
        sendMessage();
    });

    // Online status polling (lightweight)
    checkOnlineStatus();
    setInterval(checkOnlineStatus, 30000);
    
    console.log("✅ Chatbot: Initialization complete! Chatbot is ready to use.");
    return true;
}

function greet() {
    const lang = getCurrentLang();
    let greeting;
    
    if (lang === 'hi') {
        greeting = "नमस्ते! 👋 मैं आपका RuralAsist सहायक हूँ।\n\nमैं आपकी इनमें मदद कर सकता हूँ:\n🏛️ सरकारी योजनाएं\n📄 दस्तावेज़ स्कैनिंग (OCR)\n🛡️ धोखाधड़ी से बचाव\n\nहिंदी या अंग्रेजी में पूछें!";
    } else {
        greeting = "Hello! 👋 I'm your RuralAsist assistant.\n\nI can help you with:\n🏛️ Government Schemes\n📄 Document Scanning (OCR)\n🛡️ Scam Prevention\n\nAsk me in English or Hindi!";
    }
    
    addMsg(greeting, "bot");
    addQuickReplies();
    box.dataset.greeted = "1";
}

function addQuickReplies() {
    const lang = getCurrentLang();
    const quickRepliesDiv = document.createElement("div");
    quickRepliesDiv.className = "quick-replies";
    
    const replies = lang === 'hi' 
        ? [
            { text: "🏛️ योजनाएं", query: "सरकारी योजनाएं" },
            { text: "📄 OCR कैसे करें", query: "OCR कैसे करें" },
            { text: "🛡️ स्कैम से बचाव", query: "धोखाधड़ी से बचाव" },
            { text: "❓ मदद", query: "मदद" }
        ]
        : [
            { text: "🏛️ Schemes", query: "government schemes" },
            { text: "📄 How to use OCR", query: "how to scan documents" },
            { text: "🛡️ Scam Protection", query: "scam protection tips" },
            { text: "❓ Help", query: "help" }
        ];
    
    replies.forEach(reply => {
        const btn = document.createElement("button");
        btn.className = "quick-reply-btn";
        btn.textContent = reply.text;
        btn.onclick = () => {
            // Remove quick replies after selection
            quickRepliesDiv.remove();
            // Set input and send
            const inputEl = document.getElementById("chat-popup-input");
            if (inputEl) {
                inputEl.value = reply.query;
                sendMessage();
            }
        };
        quickRepliesDiv.appendChild(btn);
    });
    
    box.appendChild(quickRepliesDiv);
    box.scrollTop = box.scrollHeight;
}

function addMsg(text, sender) {
    const div = document.createElement("div");
    div.className = sender === "user" ? "msg user-msg" : "msg bot-msg";
    div.innerHTML = text.replace(/\n/g, '<br>');
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function setSendingEnabled(enabled) {
    input.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

async function checkOnlineStatus() {
    try {
        const res = await fetch(`${API_BASE_URL}/`, { method: 'GET' });
        isOnline = res.ok;
        offlineMessageShown = false;
    } catch {
        isOnline = false;
    }
    setSendingEnabled(isOnline);
}

async function logActivity(type, description) {
    const token = localStorage.getItem("ruralassist_token");
    if (!token) return;
    
    try {
        await fetch(`${API_BASE_URL}/profile/activity`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ type, description })
        });
    } catch (e) {
        // Silent fail for analytics
    }
}

async function sendMessage() {
    // Get elements fresh each time in case they weren't available initially
    const inputEl = input || document.getElementById("chat-popup-input");
    const boxEl = box || document.getElementById("chat-popup-box");
    
    if (!inputEl || !boxEl) {
        console.error("Chatbot: Input or box element not found");
        return;
    }
    
    const text = inputEl.value.trim();
    if (!text) return;

    // Simple rate-limit: 1s between sends
    const now = Date.now();
    if (now - lastSentAt < 1000) return;
    lastSentAt = now;

    // Add user message
    const userDiv = document.createElement("div");
    userDiv.className = "msg user-msg";
    userDiv.innerHTML = text.replace(/\n/g, '<br>');
    boxEl.appendChild(userDiv);
    boxEl.scrollTop = boxEl.scrollHeight;
    
    inputEl.value = "";

    // Add loading indicator
    const loading = document.createElement("div");
    loading.className = "msg bot-msg";
    loading.innerHTML = '<span class="typing-indicator">Typing<span>.</span><span>.</span><span>.</span></span>';
    boxEl.appendChild(loading);
    boxEl.scrollTop = boxEl.scrollHeight;

    const headers = { "Content-Type": "application/json" };
    const token = localStorage.getItem("ruralassist_token");
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
        console.log("Chatbot: Sending message to", `${API_BASE_URL}/chatbot/message`);
        const res = await fetch(`${API_BASE_URL}/chatbot/message`, {
            method: "POST",
            headers,
            body: JSON.stringify({ query: text })
        });

        console.log("Chatbot: Response status", res.status);
        
        if (!res.ok) {
            const errText = await res.text();
            console.error("Chatbot: Error response", errText);
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();
        console.log("Chatbot: Response data", data);

        loading.remove();
        
        // Add bot response
        const botDiv = document.createElement("div");
        botDiv.className = "msg bot-msg";
        botDiv.innerHTML = (data.reply || "Sorry, I couldn't process that. Please try again.").replace(/\n/g, '<br>');
        boxEl.appendChild(botDiv);
        boxEl.scrollTop = boxEl.scrollHeight;
        
        // Log chat activity
        logActivity("chatbot", `Asked: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
        
    } catch (e) {
        loading.remove();
        console.error("Chatbot error:", e);
        
        const errorDiv = document.createElement("div");
        errorDiv.className = "msg bot-msg";
        errorDiv.innerHTML = "❌ Error connecting to chatbot. Please check the backend server status and logs for more information.";
        boxEl.appendChild(errorDiv);
        boxEl.scrollTop = boxEl.scrollHeight;
    }
}

// Add CSS for typing indicator and quick replies
const style = document.createElement('style');
style.textContent = `
    .typing-indicator span {
        animation: blink 1.4s infinite;
        animation-fill-mode: both;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes blink {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    
    /* Ensure chat popup displays correctly */
    .chat-popup.active {
        display: flex !important;
    }
    
    /* Quick Reply Buttons */
    .quick-replies {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 8px 0;
        margin-top: 8px;
    }
    
    .quick-reply-btn {
        background: linear-gradient(135deg, #4F46E5, #34A853);
        color: white;
        border: none;
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
    }
    
    .quick-reply-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
    }
    
    .quick-reply-btn:active {
        transform: translateY(0);
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready - multiple fallbacks
function tryInit() {
    if (!initialized) {
        safeInit();
    }
}

// Try immediately if DOM is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(tryInit, 0);
} 

// Also listen for DOMContentLoaded
document.addEventListener('DOMContentLoaded', tryInit);

// And window load as final fallback
window.addEventListener('load', tryInit);
