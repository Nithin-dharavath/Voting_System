// Main JavaScript file for the Voting System
console.log("Voting System JS initialized");

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');

    if (loginSuccess === 'success') {
        const toast = document.getElementById('toast-notification');
        if (toast) {
            toast.textContent = 'Login successful! Welcome back.';
            toast.classList.remove('hidden');

            setTimeout(() => {
                toast.classList.add('hidden');
                // Remove the query param from URL without refreshing the page
                const newUrl = window.location.pathname;
                window.history.replaceState({}, document.title, newUrl);
            }, 3000);
        }
    }

    // Handle Profile Edit Button Visibility
    const editProfileBtn = document.getElementById('nav-edit-profile-btn');
    if (editProfileBtn) {
        if (window.location.pathname === '/profile') {
            editProfileBtn.classList.remove('hidden');
        } else {
            editProfileBtn.classList.add('hidden');
        }
    }
});

function switchTab(event, tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    event.currentTarget.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

function toggleEditMode() {
    const btn = document.getElementById('nav-edit-profile-btn');
    const actions = document.getElementById('form-actions');
    if (!btn || !actions) return;

    const isEditing = actions.style.display === 'flex';

    if (isEditing) {
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3l4 4-4 4"/><path d="M21 6H3"/><path d="M17 21l-4-4 4-4"/><path d="M3 18h18"/></svg> Edit Profile`;
        actions.style.display = 'none';
        document.querySelectorAll('.input-wrapper .info-box').forEach(box => box.style.display = 'flex');
        document.querySelectorAll('.info-input').forEach(input => input.style.display = 'none');
    } else {
        btn.innerHTML = 'Cancel';
        actions.style.display = 'flex';
        document.querySelectorAll('.input-wrapper .info-box').forEach(box => box.style.display = 'none');
        document.querySelectorAll('.info-input').forEach(input => input.style.display = 'block');
    }
}
