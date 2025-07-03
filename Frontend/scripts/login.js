
        // Tab switching functionality
        document.addEventListener('DOMContentLoaded', function() {
            const tabs = document.querySelectorAll('.auth-tab');
            const forms = document.querySelectorAll('.auth-form');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const targetTab = this.dataset.tab;
                    
                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Update active form
                    forms.forEach(form => {
                        form.classList.remove('active');
                        if (form.id === `${targetTab}-form`) {
                            form.classList.add('active');
                        }
                    });
                });
            });

            // Password strength indicator
            const passwordInput = document.getElementById('signup-password');
            const strengthFill = document.getElementById('strength-fill');
            const strengthText = document.getElementById('strength-text');
            
            if (passwordInput) {
                passwordInput.addEventListener('input', function() {
                    const password = this.value;
                    const strength = calculatePasswordStrength(password);
                    updatePasswordStrength(strength);
                });
            }

            // Confirm password matching
            const confirmPasswordInput = document.getElementById('signup-confirm-password');
            if (confirmPasswordInput) {
                confirmPasswordInput.addEventListener('input', function() {
                    const password = document.getElementById('signup-password').value;
                    const confirmPassword = this.value;
                    
                    if (confirmPassword && password !== confirmPassword) {
                        this.classList.add('error');
                        this.classList.remove('success');
                    } else if (confirmPassword && password === confirmPassword) {
                        this.classList.add('success');
                        this.classList.remove('error');
                    } else {
                        this.classList.remove('error', 'success');
                    }
                });
            }

            // Form submission handling
            const signinForm = document.getElementById('signin-form');
            const signupForm = document.getElementById('signup-form');

            if (signinForm) {
                signinForm.addEventListener('submit', handleFormSubmit);
            }
            
            if (signupForm) {
                signupForm.addEventListener('submit', handleFormSubmit);
            }

            // Forgot password handler
            const forgotPasswordLink = document.getElementById('forgot-password-link');
            if (forgotPasswordLink) {
                forgotPasswordLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    alert('Password reset functionality would be implemented here. Please contact your system administrator.');
                });
            }
        });

        function calculatePasswordStrength(password) {
            let score = 0;
            
            if (password.length >= 8) score += 1;
            if (password.length >= 12) score += 1;
            if (/[a-z]/.test(password)) score += 1;
            if (/[A-Z]/.test(password)) score += 1;
            if (/[0-9]/.test(password)) score += 1;
            if (/[^A-Za-z0-9]/.test(password)) score += 1;
            
            return Math.min(score, 4);
        }

        function updatePasswordStrength(strength) {
            const strengthFill = document.getElementById('strength-fill');
            const strengthText = document.getElementById('strength-text');
            
            strengthFill.className = 'password-strength-fill';
            
            switch (strength) {
                case 0:
                case 1:
                    strengthFill.classList.add('strength-weak');
                    strengthText.textContent = 'Weak';
                    break;
                case 2:
                    strengthFill.classList.add('strength-fair');
                    strengthText.textContent = 'Fair';
                    break;
                case 3:
                    strengthFill.classList.add('strength-good');
                    strengthText.textContent = 'Good';
                    break;
                case 4:
                    strengthFill.classList.add('strength-strong');
                    strengthText.textContent = 'Strong';
                    break;
            }
        }

        function handleFormSubmit(e) {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = form.querySelector('.btn-primary');
            const formData = new FormData(form);
            
            // Add loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            
            // Convert FormData to regular object
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Simulate API call
            setTimeout(() => {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
                
                if (form.id === 'signin-form') {
                    // Simulate successful login
                    alert('Login successful! Redirecting to dashboard...');
                    window.location.href = '../index.html';
                } else {
                    // Simulate successful signup
                    alert('Account created successfully! Please sign in.');
                    // Switch to signin tab
                    document.querySelector('[data-tab="signin"]').click();
                }
            }, 2000);
        }

        // Utility function for CSRF token (if needed)
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
