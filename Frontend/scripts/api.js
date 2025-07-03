// scripts/api.js
class API {
    constructor() {
        this.baseUrl = '/api/';
        this.headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        };
    }
    
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`);
        Object.keys(params).forEach(key => 
            url.searchParams.append(key, params[key])
        );
        
        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });
        
        return this.handleResponse(response);
    }
    
    async post(endpoint, data = {}) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return this.handleResponse(response);
    }
    
    async put(endpoint, data = {}) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'PUT',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return this.handleResponse(response);
    }
    
    async delete(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'DELETE',
            headers: this.headers
        });
        
        return this.handleResponse(response);
    }
    
    async handleResponse(response) {
        if(response.ok) {
            return response.json();
        } else {
            const error = await response.json();
            throw new Error(error.message || 'API request failed');
        }
    }
    
    // Specific API methods for our application
    async getDashboardData() {
        return this.get('dashboard/');
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}upload/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        return this.handleResponse(response);
    }
    
    async getAnalyticsData(params) {
        return this.get('analytics/', params);
    }
    
    async generateReport(reportType, params) {
        return this.post(`reports/${reportType}/`, params);
    }
}

// Initialize API instance
const api = new API();

// Helper function to get CSRF token
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