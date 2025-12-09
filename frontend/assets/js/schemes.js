document.addEventListener('DOMContentLoaded', () => {
    // API Configuration
    const API_BASE_URL = window.AppConfig?.API_BASE_URL;
    
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 600, once: true });
    }

    // --- DOM Elements ---
    const filterBtn = document.getElementById('filterBtn');
    const schemesListContainer = document.getElementById('schemesListContainer');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const searchQueryInput = document.getElementById('searchQueryInput');
    const stateSelectInput = document.getElementById('stateSelectInput');
    const categorySelectInput = document.getElementById('categorySelectInput');

    // --- Skeleton helpers & quick actions ---
    const SKELETON_COUNT = 8;
    const SAVED_KEY = 'ruralassist_saved_schemes';

    function renderSkeletons() {
        if (!schemesListContainer) return;
        const frag = document.createDocumentFragment();
        for (let i = 0; i < SKELETON_COUNT; i++) {
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';
            col.innerHTML = `
                <div class="skeleton-scheme-card">
                  <div class="skeleton skeleton-text title"></div>
                  <div class="skeleton skeleton-text line"></div>
                  <div class="skeleton skeleton-text line w-80"></div>
                  <div class="skeleton skeleton-block footer"></div>
                </div>`;
            frag.appendChild(col);
        }
        schemesListContainer.innerHTML = '';
        schemesListContainer.appendChild(frag);
    }

    function getSavedSet() {
        try { return new Set(JSON.parse(localStorage.getItem(SAVED_KEY) || '[]')); } catch { return new Set(); }
    }
    function setSavedSet(set) {
        try { localStorage.setItem(SAVED_KEY, JSON.stringify(Array.from(set))); } catch {}
    }
    function isSaved(id) { return getSavedSet().has(String(id)); }
    function toggleSave(id, btn) {
        const set = getSavedSet();
        const key = String(id);
        if (set.has(key)) {
            set.delete(key);
            btn.innerHTML = '<i class="bi bi-bookmark"></i>';
            btn.setAttribute('aria-pressed', 'false');
            btn.classList.remove('active');
        } else {
            set.add(key);
            btn.innerHTML = '<i class="bi bi-bookmark-fill"></i>';
            btn.setAttribute('aria-pressed', 'true');
            btn.classList.add('active');
        }
        setSavedSet(set);
    }

    function attachActions(root) {
        if (!root) return;
        root.addEventListener('click', async (e) => {
            const btn = e.target.closest('button.btn-icon');
            if (!btn) return;
            const action = btn.getAttribute('data-action');
            const id = btn.getAttribute('data-id');
            if (action === 'save') {
                toggleSave(id, btn);
            } else if (action === 'eligibility') {
                alert('Eligibility checker coming soon for scheme #' + id);
            } else if (action === 'share') {
                const url = location.origin + location.pathname + '?scheme=' + encodeURIComponent(id);
                if (navigator.share) {
                    try { await navigator.share({ title: 'Scheme', text: 'Check this scheme', url }); return; } catch {}
                }
                try { await navigator.clipboard.writeText(url); showToast('Link copied'); }
                catch { showToast('Copy failed: ' + url); }
            }
        });
        // Initialize Bootstrap tooltips if available
        if (window.bootstrap) {
            [...root.querySelectorAll('[data-bs-toggle="tooltip"]')].forEach(el => {
                if (!bootstrap.Tooltip.getInstance(el)) new bootstrap.Tooltip(el);
            });
        }
    }

    function showToast(message) {
        if (window.bootstrap) {
            let host = document.getElementById('toastHost');
            if (!host) {
                host = document.createElement('div');
                host.id = 'toastHost';
                host.className = 'position-fixed bottom-0 end-0 p-3';
                host.style.zIndex = 1080;
                document.body.appendChild(host);
            }
            const el = document.createElement('div');
            el.className = 'toast align-items-center text-bg-success border-0';
            el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite'); el.setAttribute('aria-atomic', 'true');
            el.innerHTML = `<div class="d-flex"><div class="toast-body">${escapeHtml(message)}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
            host.appendChild(el);
            const t = new bootstrap.Toast(el, { delay: 1600 }); t.show();
            setTimeout(() => el.remove(), 2000);
        } else {
            alert(message);
        }
    }

        // Shared HTML escape utility
        function escapeHtml(unsafe) {
            if (typeof unsafe !== "string") return unsafe;
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

    // --- Event Listeners ---
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            const filters = {
                q: searchQueryInput.value,
                state: stateSelectInput.value,
                category: categorySelectInput.value
            };
            fetchSchemes(filters);
        });
    }
    if (searchQueryInput) {
        searchQueryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && filterBtn) filterBtn.click();
        });
    }

    // --- Functions ---
    async function fetchSchemes(filters = {}) {
        if (loadingIndicator) loadingIndicator.classList.remove('d-none');
        renderSkeletons();

        const params = new URLSearchParams();
        if (filters.q) params.append('q', filters.q);
        if (filters.state) params.append('state', filters.state);
        if (filters.category) params.append('category', filters.category);

        // Use search endpoint if any filters, otherwise use local endpoint
        const endpoint = (filters.q || filters.state || filters.category) ? '/schemes/search' : '/schemes/local';
        const url = `${API_BASE_URL}${endpoint}${(filters.q || filters.state || filters.category) ? '?' + params.toString() : ''}`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Handle different response formats
            let schemes = [];
            if (endpoint === '/schemes/local') {
                schemes = data.schemes || [];
            } else {
                schemes = data.schemes || [];
            }
            
            renderSchemes(schemes);
        } catch (error) {
            console.error('Error fetching schemes:', error);
            if (schemesListContainer) schemesListContainer.innerHTML = '<div class="col-12"><div class="alert alert-danger text-center">Could not load schemes. Please ensure the backend server is running and try again.</div></div>';
        } finally {
            if (loadingIndicator) loadingIndicator.classList.add('d-none');
        }
    }

    function renderSchemes(schemes, eligibilityCheck = false) {
        if (!schemesListContainer) return;
        schemesListContainer.innerHTML = '';
        if (!schemes || schemes.length === 0) {
            schemesListContainer.innerHTML = '<div class="col-12"><div class="alert alert-info text-center">No schemes found matching your criteria.</div></div>';
            return;
        }
        const frag = document.createDocumentFragment();
        schemes.forEach((scheme, index) => {
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';
            col.setAttribute('data-aos', 'fade-up');
            col.setAttribute('data-aos-delay', (index % 3) * 100);
            const saved = isSaved(scheme.id);
            col.innerHTML = `
                <div class="card scheme-card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>${escapeHtml(scheme.title)}</span>
                        <div class="scheme-actions">
                            <button class="btn-icon ${saved ? 'active' : ''}" type="button" data-action="save" data-id="${scheme.id}" ${saved ? 'aria-pressed="true"' : 'aria-pressed="false"'} aria-label="Save scheme" data-bs-toggle="tooltip" title="Save">
                                <i class="bi ${saved ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>
                            </button>
                            <button class="btn-icon" type="button" data-action="eligibility" data-id="${scheme.id}" aria-label="Check eligibility" data-bs-toggle="tooltip" title="Eligibility">
                                <i class="bi bi-clipboard-check"></i>
                            </button>
                            <button class="btn-icon" type="button" data-action="share" data-id="${scheme.id}" aria-label="Share scheme" data-bs-toggle="tooltip" title="Share">
                                <i class="bi bi-share"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="card-text small">${escapeHtml(scheme.description || scheme.summary || '')}</p>
                        ${scheme.benefits ? `<p><strong>Benefits:</strong> ${escapeHtml(scheme.benefits)}</p>` : ''}
                    </div>
                    <div class="card-footer bg-white border-top-0">
                         <a href="${scheme.apply_link || ('schemes.html?q=' + encodeURIComponent(scheme.query || ''))}" target="_blank" class="btn btn-sm btn-outline-secondary w-100">Learn More</a>
                    </div>
                </div>`;
            frag.appendChild(col);
        });
        schemesListContainer.appendChild(frag);
        attachActions(schemesListContainer);
        if (typeof AOS !== 'undefined') AOS.refresh();
    }

    // Initial load of all schemes
    fetchSchemes();
});
