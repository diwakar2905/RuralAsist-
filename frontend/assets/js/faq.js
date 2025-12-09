// -----------------------------
// ADVANCED FAQ PAGE SCRIPT - Modern Version
// -----------------------------

// Use global config if available, fallback to direct values

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
const API_BASE_URL = window.AppConfig?.API_BASE_URL || "https://rural-asist.onrender.com";
const FAQ_LANG_KEY = window.AppConfig?.STORAGE_KEYS?.LANGUAGE || 'ruralassist_language';

// Global variables
let searchInput = null;
let faqContainer = null;
let loadingElement = null;
let noResultsElement = null;
let searchSuggestions = null;
let currentCategory = 'all';
let allFaqs = [];
let searchTimeout = null;

// Enhanced FAQ data with voting and better categorization
const ENHANCED_FAQS = [
    {
        id: "faq_login_otp",
        category: "general",
        question_en: "How do I log in with OTP?",
        question_hi: "मैं OTP से कैसे लॉगिन करूं?",
        answer_en: "Enter your email on the Login page, click 'Send OTP', then enter the OTP that appears in the backend console during development. In production, the OTP will be sent to your email. This ensures secure email-based authentication.",
        answer_hi: "लॉगिन पेज पर अपना ईमेल दर्ज करें, 'OTP भेजें' पर क्लिक करें, फिर डेवलपमेंट के दौरान बैकएंड कंसोल में दिखाए गए OTP को दर्ज करें। प्रोडक्शन में, OTP आपके ईमेल पर भेजा जाएगा।",
        icon: "bi-box-arrow-in-right",
        keywords: ["login", "otp", "email", "authentication", "sign in"],
        helpful_count: 127,
        unhelpful_count: 8
    },
    {
        id: "faq_schemes_find",
        category: "schemes",
        question_en: "Where can I find government schemes?",
        question_hi: "सरकारी योजनाएं कहां मिलेंगी?",
        answer_en: "Visit the 'Schemes' page to browse 150+ government schemes. Filter by category (Agriculture, Education, Health, Housing, Employment) or search by keywords. Each scheme shows detailed eligibility criteria, benefits, and application links.",
        answer_hi: "150+ सरकारी योजनाएं देखने के लिए 'योजनाएं' पेज पर जाएं। श्रेणी (कृषि, शिक्षा, स्वास्थ्य, आवास, रोजगार) से फ़िल्टर करें या कीवर्ड से खोजें। प्रत्येक योजना में विस्तृत पात्रता मानदंड, लाभ और आवेदन लिंक दिखाए गए हैं।",
        icon: "bi-building",
        keywords: ["schemes", "government", "benefits", "agriculture", "education"],
        helpful_count: 234,
        unhelpful_count: 12
    },
    {
        id: "faq_ocr_scan",
        category: "ocr",
        question_en: "How do I scan a document (OCR)?",
        question_hi: "दस्तावेज़ कैसे स्कैन करें (OCR)?",
        answer_en: "Go to OCR page, upload an image (JPG, PNG) or PDF document up to 10MB, click 'Extract Text' to get instant text recognition. Supports both English and Hindi text. Works best with clear, well-lit images.",
        answer_hi: "OCR पेज पर जाएं, 10MB तक का इमेज (JPG, PNG) या PDF दस्तावेज़ अपलोड करें, तुरंत टेक्स्ट पहचान के लिए 'टेक्स्ट निकालें' पर क्लिक करें। अंग्रेजी और हिंदी दोनों टेक्स्ट का समर्थन करता है।",
        icon: "bi-file-earmark-text",
        keywords: ["ocr", "scan", "document", "text extraction", "pdf", "image"],
        helpful_count: 189,
        unhelpful_count: 15
    },
    {
        id: "faq_scam_report",
        category: "scam",
        question_en: "How do I report a scam?",
        question_hi: "धोखाधड़ी की रिपोर्ट कैसे करें?",
        answer_en: "Use the 'Report Scam' page to submit suspicious SMS, calls, or fraud attempts. Our AI analyzes the content and flags common scam patterns. Your reports help protect the entire rural community from fraud.",
        answer_hi: "संदिग्ध SMS, कॉल या धोखाधड़ी के प्रयासों की रिपोर्ट करने के लिए 'धोखाधड़ी रिपोर्ट' पेज का उपयोग करें। हमारी AI सामग्री का विश्लेषण करती है और सामान्य स्कैम पैटर्न को फ्लैग करती है।",
        icon: "bi-shield-exclamation",
        keywords: ["scam", "fraud", "report", "protection", "safety", "sms"],
        helpful_count: 156,
        unhelpful_count: 7
    },
    {
        id: "faq_profile_update",
        category: "general",
        question_en: "How do I update my profile?",
        question_hi: "अपनी प्रोफ़ाइल कैसे अपडेट करें?",
        answer_en: "After logging in, go to Profile page, click 'Edit Profile', update your name and preferences, then save. Your dashboard shows activity history, usage statistics, and personalized recommendations.",
        answer_hi: "लॉगिन के बाद प्रोफ़ाइल पेज पर जाएं, 'प्रोफ़ाइल संपादित करें' पर क्लिक करें, अपना नाम और वरीयताएं अपडेट करें, फिर सेव करें। आपका डैशबोर्ड गतिविधि इतिहास दिखाता है।",
        icon: "bi-person",
        keywords: ["profile", "update", "edit", "settings", "dashboard"],
        helpful_count: 98,
        unhelpful_count: 5
    },
    {
        id: "faq_hindi_support",
        category: "general",
        question_en: "Can I use RuralAsist in Hindi?",
        question_hi: "क्या मैं RuralAsist हिंदी में उपयोग कर सकता हूं?",
        answer_en: "Yes! Full Hindi support is available. The AI chatbot understands Hindi queries, OCR can extract Hindi text, and the entire interface can be switched to Hindi using the EN/हि toggle in the top navigation.",
        answer_hi: "हां! पूर्ण हिंदी समर्थन उपलब्ध है। AI चैटबॉट हिंदी प्रश्नों को समझता है, OCR हिंदी टेक्स्ट निकाल सकता है, और पूरा इंटरफेस हिंदी में स्विच किया जा सकता है।",
        icon: "bi-translate",
        keywords: ["hindi", "language", "translation", "support", "interface"],
        helpful_count: 203,
        unhelpful_count: 3
    },
    {
        id: "faq_schemes_eligibility",
        category: "schemes",
        question_en: "How do I check if I'm eligible for a scheme?",
        question_hi: "मैं कैसे जांचूं कि मैं किसी योजना के लिए योग्य हूं?",
        answer_en: "Each scheme page shows detailed eligibility criteria including age limits, income requirements, category (SC/ST/OBC), and documentation needed. Use filters to find schemes matching your profile.",
        answer_hi: "प्रत्येक योजना पेज में आयु सीमा, आय आवश्यकताएं, श्रेणी (SC/ST/OBC), और आवश्यक दस्तावेज सहित विस्तृत पात्रता मानदंड दिखाए गए हैं।",
        icon: "bi-check-circle",
        keywords: ["eligibility", "qualification", "criteria", "age", "income", "category"],
        helpful_count: 176,
        unhelpful_count: 11
    },
    {
        id: "faq_ocr_accuracy",
        category: "ocr",
        question_en: "How accurate is the OCR text extraction?",
        question_hi: "OCR टेक्स्ट निष्कर्षण कितना सटीक है?",
        answer_en: "OCR accuracy ranges from 90-98% for clear, printed text. Handwritten text has lower accuracy (60-80%). For best results: use good lighting, avoid shadows, keep text horizontal, and ensure high image quality.",
        answer_hi: "स्पष्ट, मुद्रित टेक्स्ट के लिए OCR की सटीकता 90-98% है। हस्तलिखित टेक्स्ट की सटीकता कम है (60-80%)। बेहतर परिणामों के लिए: अच्छी रोशनी का उपयोग करें।",
        icon: "bi-accuracy",
        keywords: ["accuracy", "precision", "quality", "handwriting", "printed text"],
        helpful_count: 145,
        unhelpful_count: 18
    },
    {
        id: "faq_scam_protection",
        category: "scam",
        question_en: "What are common signs of a scam?",
        question_hi: "धोखाधड़ी के सामान्य संकेत क्या हैं?",
        answer_en: "Red flags include: urgency (\"act now\"), requests for OTP/passwords, unknown links, poor grammar, threats of account suspension, unrealistic offers, and callers asking for bank details. Never share OTP with anyone.",
        answer_hi: "खतरे के संकेत: तात्कालिकता (\"अब कार्य करें\"), OTP/पासवर्ड की मांग, अज्ञात लिंक, खराब व्याकरण, खाता बंद करने की धमकी, अवास्तविक ऑफर। OTP कभी किसी के साथ साझा न करें।",
        icon: "bi-exclamation-triangle",
        keywords: ["scam signs", "red flags", "warning", "otp", "fraud prevention"],
        helpful_count: 267,
        unhelpful_count: 6
    },
    {
        id: "faq_data_security",
        category: "general",
        question_en: "Is my data secure on RuralAsist?",
        question_hi: "क्या RuralAsist पर मेरा डेटा सुरक्षित है?",
        answer_en: "Yes, we follow strict privacy standards. Uploaded documents are deleted immediately after OCR processing. No personal data is stored unnecessarily. All communications use HTTPS encryption.",
        answer_hi: "हां, हम कड़े गोपनीयता मानकों का पालन करते हैं। OCR प्रसंस्करण के बाद अपलोड किए गए दस्तावेज तुरंत हटा दिए जाते हैं। कोई व्यक्तिगत डेटा अनावश्यक रूप से संग्रहीत नहीं किया जाता।",
        icon: "bi-shield-check",
        keywords: ["security", "privacy", "data protection", "encryption", "safe"],
        helpful_count: 198,
        unhelpful_count: 4
    }
];

// Get current language
function getCurrentLang() {
    return localStorage.getItem(FAQ_LANG_KEY) || 'en';
}

// Get FAQ text based on language
function getFAQText(faq) {
    const lang = getCurrentLang();
    return {
        id: faq.id,
        category: faq.category,
        question: lang === 'hi' ? faq.question_hi : faq.question_en,
        answer: lang === 'hi' ? faq.answer_hi : faq.answer_en,
        icon: faq.icon,
        keywords: faq.keywords || [],
        helpful_count: faq.helpful_count || 0,
        unhelpful_count: faq.unhelpful_count || 0
    };
}

// Initialize FAQ system
function initFAQs() {
    console.log('🚀 Initializing Advanced FAQ System...');
    
    // Get DOM elements
    searchInput = document.getElementById("faq-search");
    faqContainer = document.getElementById("faq-results");
    loadingElement = document.getElementById("faq-loading");
    noResultsElement = document.getElementById("faq-no-results");
    searchSuggestions = document.getElementById("search-suggestions");
    
    console.log('✅ FAQ elements initialized');
    
    // Load all FAQs initially
    allFaqs = ENHANCED_FAQS.map(getFAQText);
    renderFAQs(allFaqs);
    updateStats();
    
    // Set up event listeners
    setupEventListeners();
    setupCategoryFilters();
    setupSearchSuggestions();
    
    console.log('✅ FAQ system ready with', allFaqs.length, 'FAQs');
}

// Setup event listeners
function setupEventListeners() {
    if (searchInput) {
        searchInput.addEventListener("input", handleSearchInput);
        searchInput.addEventListener("focus", showSearchSuggestions);
        searchInput.addEventListener("blur", hideSearchSuggestions);
    }
}

// Setup category filters
function setupCategoryFilters() {
    const categoryButtons = document.querySelectorAll('.category-btn');
    categoryButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active state
            categoryButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter FAQs
            currentCategory = btn.dataset.category;
            filterFAQsByCategory(currentCategory);
        });
    });
}

// Setup search suggestions
function setupSearchSuggestions() {
    const suggestions = [
        'login', 'schemes', 'OCR', 'scam', 'eligibility', 'documents',
        'agriculture', 'education', 'health', 'pension', 'housing',
        'OTP', 'fraud protection', 'text extraction', 'profile'
    ];
    
    if (searchSuggestions) {
        searchSuggestions.innerHTML = suggestions.map(term => 
            `<div class="suggestion-item" data-term="${term}">${term}</div>`
        ).join('');
        
        // Add click handlers
        searchSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const term = e.target.dataset.term;
                searchInput.value = term;
                searchFAQ(term);
                hideSearchSuggestions();
            });
        });
    }
}

// Handle search input with debouncing
function handleSearchInput(e) {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length === 0) {
        resetFAQSearch();
        return;
    }
    
    searchTimeout = setTimeout(() => {
        if (query.length >= 2) {
            searchFAQ(query);
        }
    }, 300);
}

// Show/hide search suggestions
function showSearchSuggestions() {
    if (searchSuggestions && searchInput.value.length === 0) {
        searchSuggestions.style.display = 'block';
    }
}

function hideSearchSuggestions() {
    setTimeout(() => {
        if (searchSuggestions) {
            searchSuggestions.style.display = 'none';
        }
    }, 200);
}

// Advanced search function
async function searchFAQ(query = null) {
    const q = query || (searchInput?.value || "").trim();
    
    if (q.length < 2) {
        resetFAQSearch();
        return;
    }
    
    showLoading(true);
    
    try {
        // Try backend search first
        const response = await fetch(`${API_BASE_URL}/faq/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: q, limit: 20 })
        });
        
        if (response.ok) {
            const data = await response.json();
            const results = data.results || [];
            
            if (results.length > 0) {
                renderFAQs(results);
                showLoading(false);
                return;
            }
        }
    } catch (error) {
        console.log('Backend search failed, using local search:', error.message);
    }
    
    // Fallback to enhanced local search
    const localResults = performLocalSearch(q);
    renderFAQs(localResults);
    showLoading(false);
}

// Enhanced local search with scoring
function performLocalSearch(query) {
    const q = query.toLowerCase().trim();
    const results = [];
    
    allFaqs.forEach(faq => {
        let score = 0;
        
        // Question title match (highest weight)
        if (faq.question.toLowerCase().includes(q)) {
            score += 100;
        }
        
        // Answer content match
        if (faq.answer.toLowerCase().includes(q)) {
            score += 50;
        }
        
        // Keywords match
        faq.keywords.forEach(keyword => {
            if (keyword.toLowerCase().includes(q)) {
                score += 30;
            }
        });
        
        // Category match
        if (faq.category.toLowerCase().includes(q)) {
            score += 40;
        }
        
        // Token-based matching
        const queryTokens = q.split(/\s+/);
        const contentTokens = [
            ...faq.question.toLowerCase().split(/\s+/),
            ...faq.answer.toLowerCase().split(/\s+/),
            ...faq.keywords.map(k => k.toLowerCase())
        ];
        
        queryTokens.forEach(qToken => {
            contentTokens.forEach(cToken => {
                if (cToken.includes(qToken) || qToken.includes(cToken)) {
                    score += 10;
                }
            });
        });
        
        if (score > 0) {
            results.push({ faq, score });
        }
    });
    
    // Sort by score and return FAQs
    results.sort((a, b) => b.score - a.score);
    return results.map(r => r.faq);
}

// Filter FAQs by category
function filterFAQsByCategory(category) {
    if (category === 'all') {
        renderFAQs(allFaqs);
    } else {
        const filtered = allFaqs.filter(faq => faq.category === category);
        renderFAQs(filtered);
    }
}

// Advanced FAQ card rendering
function renderFAQs(faqs) {
    if (!faqContainer) return;
    
    if (faqs.length === 0) {
        showNoResults(true);
        return;
    }
    
    showNoResults(false);
    
    faqContainer.innerHTML = faqs.map((faq, index) => {
        const categoryEmoji = getCategoryEmoji(faq.category);
        const categoryName = getCategoryName(faq.category);
        return `
            <div class="faq-card" data-aos="fade-up" data-aos-delay="${index * 50}" data-id="${escapeHTML(faq.id)}">
                <div class="faq-question" onclick="toggleFAQ(this)">
                    <div>
                        <div class="faq-category-badge">${categoryEmoji} ${escapeHTML(categoryName)}</div>
                        <div>${escapeHTML(faq.question)}</div>
                    </div>
                    <div class="faq-toggle">
                        <i class="bi bi-plus"></i>
                    </div>
                </div>
                <div class="faq-answer">
                    <p>${escapeHTML(faq.answer).replace(/\n/g, "<br>")}</p>
                </div>
                <div class="faq-voting">
                    <div class="vote-buttons">
                        <button class="vote-btn" onclick="voteFAQ('${escapeHTML(faq.id)}', 'helpful')" data-type="helpful">
                            <i class="bi bi-hand-thumbs-up"></i>
                            <span>${faq.helpful_count}</span>
                        </button>
                        <button class="vote-btn" onclick="voteFAQ('${escapeHTML(faq.id)}', 'unhelpful')" data-type="unhelpful">
                            <i class="bi bi-hand-thumbs-down"></i>
                            <span>${faq.unhelpful_count}</span>
                        </button>
                    </div>
                    <small class="text-muted">Was this helpful?</small>
                </div>
            </div>
        `;
    }).join('');
    
    // Initialize AOS for new elements
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

// Toggle FAQ expansion
function toggleFAQ(element) {
    const card = element.closest('.faq-card');
    const isExpanded = card.classList.contains('expanded');
    
    // Close all other FAQs
    document.querySelectorAll('.faq-card.expanded').forEach(c => {
        if (c !== card) {
            c.classList.remove('expanded');
        }
    });
    
    // Toggle current FAQ
    card.classList.toggle('expanded');
}

// Vote for FAQ helpfulness
function voteFAQ(faqId, voteType) {
    // Check if already voted
    const votedFaqs = JSON.parse(localStorage.getItem('votedFaqs') || '{}');
    if (votedFaqs[faqId]) {
        return; // Already voted
    }
    
    // Find FAQ and update count
    const faq = ENHANCED_FAQS.find(f => f.id === faqId);
    if (faq) {
        if (voteType === 'helpful') {
            faq.helpful_count++;
        } else {
            faq.unhelpful_count++;
        }
        
        // Mark as voted
        votedFaqs[faqId] = voteType;
        localStorage.setItem('votedFaqs', JSON.stringify(votedFaqs));
        
        // Update display
        const card = document.querySelector(`[data-id="${faqId}"]`);
        if (card) {
            const btn = card.querySelector(`[data-type="${voteType}"]`);
            if (btn) {
                btn.classList.add('voted');
                btn.querySelector('span').textContent = 
                    voteType === 'helpful' ? faq.helpful_count : faq.unhelpful_count;
            }
        }
        
        // Send to backend if available
        sendVoteToBackend(faqId, voteType);
    }
}

// Send vote to backend
async function sendVoteToBackend(faqId, voteType) {
    try {
        await fetch(`${API_BASE_URL}/faq/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ faq_id: faqId, vote_type: voteType })
        });
    } catch (error) {
        console.log('Vote sync failed:', error);
    }
}

// Get category emoji and name
function getCategoryEmoji(category) {
    const emojis = {
        'schemes': '📋',
        'ocr': '📄',
        'scam': '🛡️',
        'general': '❓'
    };
    return emojis[category] || '❓';
}

function getCategoryName(category) {
    const lang = getCurrentLang();
    const names = {
        'schemes': lang === 'hi' ? 'योजनाएं' : 'Schemes',
        'ocr': 'OCR',
        'scam': lang === 'hi' ? 'धोखाधड़ी सुरक्षा' : 'Scam Protection',
        'general': lang === 'hi' ? 'सामान्य' : 'General'
    };
    return names[category] || category;
}

// Update statistics
function updateStats() {
    const totalElement = document.getElementById('total-faqs');
    const categoriesElement = document.getElementById('categories-count');
    
    if (totalElement) totalElement.textContent = allFaqs.length;
    if (categoriesElement) {
        const uniqueCategories = [...new Set(allFaqs.map(faq => faq.category))];
        categoriesElement.textContent = uniqueCategories.length;
    }
}

// Show/hide loading state
function showLoading(show) {
    if (loadingElement) {
        loadingElement.classList.toggle('d-none', !show);
    }
    if (faqContainer) {
        faqContainer.style.opacity = show ? '0.5' : '1';
    }
}

// Show/hide no results
function showNoResults(show) {
    if (noResultsElement) {
        noResultsElement.classList.toggle('d-none', !show);
    }
    if (faqContainer) {
        faqContainer.style.display = show ? 'none' : 'grid';
    }
}

// Reset search
function resetFAQSearch() {
    if (searchInput) searchInput.value = '';
    currentCategory = 'all';
    
    // Reset category buttons
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === 'all');
    });
    
    renderFAQs(allFaqs);
    showLoading(false);
    showNoResults(false);
}

// Global search function for quick search buttons
window.searchFAQ = searchFAQ;
window.resetFAQSearch = resetFAQSearch;
window.toggleFAQ = toggleFAQ;
window.voteFAQ = voteFAQ;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFAQs);
} else {
    initFAQs();
}
