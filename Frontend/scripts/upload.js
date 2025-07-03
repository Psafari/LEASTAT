
// File type mappings
const fileTypeMappings = {
    'little-hotelier': [
        'Leaside Revenue Summary',
        'Apartments Revenue Summary',
        'Monastery Suites Revenue Summary',
        'Leaside Extras',
        'Monastery Suites Extras'
    ],
    'jane': [
        'Monastery Health Sales',
        'Riverside Therapeutics Sales',
        'Villanova Sales'
    ],
    'booker': [
        'Service Sales',
        'Product Sales'
    ]
};

// DOM elements
const managementSoftwareSelect = document.getElementById('managementSoftware');
const fileTypeSelect = document.getElementById('fileType');
const dataDateInput = document.getElementById('dataDate');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('file-input');
const chooseFileBtn = document.getElementById('chooseFileBtn');
const validationMessage = document.getElementById('validationMessage');
const uploadProgress = document.getElementById('upload-progress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const filesList = document.getElementById('filesList');

// Update file type options based on management software selection
managementSoftwareSelect.addEventListener('change', function() {
    const selectedSoftware = this.value;
    fileTypeSelect.innerHTML = '<option value="">Select File Type</option>';
    
    if (selectedSoftware && fileTypeMappings[selectedSoftware]) {
        fileTypeSelect.disabled = false;
        fileTypeMappings[selectedSoftware].forEach(fileType => {
            const option = document.createElement('option');
            option.value = fileType.toLowerCase().replace(/\s+/g, '-');
            option.textContent = fileType;
            fileTypeSelect.appendChild(option);
        });
    } else {
        fileTypeSelect.disabled = true;
    }
    
    validateForm();
});

// Validate form and enable/disable upload area
function validateForm() {
    const isValid = managementSoftwareSelect.value && 
                    fileTypeSelect.value && 
                    dataDateInput.value;
    
    if (isValid) {
        uploadArea.classList.remove('disabled');
        fileInput.disabled = false;
        chooseFileBtn.disabled = false;
        uploadArea.querySelector('p small').textContent = 'Supported formats: Excel (.xlsx, .xls) and CSV (.csv)';
        validationMessage.style.display = 'none';
    } else {
        uploadArea.classList.add('disabled');
        fileInput.disabled = true;
        chooseFileBtn.disabled = true;
        uploadArea.querySelector('p small').textContent = 'Complete the form above to enable file upload';
    }
}

// Add event listeners for form validation
fileTypeSelect.addEventListener('change', validateForm);
dataDateInput.addEventListener('change', validateForm);

// File upload functionality
chooseFileBtn.addEventListener('click', function() {
    if (!chooseFileBtn.disabled) {
        fileInput.click();
    }
});

uploadArea.addEventListener('click', function() {
    if (!uploadArea.classList.contains('disabled')) {
        fileInput.click();
    }
});

// Drag and drop functionality
uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    if (!uploadArea.classList.contains('disabled')) {
        uploadArea.classList.add('dragover');
    }
});

uploadArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    if (!uploadArea.classList.contains('disabled')) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }
});

fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// Handle file upload
function handleFileUpload(file) {
    // Validate file type
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        alert('Please upload only Excel (.xlsx, .xls) or CSV (.csv) files.');
        return;
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
        alert('File size must be less than 50MB.');
        return;
    }

    // Show validation error if form is not complete
    if (!managementSoftwareSelect.value || !fileTypeSelect.value || !dataDateInput.value) {
        validationMessage.style.display = 'block';
        return;
    }

    // Start upload process
    uploadFile(file);
}

// Simulate file upload process
function uploadFile(file) {
    uploadProgress.style.display = 'block';
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // Complete upload
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                addFileToList(file);
                resetForm();
            }, 500);
        }
        
        progressFill.style.width = progress + '%';
        progressText.textContent = Math.round(progress) + '% Complete';
    }, 200);
}

// Add uploaded file to the list
function addFileToList(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    
    const managementSoftwareText = managementSoftwareSelect.options[managementSoftwareSelect.selectedIndex].text;
    const fileTypeText = fileTypeSelect.options[fileTypeSelect.selectedIndex].text;
    const formattedDate = new Date(dataDateInput.value).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
    
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const iconClass = fileExtension === 'csv' ? 'fa-file-csv' : 'fa-file-excel';
    
    fileItem.innerHTML = `
        <div class="file-info">
            <div class="file-icon"><i class="fa-solid ${iconClass}"></i></div>
            <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">${managementSoftwareText} • ${fileTypeText} • ${formattedDate}</div>
            </div>
        </div>
        <div class="file-status processing">
            <i class="fa-solid fa-clock"></i>
            Processing
        </div>
    `;
    
    filesList.insertBefore(fileItem, filesList.firstChild);
    
    // Simulate processing completion
    setTimeout(() => {
        const statusElement = fileItem.querySelector('.file-status');
        statusElement.className = 'file-status success';
        statusElement.innerHTML = `
            <i class="fa-solid fa-check-circle"></i>
            Processed
        `;
    }, 3000);
}

// Reset form after successful upload
function resetForm() {
    managementSoftwareSelect.value = '';
    fileTypeSelect.value = '';
    fileTypeSelect.disabled = true;
    fileTypeSelect.innerHTML = '<option value="">Select File Type</option>';
    dataDateInput.value = '';
    fileInput.value = '';
    
    uploadArea.classList.add('disabled');
    fileInput.disabled = true;
    chooseFileBtn.disabled = true;
    uploadArea.querySelector('p small').textContent = 'Complete the form above to enable file upload';
}

// Navigation functionality (basic)
const navLinks = document.querySelectorAll('.nav-link');
navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        navLinks.forEach(l => l.classList.remove('active'));
        this.classList.add('active');
    });
});

// Set max date to today
const today = new Date().toISOString().split('T')[0];
dataDateInput.setAttribute('max', today);
