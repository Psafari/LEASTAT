// scripts/validation.js
class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.fields = Array.from(formElement.querySelectorAll('[data-validate]'));
        this.init();
    }
    
    init() {
        this.form.addEventListener('submit', this.validateForm.bind(this));
        
        this.fields.forEach(field => {
            field.addEventListener('blur', this.validateField.bind(this));
            field.addEventListener('input', this.clearError.bind(this));
        });
    }
    
    validateForm(e) {
        e.preventDefault();
        let isValid = true;
        
        this.fields.forEach(field => {
            if(!this.validateField({ target: field })) {
                isValid = false;
            }
        });
        
        if(isValid) {
            this.submitForm();
        }
    }
    
    validateField(e) {
        const field = e.target;
        const value = field.value.trim();
        const rules = field.dataset.validate.split('|');
        
        field.classList.remove('error');
        this.clearErrorMsg(field);
        
        for(const rule of rules) {
            const [ruleName, ruleValue] = rule.split(':');
            
            if(!this[`validate_${ruleName}`](value, ruleValue)) {
                this.showError(field, ruleName);
                return false;
            }
        }
        
        field.classList.add('success');
        return true;
    }
    
    clearError(e) {
        const field = e.target;
        field.classList.remove('error', 'success');
        this.clearErrorMsg(field);
    }
    
    clearErrorMsg(field) {
        const errorMsg = field.nextElementSibling;
        if(errorMsg && errorMsg.classList.contains('error-message')) {
            errorMsg.remove();
        }
    }
    
    showError(field, ruleName) {
        field.classList.add('error');
        
        const messages = {
            required: 'This field is required',
            email: 'Please enter a valid email address',
            min: `Minimum length is ${field.dataset.validate.split('min:')[1].split('|')[0]}`,
            max: `Maximum length is ${field.dataset.validate.split('max:')[1].split('|')[0]}`,
            numeric: 'Please enter a valid number',
            match: 'Values do not match'
        };
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'error-message';
        errorMsg.innerHTML = `
            <span class="error-icon">!</span>
            <span>${messages[ruleName]}</span>
        `;
        
        field.after(errorMsg);
    }
    
    // Validation methods
    validate_required(value) {
        return value !== '';
    }
    
    validate_email(value) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    }
    
    validate_min(value, min) {
        return value.length >= parseInt(min);
    }
    
    validate_max(value, max) {
        return value.length <= parseInt(max);
    }
    
    validate_numeric(value) {
        return !isNaN(value);
    }
    
    validate_match(value, fieldName) {
        const fieldToMatch = this.form.querySelector(`[name="${fieldName}"]`);
        return value === fieldToMatch.value;
    }
    
    submitForm() {
        // Handle form submission
        const formData = new FormData(this.form);
        
        fetch(this.form.action, {
            method: this.form.method,
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                // Handle success
            } else {
                // Handle errors
            }
        });
    }
}

// Initialize validators on all forms
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form').forEach(form => {
        new FormValidator(form);
    });
});