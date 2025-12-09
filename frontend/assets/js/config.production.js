/**
 * Production Configuration for Deployment
 * This file will be used to override local config when deployed
 */

const ProductionConfig = {
    // API Configuration - will be updated with actual Render URL
    API_BASE_URL: "https://ruralasist-jhwx.onrender.com",
    
    // File upload limits
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_FILE_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'],
    
    // Local storage keys
    STORAGE_KEYS: {
        TOKEN: 'ruralassist_token',
        LANGUAGE: 'ruralassist_language',
        USER_NAME: 'ruralassist_name',
        USER_EMAIL: 'user_email',
        LOGIN_REDIRECT: 'login_redirect_target',
        LOGGED_IN: 'ruralassist_logged_in'
    },
    
    // Cache configuration
    CACHE_KEYS: {
        SCHEMES: 'schemes_cache',
        FAQ: 'faq_cache'
    },
    CACHE_EXPIRY: 60 * 60 * 1000, // 1 hour
    
    // UI Configuration
    FEATURES: {
        CHATBOT_ENABLED: true,
        PWA_ENABLED: true,
        OFFLINE_MODE: true
    },
    
    // Language configuration
    DEFAULT_LANGUAGE: 'en',
    SUPPORTED_LANGUAGES: ['en', 'hi'],
    
    // Retry configuration
    RETRY_DELAYS: {
        CHAT_INIT: 100,
        API_REQUEST: 1000
    },
    MAX_RETRIES: {
        CHAT_INIT: 20,
        API_REQUEST: 3
    },
    
    // Production mode
    DEBUG: false,
    
    // Rate limiting
    RATE_LIMITS: {
        CHAT_MESSAGE: 1000, // 1 second between messages
        OTP_RESEND: 30000   // 30 seconds between OTP resends
    }
};

// Override local config in production
if (typeof window !== 'undefined') {
    window.AppConfig = ProductionConfig;
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProductionConfig;
}