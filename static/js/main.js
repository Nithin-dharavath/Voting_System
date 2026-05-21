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
});
