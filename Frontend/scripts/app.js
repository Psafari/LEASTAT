// scripts/app.js
document.addEventListener('DOMContentLoaded', function() {
    // Handle section switching
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active nav link
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding section
            const sectionId = `${this.dataset.section}-section`;
            sections.forEach(section => {
                section.classList.remove('active');
                if(section.id === sectionId) {
                    section.classList.add('active');
                }
            });
            
            // Load section-specific JS if needed
            loadSectionScript(this.dataset.section);
        });
    });
    
    // Handle logout
    const logoutBtn = document.querySelector('.logout-btn');
    if(logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // Call API to logout
            fetch('/api/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if(response.ok) {
                    window.location.href = '/login/';
                }
            });
        });
    }
    
    // Initialize file upload functionality if on upload page
    if(document.getElementById('upload-section').classList.contains('active')) {
        initFileUpload();
    }
});

function loadSectionScript(section) {
    // Dynamically load section-specific JS
    const scriptMap = {
        'dashboard': 'dashboard.js',
        'upload': 'upload.js',
        'analytics': 'analytics.js',
        'reports': 'reports.js'
    };
    
    if(scriptMap[section]) {
        const script = document.createElement('script');
        script.src = `scripts/${scriptMap[section]}`;
        document.body.appendChild(script);
    }
}

function getCookie(name) {
    // Helper function for CSRF token
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