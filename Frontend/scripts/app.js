// scripts/app.js - Enhanced version
document.addEventListener('DOMContentLoaded', function() {
    console.log('LEASTAT Dashboard loaded');
    
    // Handle logout button
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            console.log('Logout clicked');
            window.location.href = '/logout'; // Example logout endpoint
        });
    }
    
    // Initialize navigation
    initializeNavigation();
});

function initializeNavigation() {
    // Set active navigation based on current page
    setActiveNavigation();
    
    // Load section-specific scripts
    loadCurrentSectionScript();
    
    // Setup navigation event listeners
    setupNavigationLinks();
}

function setActiveNavigation() {
    const currentPage = getCurrentPage();
    const currentSection = getSectionForPage(currentPage);
    
    // Update active states
    updateActiveNavLink(currentSection);
    updateActiveContentSection(currentSection);
}

function getCurrentPage() {
    return window.location.pathname.split('/').pop() || 'index.html';
}

function getSectionForPage(page) {
    const pageMap = {
        'index.html': 'dashboard',
        '': 'dashboard',
        'upload.html': 'upload',
        'analytics.html': 'analytics',
        'reports.html': 'reports'
    };
    return pageMap[page] || 'dashboard';
}

function updateActiveNavLink(section) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));
    
    const activeLink = document.querySelector(`.nav-link[data-section="${section}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function updateActiveContentSection(section) {
    const contentSections = document.querySelectorAll('.content-section');
    contentSections.forEach(section => section.classList.remove('active'));
    
    const activeSection = document.getElementById(`${section}-section`);
    if (activeSection) {
        activeSection.classList.add('active');
    }
}

function setupNavigationLinks() {
    const navLinks = document.querySelectorAll('.nav-link:not([href^="http"])');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Prevent default only for same-domain links
            if (!this.href || this.href.startsWith(window.location.origin)) {
                e.preventDefault();
                
                // Update active states immediately for better UX
                const section = this.getAttribute('data-section');
                updateActiveNavLink(section);
                updateActiveContentSection(section);
                
                // Navigate after a small delay to allow UI update
                setTimeout(() => {
                    window.location.href = this.getAttribute('href');
                }, 100);
            }
        });
    });
}

function loadCurrentSectionScript() {
    const currentPage = getCurrentPage();
    const currentSection = getSectionForPage(currentPage);
    loadSectionScript(currentSection);
}

function loadSectionScript(section) {
    const scriptMap = {
        'dashboard': 'dashboard.js',
        'upload': 'upload.js',
        
        'reports': 'reports.js'
    };
    
    if (scriptMap[section] && !isScriptLoaded(scriptMap[section])) {
        loadScript(`scripts/${scriptMap[section]}`);
    }
}

function isScriptLoaded(scriptName) {
    return !!document.querySelector(`script[src*="${scriptName}"]`);
}

function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
        document.body.appendChild(script);
    }).catch(error => {
        console.error(error);
    });
}

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