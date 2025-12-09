// Use global config if available, fallback to direct URL
const API_BASE_URL = window.AppConfig?.API_BASE_URL || "https://rural-asist.onrender.com";

document.addEventListener('DOMContentLoaded', () => {
  const emailEl = document.getElementById('prof-email');
  const nameEl = document.getElementById('prof-name');
  const saveBtn = document.getElementById('prof-save');
  const statusEl = document.getElementById('prof-status');

  const token = localStorage.getItem('ruralassist_token');
  if (!token) return; // guarded by profile.html inline script already

  async function loadProfile() {
    statusEl.textContent = 'Loading profile...';
    try {
      const res = await fetch(`${API_BASE_URL}/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load profile');
      emailEl.value = data.email || '';
      nameEl.value = data.name || '';
      statusEl.textContent = '';
    } catch (e) {
      statusEl.textContent = e.message;
    }
  }

  async function saveProfile() {
    const name = nameEl.value.trim();
    saveBtn.disabled = true;
    statusEl.textContent = 'Saving...';
    try {
      const res = await fetch(`${API_BASE_URL}/profile/me`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save profile');
      statusEl.textContent = 'Saved!';
      // also persist locally for quick access
      try { localStorage.setItem('ruralassist_name', data.name || ''); } catch {}
    } catch (e) {
      statusEl.textContent = e.message;
    }
    saveBtn.disabled = false;
  }

  saveBtn.addEventListener('click', saveProfile);
  loadProfile();
});
