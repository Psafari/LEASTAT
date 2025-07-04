// scripts/reports.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Reports section loaded');
    
    // Handle report generation buttons
    const generateButtons = document.querySelectorAll('.generate-btn');
    generateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reportType = this.closest('.template-card').querySelector('h4').textContent;
            console.log(`Generating report: ${reportType}`);
            // Add actual report generation logic here
        });
    });
    
    // Handle report download/view buttons
    const reportActions = document.querySelectorAll('.download-btn, .view-btn');
    reportActions.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.classList.contains('download-btn') ? 'Download' : 'View';
            const reportName = this.closest('.report-item').querySelector('h4').textContent;
            console.log(`${action}ing report: ${reportName}`);
            // Add actual download/view logic here
        });
    });
});