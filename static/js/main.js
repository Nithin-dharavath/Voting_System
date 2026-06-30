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
                const newUrl = window.location.pathname;
                window.history.replaceState({}, document.title, newUrl);
            }, 3000);
        }
    }

    const editProfileBtn = document.getElementById('nav-edit-profile-btn');
    if (editProfileBtn) {
        if (window.location.pathname === '/profile') {
            editProfileBtn.classList.remove('hidden');
        } else {
            editProfileBtn.classList.add('hidden');
        }
    }

    setupSkipLink();
    setupFormValidation();
    setupPasswordStrength();
});

function setupSkipLink() {
    const skipLink = document.querySelector('.skip-link');
    if (skipLink) {
        skipLink.addEventListener('focus', () => {
            skipLink.style.left = '0';
        });
        skipLink.addEventListener('blur', () => {
            skipLink.style.left = '-9999px';
        });
        skipLink.addEventListener('click', (e) => {
            e.preventDefault();
            const main = document.getElementById('main-content');
            if (main) {
                main.setAttribute('tabindex', '-1');
                main.focus();
            }
        });
    }
}

function setupFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;
            requiredFields.forEach(field => {
                if (!field.value || field.value.trim() === '') {
                    markInvalid(field, 'This field is required.');
                    valid = false;
                } else if (field.type === 'email' && !isValidEmail(field.value)) {
                    markInvalid(field, 'Please enter a valid email address.');
                    valid = false;
                } else if (field.hasAttribute('minlength') && field.value.length < parseInt(field.getAttribute('minlength'))) {
                    markInvalid(field, `Must be at least ${field.getAttribute('minlength')} characters.`);
                    valid = false;
                } else if (field.hasAttribute('pattern') && field.value && !new RegExp(field.getAttribute('pattern')).test(field.value)) {
                    markInvalid(field, 'Please match the requested format.');
                    valid = false;
                } else {
                    clearInvalid(field);
                }
            });
            if (!valid) {
                e.preventDefault();
            }
        });

        form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('input', () => {
                if (field.hasAttribute('aria-invalid') && field.value.trim() !== '') {
                    clearInvalid(field);
                }
            });
        });
    });
}

function setupPasswordStrength() {
    const passwordField = document.getElementById('password');
    if (passwordField) {
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';
        strengthIndicator.setAttribute('aria-live', 'polite');
        passwordField.parentNode.appendChild(strengthIndicator);

        passwordField.addEventListener('input', () => {
            const val = passwordField.value;
            let strength = 'weak';
            let score = 0;
            if (val.length >= 8) score++;
            if (val.length >= 12) score++;
            if (/[a-z]/.test(val) && /[A-Z]/.test(val)) score++;
            if (/\d/.test(val)) score++;
            if (/[^a-zA-Z0-9]/.test(val)) score++;
            if (score <= 1) strength = 'weak';
            else if (score <= 3) strength = 'medium';
            else strength = 'strong';
            strengthIndicator.className = `password-strength strength-${strength}`;
            strengthIndicator.textContent = `Password strength: ${strength}`;
        });
    }
}

function isValidEmail(email) {
    return /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(email);
}

function markInvalid(field, message) {
    field.setAttribute('aria-invalid', 'true');
    let errorEl = field.parentNode.querySelector('.field-error');
    if (!errorEl) {
        errorEl = document.createElement('span');
        errorEl.className = 'field-error';
        errorEl.setAttribute('role', 'alert');
        field.parentNode.appendChild(errorEl);
    }
    errorEl.textContent = message;
}

function clearInvalid(field) {
    field.removeAttribute('aria-invalid');
    const errorEl = field.parentNode.querySelector('.field-error');
    if (errorEl) {
        errorEl.remove();
    }
}

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
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 3l4 4-4 4"/><path d="M21 6H3"/><path d="M17 21l-4-4 4-4"/><path d="M3 18h18"/></svg> Edit Profile';
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
