// scripts/upload.js
function initFileUpload() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('file-input');
    const progressSection = document.getElementById('upload-progress');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    const filesList = document.querySelector('.files-list');
    
    // Handle drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if(e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFiles(fileInput.files);
        }
    });
    
    // Handle file selection
    fileInput.addEventListener('change', () => {
        if(fileInput.files.length) {
            handleFiles(fileInput.files);
        }
    });
    
    function handleFiles(files) {
        progressSection.style.display = 'block';
        let progress = 0;
        const totalFiles = files.length;
        
        // Process each file
        Array.from(files).forEach((file, index) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('subsidiary_id', 'current_subsidiary'); // Should be dynamic
            
            fetch('/api/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    addFileToList(file, data.file_id);
                }
                
                // Update progress
                progress = ((index + 1) / totalFiles) * 100;
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${Math.round(progress)}% Complete`;
                
                if(index === totalFiles - 1) {
                    setTimeout(() => {
                        progressSection.style.display = 'none';
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    function addFileToList(file, fileId) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileSize = (file.size / (1024 * 1024)).toFixed(2); // MB
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">${getFileIcon(file.name)}</div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${fileSize} MB</div>
                </div>
            </div>
            <button class="file-remove" data-file-id="${fileId}">×</button>
        `;
        
        filesList.appendChild(fileItem);
    }
    
    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if(['xlsx', 'xls'].includes(ext)) return '📊';
        if(ext === 'csv') return '📝';
        return '📄';
    }
}