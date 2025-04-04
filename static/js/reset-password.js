document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const requestForm = document.getElementById('requestForm');
    const verifyForm = document.getElementById('verifyForm');
    const passwordForm = document.getElementById('passwordForm');
    const requestCard = document.getElementById('requestCard');
    const verifyCard = document.getElementById('verifyCard');
    const passwordCard = document.getElementById('passwordCard');
    const emailDisplay = document.getElementById('emailDisplay');
    const resendCodeBtn = document.getElementById('resendCode');
    const countdownEl = document.getElementById('countdown');
    const successModal = document.querySelector('.success-modal');
    const togglePwBtns = document.querySelectorAll('.toggle-pw');
    const newPasswordInput = document.getElementById('newPassword');
    const progressFill = document.querySelector('.progress-fill');
    const steps = document.querySelectorAll('.step');

    // State
    let countdownInterval;
    let userEmail = '';

    // ✅ Initialize Functions
    initCodeInputs();
    initPasswordStrength();

    // 1. Request Code Form
    requestForm.addEventListener('submit', function (e) {
        e.preventDefault();
        userEmail = document.getElementById('userEmail').value.trim();

        if (!validateEmail(userEmail)) {
            showError(requestForm, 'Please enter a valid email address');
            return;
        }

        showLoading(requestForm.querySelector('button'));
        simulateSendCode(userEmail);
    });

    // 2. Verify Code Form
    verifyForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const enteredCode = getEnteredCode();

        if (enteredCode.length !== 6) {
            showError(verifyForm, 'Please enter the full 6-digit code');
            return;
        }

        fetch('/verify_reset_codes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enteredCode })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    showError(verifyForm, data.error);
                } else {
                    showNextStep(2);
                }
            })
            .catch(error => {
                showError(verifyForm, 'An error occurred. Please try again.');
            });
    });

    // 3. New Password Form
    passwordForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const password = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            showError(passwordForm, 'Passwords do not match');
            return;
        }

        if (password.length < 8) {
            showError(passwordForm, 'Password must be at least 8 characters');
            return;
        }

        showLoading(passwordForm.querySelector('button'));
        simulateUpdatePassword(password);
    });

    // Resend Code Button
    resendCodeBtn.addEventListener('click', function () {
        console.log('✅ Button Clicked!');
        simulateSendCode(userEmail);
    });

    // Toggle Password Visibility
    togglePwBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const input = this.parentElement.querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.classList.toggle('fa-eye-slash');
        });
    });

    // Helper Functions
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function showError(form, message) {
        let existingError = form.querySelector('.error-message');
        if (existingError) existingError.remove();

        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = message;
        errorEl.style.color = 'var(--error)';
        errorEl.style.marginTop = '10px';
        errorEl.style.fontSize = '14px';

        form.appendChild(errorEl);
    }

    function showLoading(button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        button.disabled = true;

        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }, 2000);
    }

    function simulateSendCode(email) {
        fetch('/send_reset_codes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    emailDisplay.textContent = email;
                    showNextStep(1);
                    startCountdown(300);
                }
            });
    }

    function showNextStep(currentStep) {
        progressFill.style.width = `${(currentStep / 3) * 100}%`;

        steps.forEach((step, index) => {
            step.classList.toggle('active', index <= currentStep);
        });

        if (currentStep === 1) {
            requestCard.classList.remove('active');
            verifyCard.classList.add('active');
        } else if (currentStep === 2) {
            verifyCard.classList.remove('active');
            passwordCard.classList.add('active');
        } else if (currentStep === 3) {
            passwordCard.classList.remove('active');
            successModal.style.display = 'flex';
        }
    }

    function startCountdown(seconds) {
        clearInterval(countdownInterval);

        function updateCountdown() {
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            countdownEl.textContent = `${mins}:${secs}`;

            if (seconds <= 0) {
                clearInterval(countdownInterval);
                countdownEl.textContent = 'Expired';
                countdownEl.style.color = 'var(--error)';
            }
            seconds--;
        }

        updateCountdown();
        countdownInterval = setInterval(updateCountdown, 1000);
    }

    function getEnteredCode() {
        return Array.from(verifyForm.querySelectorAll('input'))
            .map(input => input.value)
            .join('');
    }

    function initCodeInputs() {
        const inputs = verifyForm.querySelectorAll('input');

        inputs.forEach((input, index) => {
            input.addEventListener('input', function () {
                if (this.value.length === 1 && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            });

            input.addEventListener('keydown', function (e) {
                if (e.key === 'Backspace' && this.value.length === 0 && index > 0) {
                    inputs[index - 1].focus();
                }
            });
        });
    }

    function initPasswordStrength() {
        if (!newPasswordInput) return;

        newPasswordInput.addEventListener('input', function () {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            const inputGroup = this.parentElement;

            inputGroup.classList.remove('weak', 'medium', 'strong','weakest');

            if (password.length > 0) {
                inputGroup.classList.add(strength);
            }
        });
    }

    function checkPasswordStrength(password) {
        if (password.length === 0) return '';

        const hasUpper = /[A-Z]/.test(password);
        const hasLower = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[^A-Za-z0-9]/.test(password);

        let strength = 0;
        if (password.length >= 6) strength++;
        if (hasUpper && hasLower) strength++;
        if (hasNumber) strength++;
        if (hasSpecial) strength++;

        if (password.length >= 12 && strength >= 3) return 'strong';
        if (password.length >= 8 && strength >= 2) return 'medium';
        if (password.length >= 6 && strength >= 1) return 'weak';
        if(password.length <5 && strength >= 0) return 'weakest';
    }

    function simulateUpdatePassword(password) {
        fetch('/update_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    setTimeout(() => showNextStep(3), 1500);
                }
            })
            .catch(() => alert('An error occurred. Please try again.'));
    }
});
