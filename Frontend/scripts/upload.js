// Upload.js - Enhanced Automated File Processing for LEASTAT Platform
// Handles file uploads and processing pipeline with improved error handling and PDF support

class FileUploadManager {
    constructor() {
        // Configuration - Updated to include PDF support
        this.API_BASE_URL = this.getApiBaseUrl();
        this.allowedExtensions = ['.xlsx', '.xls', '.csv', '.pdf']; // Added PDF support
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        
        // State management
        this.fileQueue = [];
        this.processingQueue = [];
        
        // Initialize
        this.initializeElements();
        this.setupEventListeners();
        this.validateFormAndEnableUpload();
        
        // Check API connection on startup
        this.initializeApiConnection();
    }

    getApiBaseUrl() {
        // Detect API base URL based on current environment
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `${protocol}//127.0.0.1:8000`;
        } else {
            // Production API URL - adjust as needed
            return `${protocol}//${hostname}/api`;
        }
    }

    initializeElements() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('file-input');
        this.chooseFileBtn = document.getElementById('chooseFileBtn');
        this.dataDateInput = document.getElementById('dataDate');
        this.revenueTypeSelect = document.querySelector('[name="revenue_type"]');
        this.validationMessage = document.getElementById('validationMessage');
        this.uploadProgress = document.getElementById('upload-progress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.filesList = document.getElementById('filesList');
        this.uploadForm = document.getElementById('uploadForm');
    }

    setupEventListeners() {
        // Enable upload area when date is selected
        this.dataDateInput?.addEventListener('change', () => {
            this.validateFormAndEnableUpload();
        });

        // File input change event
        this.fileInput?.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                this.handleFileSelection(e.target.files);
            }
        });

        // Choose file button click
        this.chooseFileBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            if (!this.chooseFileBtn.disabled) {
                this.fileInput?.click();
            }
        });

        // Drag and drop functionality
        if (this.uploadArea) {
            this.uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!this.uploadArea.classList.contains('disabled')) {
                    this.uploadArea.classList.add('drag-over');
                }
            });

            this.uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.uploadArea.classList.remove('drag-over');
            });

            this.uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.uploadArea.classList.remove('drag-over');
                
                if (!this.uploadArea.classList.contains('disabled') && e.dataTransfer.files.length > 0) {
                    this.handleFileSelection(e.dataTransfer.files);
                }
            });
        }

        // Form submission prevention
        this.uploadForm?.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }

    validateFormAndEnableUpload() {
        const dateValue = this.dataDateInput?.value;
        
        if (dateValue) {
            this.uploadArea?.classList.remove('disabled');
            if (this.fileInput) this.fileInput.disabled = false;
            if (this.chooseFileBtn) this.chooseFileBtn.disabled = false;
            if (this.validationMessage) this.validationMessage.style.display = 'none';
            
            // Update upload area text to include PDF support
            const infoText = this.uploadArea?.querySelector('p:last-child small');
            if (infoText) {
                infoText.textContent = 'Supported formats: Excel (.xlsx, .xls), CSV (.csv), PDF (.pdf)';
            }
        } else {
            this.uploadArea?.classList.add('disabled');
            if (this.fileInput) this.fileInput.disabled = true;
            if (this.chooseFileBtn) this.chooseFileBtn.disabled = true;
            if (this.validationMessage) this.validationMessage.style.display = 'block';
        }
    }

    handleFileSelection(files) {
        const validFiles = [];
        const errors = [];

        Array.from(files).forEach(file => {
            const validation = this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                errors.push(`${file.name}: ${validation.error}`);
            }
        });

        if (errors.length > 0) {
            this.showValidationErrors(errors);
        }

        if (validFiles.length > 0) {
            this.queueFilesForProcessing(validFiles);
        }
    }

    validateFile(file) {
        console.log(`Validating file: ${file.name}, size: ${file.size} bytes, type: ${file.type}`);
        
        // Check file extension
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.allowedExtensions.includes(fileExtension)) {
            return {
                valid: false,
                error: `Unsupported file type. Only ${this.allowedExtensions.join(', ')} files are allowed.`
            };
        }

        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                error: `File too large. Maximum size is ${this.maxFileSize / (1024 * 1024)}MB.`
            };
        }

        // Check if file is not empty
        if (file.size === 0) {
            return {
                valid: false,
                error: 'File is empty.'
            };
        }

        // Additional validation for PDF files
        if (fileExtension === '.pdf') {
            // Basic MIME type check for PDF
            if (file.type && !file.type.includes('pdf')) {
                console.warn(`PDF file has unexpected MIME type: ${file.type}`);
                // Don't fail validation, just warn - some systems may not set MIME type correctly
            }
        }

        return { valid: true };
    }

    async queueFilesForProcessing(files) {
        const dataDate = this.dataDateInput?.value;
        const revenueType = this.revenueTypeSelect?.value || null;
        
        console.log(`Queueing ${files.length} files for processing. Date: ${dataDate}, Revenue Type: ${revenueType}`);
        
        files.forEach(file => {
            const fileMetadata = {
                id: this.generateFileId(),
                file: file,
                filename: file.name,
                dataDate: dataDate,
                revenueType: revenueType,
                status: 'queued',
                progress: 0
            };
            
            this.fileQueue.push(fileMetadata);
            this.addFileToUI(fileMetadata);
        });

        this.processFileQueue();
    }

    generateFileId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async processFileQueue() {
        if (this.processingQueue.length > 0) {
            console.log('Already processing files, waiting...');
            return; // Already processing
        }

        while (this.fileQueue.length > 0) {
            const fileMetadata = this.fileQueue.shift();
            this.processingQueue.push(fileMetadata);
            
            try {
                await this.processFile(fileMetadata);
            } catch (error) {
                console.error('Error processing file:', error);
                this.updateFileStatus(fileMetadata.id, 'error', error.message);
            } finally {
                // Remove from processing queue
                this.processingQueue = this.processingQueue.filter(f => f.id !== fileMetadata.id);
            }
        }
    }

    async processFile(fileMetadata) {
        console.log(`Processing file: ${fileMetadata.filename} (${fileMetadata.file.type})`);
        
        try {
            this.updateFileStatus(fileMetadata.id, 'uploading', 'Preparing upload...');
            this.showUploadProgress(true);
            this.updateProgress(10);
            
            // Validate required fields
            if (!fileMetadata.dataDate) {
                throw new Error('Data date is required');
            }
            
            // Check if revenue type is needed based on filename
            const filename = fileMetadata.filename.toLowerCase();
            if (filename.includes('revenue') && !fileMetadata.revenueType) {
                throw new Error('Revenue type is required for revenue files');
            }
            
            const formData = new FormData();
            formData.append('file', fileMetadata.file);
            formData.append('Data Date', fileMetadata.dataDate);
            
            if (fileMetadata.revenueType) {
                formData.append('Revenue Type', fileMetadata.revenueType);
            }
            
            // Debug: Log what we're sending
            console.log('FormData prepared:', {
                filename: fileMetadata.filename,
                dataDate: fileMetadata.dataDate,
                revenueType: fileMetadata.revenueType,
                fileSize: fileMetadata.file.size,
                fileType: fileMetadata.file.type,
                fileExtension: '.' + fileMetadata.filename.split('.').pop().toLowerCase()
            });
            
            // Debug: Log all FormData entries
            console.log('FormData entries:');
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}:`, value instanceof File ? `File(${value.name}, ${value.size} bytes, ${value.type})` : value);
            }

            this.updateProgress(30);
            this.updateFileStatus(fileMetadata.id, 'uploading', 'Uploading file...');
            
            // Adjust timeout for PDF files (they might be larger and take longer to process)
            const isPdf = fileMetadata.filename.toLowerCase().endsWith('.pdf');
            const timeoutDuration = isPdf ? 600000 : 300000; // 10 minutes for PDF, 5 for others
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
            
            const response = await fetch(`${this.API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
                signal: controller.signal
                // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
            });
            
            clearTimeout(timeoutId);

            this.updateProgress(70);
            this.updateFileStatus(fileMetadata.id, 'processing', isPdf ? 'Extracting data from PDF...' : 'Processing data...');
            
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                let errorMessage = 'Upload failed';
                let errorDetails = null;
                
                try {
                    // Clone the response to read it multiple times if needed
                    const responseClone = response.clone();
                    const contentType = response.headers.get('content-type');
                    
                    console.log('Error response status:', response.status);
                    console.log('Error response headers:', Object.fromEntries(response.headers.entries()));
                    
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        console.error('Full API Error Response:', errorData);
                        
                        // Handle FastAPI validation errors
                        if (errorData.detail) {
                            if (Array.isArray(errorData.detail)) {
                                // Validation errors format
                                errorMessage = errorData.detail.map(err => 
                                    `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`
                                ).join('; ');
                            } else if (typeof errorData.detail === 'string') {
                                errorMessage = errorData.detail;
                            } else {
                                errorMessage = JSON.stringify(errorData.detail);
                            }
                        } else {
                            errorMessage = errorData.message || JSON.stringify(errorData);
                        }
                        errorDetails = errorData;
                    } else {
                        const textResponse = await responseClone.text();
                        console.error('Non-JSON Error Response:', textResponse);
                        errorMessage = textResponse || `HTTP ${response.status}: ${response.statusText}`;
                    }
                } catch (parseError) {
                    console.error('Error parsing error response:', parseError);
                    // Try to get the raw response as text
                    try {
                        const rawText = await response.text();
                        console.error('Raw error response:', rawText);
                        errorMessage = rawText || `HTTP ${response.status}: ${response.statusText}`;
                    } catch (textError) {
                        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    }
                }
                
                console.error('Final error message:', errorMessage);
                throw new Error(errorMessage);
            }

            const result = await response.json();
            console.log('Upload successful:', result);
            
            this.updateProgress(100);
            this.updateFileStatus(fileMetadata.id, 'processed', 
                result.message || 'File processed successfully');
            
            // Show success notification with additional info for PDF files
            const successMessage = result.message || 'File processed successfully';
            const detailedMessage = isPdf ? 
                `${successMessage} (PDF tables extracted and processed)` : 
                successMessage;
            
            this.showSuccessNotification(fileMetadata.filename, detailedMessage);
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('Upload timeout:', error);
                const isPdf = fileMetadata.filename.toLowerCase().endsWith('.pdf');
                const timeoutMessage = isPdf ? 
                    'PDF processing timeout - file may be too complex or large' : 
                    'Upload timeout - file too large or slow connection';
                this.updateFileStatus(fileMetadata.id, 'error', timeoutMessage);
                this.showErrorNotification(fileMetadata.filename, timeoutMessage);
            } else {
                console.error('Upload error:', error);
                this.updateFileStatus(fileMetadata.id, 'error', error.message);
                this.showErrorNotification(fileMetadata.filename, error.message);
            }
            throw error;
        } finally {
            setTimeout(() => {
                this.showUploadProgress(false);
            }, 1000);
        }
    }

    addFileToUI(fileMetadata) {
        if (!this.filesList) return;

        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.id = `file-${fileMetadata.id}`;
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fa-solid ${this.getFileIcon(fileMetadata.filename)}"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${fileMetadata.filename}</div>
                    <div class="file-meta">Date: ${fileMetadata.dataDate}${fileMetadata.revenueType ? ' • Type: ' + fileMetadata.revenueType : ''}</div>
                </div>
            </div>
            <div class="file-status queued">
                <i class="fa-solid fa-clock"></i>
                <span class="status-text">Queued</span>
            </div>
        `;

        // Insert at the top of the list
        this.filesList.insertBefore(fileItem, this.filesList.firstChild);
    }

    getFileIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        switch (extension) {
            case 'xlsx':
            case 'xls':
                return 'fa-file-excel';
            case 'csv':
                return 'fa-file-csv';
            case 'pdf':
                return 'fa-file-pdf'; // Added PDF icon
            default:
                return 'fa-file';
        }
    }

    updateFileStatus(fileId, status, message) {
        const fileItem = document.getElementById(`file-${fileId}`);
        if (!fileItem) return;

        const statusElement = fileItem.querySelector('.file-status');
        const statusText = statusElement?.querySelector('.status-text');
        const statusIcon = statusElement?.querySelector('i');

        if (!statusElement || !statusText || !statusIcon) return;

        statusElement.className = `file-status ${status}`;
        statusText.textContent = message;

        const iconMap = {
            'queued': 'fa-clock',
            'uploading': 'fa-cloud-arrow-up',
            'processing': 'fa-spinner fa-spin',
            'processed': 'fa-check-circle',
            'error': 'fa-exclamation-triangle'
        };

        statusIcon.className = `fa-solid ${iconMap[status] || 'fa-question-circle'}`;
    }

    showUploadProgress(show) {
        if (this.uploadProgress) {
            this.uploadProgress.style.display = show ? 'block' : 'none';
            if (!show) {
                this.updateProgress(0);
            }
        }
    }

    updateProgress(percentage) {
        if (this.progressFill && this.progressText) {
            this.progressFill.style.width = `${percentage}%`;
            this.progressText.textContent = `${percentage}% Complete`;
        }
    }

    showValidationErrors(errors) {
        if (!this.validationMessage) return;

        const errorContainer = document.createElement('div');
        errorContainer.className = 'validation-errors';
        errorContainer.innerHTML = `
            <h4>Upload Errors:</h4>
            <ul>${errors.map(error => `<li>${error}</li>`).join('')}</ul>
        `;

        this.validationMessage.innerHTML = '';
        this.validationMessage.appendChild(errorContainer);
        this.validationMessage.style.display = 'block';

        setTimeout(() => {
            this.validationMessage.style.display = 'none';
        }, 8000);
    }

    showSuccessNotification(filename, message) {
        this.showNotification('success', `✅ ${filename}`, message);
    }

    showErrorNotification(filename, message) {
        this.showNotification('error', `❌ ${filename}`, message);
    }

    showNotification(type, title, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add to page
        let notificationContainer = document.getElementById('notifications');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notifications';
            notificationContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                max-width: 400px;
            `;
            document.body.appendChild(notificationContainer);
        }

        notificationContainer.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // API health check
    async checkApiHealth() {
        try {
            console.log(`Checking API health at: ${this.API_BASE_URL}`);
            const response = await fetch(`${this.API_BASE_URL}/health`, {
                method: 'GET',
                timeout: 10000
            });
            console.log(`API health check response: ${response.status}`);
            return response.ok;
        } catch (error) {
            console.warn('API health check failed:', error);
            return false;
        }
    }

    // Initialize API connection check
    async initializeApiConnection() {
        console.log('Initializing API connection check...');
        const isHealthy = await this.checkApiHealth();
        if (!isHealthy) {
            this.showNotification('error', 'API Connection', 
                `Cannot connect to API at ${this.API_BASE_URL}. Please check if the backend server is running.`);
        } else {
            console.log('API connection successful');
        }
    }

    // Debug method to check form values
    debugFormValues() {
        console.log('Current form values:', {
            dataDate: this.dataDateInput?.value,
            revenueType: this.revenueTypeSelect?.value,
            apiBaseUrl: this.API_BASE_URL,
            allowedExtensions: this.allowedExtensions
        });
    }
}

// Add notification styles to the page
const notificationStyles = `
<style>
.notification {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-bottom: 10px;
    padding: 16px;
    border-left: 4px solid;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    animation: slideIn 0.3s ease-out;
}

.notification-success {
    border-left-color: #22c55e;
}

.notification-error {
    border-left-color: #ef4444;
}

.notification-content {
    flex: 1;
}

.notification-title {
    font-weight: 600;
    margin-bottom: 4px;
}

.notification-message {
    font-size: 14px;
    color: #666;
    word-break: break-word;
}

.notification-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #999;
    padding: 0;
    margin-left: 10px;
    min-width: 20px;
}

.notification-close:hover {
    color: #333;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.validation-errors {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    padding: 12px;
    color: #dc2626;
}

.validation-errors h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    font-weight: 600;
}

.validation-errors ul {
    margin: 0;
    padding-left: 20px;
}

.validation-errors li {
    margin-bottom: 4px;
    font-size: 13px;
}
</style>
`;

// Initialize the upload manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing FileUploadManager...');
    
    // Add notification styles
    document.head.insertAdjacentHTML('beforeend', notificationStyles);
    
    // Initialize upload manager
    window.fileUploadManager = new FileUploadManager();
    
    // Add debug helper to window for troubleshooting
    window.debugUpload = () => {
        if (window.fileUploadManager) {
            window.fileUploadManager.debugFormValues();
            console.log('File queue:', window.fileUploadManager.fileQueue);
            console.log('Processing queue:', window.fileUploadManager.processingQueue);
        }
    };
    
    console.log('FileUploadManager initialized successfully');
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FileUploadManager;
}