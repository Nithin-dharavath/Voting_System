document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');
    if (loginSuccess === 'success') {
        showToast('Login successful! Welcome back.', 'success');
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }

    const breachWarning = getCookie('breach_warning');
    if (breachWarning) {
        showToast(decodeURIComponent(breachWarning), 'warning');
        document.cookie = 'breach_warning=; Max-Age=0; path=/';
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
    setupLoadingStates();
    setupBackToTop();
});

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
}

function showToast(message, type) {
    type = type || 'success';
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    const icons = { success: '&#10004;', error: '&#10006;', info: '&#9432;', warning: '&#9888;' };
    toast.innerHTML = '<span class="toast-icon">' + (icons[type] || icons.info) + '</span>' +
        '<span class="toast-msg">' + message + '</span>' +
        '<button class="toast-close" onclick="this.parentElement.remove()" aria-label="Dismiss">&times;</button>';
    container.appendChild(toast);
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(120%)';
        setTimeout(function() { toast.remove(); }, 400);
    }, 5000);
}

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
    if (!passwordField) return;

    const container = document.createElement('div');
    container.className = 'password-strength-container';

    const bar = document.createElement('div');
    bar.className = 'password-strength-bar';
    const barFill = document.createElement('div');
    barFill.className = 'password-strength-bar-fill';
    bar.appendChild(barFill);
    container.appendChild(bar);

    const checklist = document.createElement('ul');
    checklist.className = 'password-checklist';
    checklist.setAttribute('aria-live', 'polite');
    const rules = [
        { key: 'length', label: 'At least 12 characters', test: (v) => v.length >= 12 },
        { key: 'upper', label: 'One uppercase letter', test: (v) => /[A-Z]/.test(v) },
        { key: 'lower', label: 'One lowercase letter', test: (v) => /[a-z]/.test(v) },
        { key: 'digit', label: 'One digit', test: (v) => /\d/.test(v) },
        { key: 'special', label: 'One special character', test: (v) => /[^a-zA-Z0-9]/.test(v) },
    ];
    rules.forEach((rule) => {
        const li = document.createElement('li');
        li.className = 'pwd-check-item';
        li.dataset.rule = rule.key;
        li.textContent = rule.label;
        checklist.appendChild(li);
    });
    container.appendChild(checklist);
    passwordField.parentNode.appendChild(container);

    passwordField.addEventListener('input', () => {
        const val = passwordField.value;
        let score = 0;
        rules.forEach((rule) => {
            const li = checklist.querySelector(`[data-rule="${rule.key}"]`);
            const passed = rule.test(val);
            li.classList.toggle('pwd-check-pass', passed);
            li.classList.toggle('pwd-check-fail', !passed);
            if (passed) score++;
        });

        const pct = Math.round((score / rules.length) * 100);
        barFill.style.width = pct + '%';
        barFill.className = 'password-strength-bar-fill';
        if (pct <= 40) barFill.classList.add('strength-weak');
        else if (pct <= 80) barFill.classList.add('strength-medium');
        else barFill.classList.add('strength-strong');
    });

    const form = passwordField.closest('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const val = passwordField.value;
            const allPassed = rules.every((r) => r.test(val));
            if (!allPassed) {
                e.preventDefault();
                passwordField.setAttribute('aria-invalid', 'true');
                let errorEl = passwordField.parentNode.querySelector('.field-error');
                if (!errorEl) {
                    errorEl = document.createElement('span');
                    errorEl.className = 'field-error';
                    errorEl.setAttribute('role', 'alert');
                    passwordField.parentNode.appendChild(errorEl);
                }
                errorEl.textContent = 'Please meet all password requirements.';
            }
        });
    }
}

function setupLoadingStates() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            const btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                const hasRequired = form.querySelectorAll('[required]');
                let valid = true;
                hasRequired.forEach(f => { if (!f.value) valid = false; });
                if (!valid) return;
                btn.disabled = true;
                const orig = btn.innerHTML;
                btn.innerHTML = '<span class="spinner"></span> <span class="btn-text">Processing...</span>';
                btn.dataset.origHtml = orig;
                setTimeout(() => { btn.disabled = false; }, 10000);
            }
        });
    });
}

function setupBackToTop() {
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"/></svg>';
    document.body.appendChild(btn);
    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 400);
    });
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
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
