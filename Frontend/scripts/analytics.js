// scripts/analytics.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Analytics section loaded');
    
    // Initialize chart elements
    const revenueChartEl = document.getElementById('revenue-chart');
    const occupancyAdrChartEl = document.getElementById('occupancy-adr-chart');
    const compositionChartEl = document.getElementById('composition-chart');
    const servicesChartEl = document.getElementById('services-chart');
    
    // Initialize charts with Chart.js
    const revenueChart = new Chart(revenueChartEl, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: createChartOptions('Revenue Trends', '$')
    });
    
    const occupancyAdrChart = new Chart(occupancyAdrChartEl, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: createChartOptions('Occupancy & ADR', '', true)
    });
    
    const compositionChart = new Chart(compositionChartEl, {
        type: 'pie',
        data: { labels: [], datasets: [] },
        options: createChartOptions('Revenue Composition', '$')
    });
    
    const servicesChart = new Chart(servicesChartEl, {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: createChartOptions('Service Revenue', '$')
    });

    // Initialize target card functionality
    const dashboard = new AnalyticsDashboard();
    dashboard.startAutoRefresh(5); // Refresh every 5 minutes
    
    // Filter event listeners
    document.getElementById('date-range').addEventListener('change', function() {
        const customRange = document.getElementById('custom-date-range');
        customRange.style.display = this.value === 'custom' ? 'block' : 'none';
    });
    
    document.getElementById('apply-filters').addEventListener('click', function() {
        loadAnalyticsData();
    });
    
    // Initial data load
    loadAnalyticsData();
    
    // Analytics Dashboard Class for target cards
    class AnalyticsDashboard {
        constructor() {
            this.setupCardFilters();
        }

        setupCardFilters() {
            const cards = ['accommodations', 'health', 'restaurants', 'total'];
            cards.forEach(card => {
                document.getElementById(`${card}-month`).addEventListener('change', async () => {
                    await this.updateCardData(card);
                });
                document.getElementById(`${card}-year`).addEventListener('change', async () => {
                    await this.updateCardData(card);
                });
            });
        }

        async updateCardData(cardType) {
            try {
                const monthSelect = document.getElementById(`${cardType}-month`);
                const yearSelect = document.getElementById(`${cardType}-year`);
                
                // Skip if month or year not selected
                if (!monthSelect.value || !yearSelect.value) return;
                
                const month = monthSelect.options[monthSelect.selectedIndex].text;
                const year = parseInt(yearSelect.value);
                
                let endpoint;
                
                // Determine which endpoint to call based on card type
                switch(cardType) {
                    case 'accommodations':
                        endpoint = '/api/analysis/accomodations';
                        break;
                    case 'health':
                        endpoint = '/api/analysis/health';
                        break;
                    case 'restaurants':
                        endpoint = '/api/analysis/restaurants';
                        break;
                    case 'total':
                        endpoint = '/api/analysis/total';
                        break;
                    default:
                        return;
                }
                
                const response = await fetch(`${endpoint}?select_month=${encodeURIComponent(month)}&select_year=${year}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    }
                });

                if (!response.ok) throw new Error('Failed to fetch card data');
                
                const data = await response.json();
                
                // Update the UI
                const currentEl = document.getElementById(`${cardType}-current`);
                const targetEl = document.getElementById(`${cardType}-target`);
                const progressEl = document.getElementById(`${cardType}-progress`);
                
                if (currentEl) currentEl.textContent = `$${data.Current.toLocaleString()}`;
                if (targetEl) targetEl.textContent = `$${data.Target.toLocaleString()}`;
                
                if (progressEl) {
                    const percentage = data.Target > 0 ? Math.min((data.Current / data.Target) * 100, 100) : 0;
                    progressEl.style.width = `${percentage}%`;
                }
                
            } catch (error) {
                console.error(`Error updating ${cardType} card data:`, error);
                this.showError(`Failed to update ${cardType} data`);
            }
        }

        getAuthToken() {
            // Get authentication token from localStorage or sessionStorage
            return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        }

        showError(message) {
            // Create error notification
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-notification';
            errorDiv.innerHTML = `
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ef4444;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    max-width: 400px;
                ">
                    <i class="fas fa-exclamation-triangle"></i>
                    ${message}
                    <button onclick="this.parentElement.remove()" style="
                        background: none;
                        border: none;
                        color: white;
                        float: right;
                        font-size: 1.2rem;
                        cursor: pointer;
                        margin-left: 10px;
                    ">×</button>
                </div>
            `;
            document.body.appendChild(errorDiv);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (errorDiv.parentElement) {
                    errorDiv.remove();
                }
            }, 5000);
        }

        // Refresh data periodically
        startAutoRefresh(intervalMinutes = 5) {
            setInterval(() => {
                this.setupCardFilters(); // Refresh all card data
            }, intervalMinutes * 60 * 1000);
        }
    }
    
    function loadAnalyticsData() {
        // Get filter values
        const dateRange = document.getElementById('date-range').value;
        const property = document.getElementById('property').value;
        const metric = document.getElementById('metric').value;
        const breakdown = document.getElementById('breakdown').value;
        
        // Show loading state
        document.querySelectorAll('.chart-container').forEach(el => {
            el.classList.add('loading');
        });
        
        // Simulate API call (in a real app, this would be fetch/axios)
        setTimeout(() => {
            // Generate mock data based on filters
            const data = generateMockData(dateRange, property, metric, breakdown);
            
            // Update charts
            updateRevenueChart(data);
            updateOccupancyAdrChart(data);
            updateCompositionChart(data);
            updateServicesChart(data);
            
            // Update summary metrics
            updateSummaryMetrics(data);
            
            // Remove loading state
            document.querySelectorAll('.chart-container').forEach(el => {
                el.classList.remove('loading');
            });
        }, 1000);
    }
    
    function updateRevenueChart(data) {
        revenueChart.data.labels = data.dates;
        revenueChart.data.datasets = [{
            label: 'Revenue',
            data: data.revenue,
            borderColor: '#21273d',
            backgroundColor: 'rgba(33, 39, 61, 0.1)',
            tension: 0.1,
            fill: true
        }];
        revenueChart.update();
    }
    
    function updateOccupancyAdrChart(data) {
        occupancyAdrChart.data.labels = data.dates;
        occupancyAdrChart.data.datasets = [
            {
                label: 'Occupancy %',
                data: data.occupancy,
                backgroundColor: '#b9d4f1',
                yAxisID: 'y'
            },
            {
                label: 'ADR',
                data: data.adr,
                backgroundColor: '#10b981',
                yAxisID: 'y1',
                type: 'line'
            }
        ];
        occupancyAdrChart.update();
    }
    
    function updateCompositionChart(data) {
        compositionChart.data.labels = ['Room', 'Extras', 'Taxes', 'Services'];
        compositionChart.data.datasets = [{
            data: [data.roomRevenue, data.extrasRevenue, data.taxes, data.serviceRevenue],
            backgroundColor: ['#21273d', '#b9d4f1', '#10b981', '#f59e0b']
        }];
        compositionChart.update();
    }
    
    function updateServicesChart(data) {
        servicesChart.data.labels = data.topServices.map(s => s.name);
        servicesChart.data.datasets = [{
            data: data.topServices.map(s => s.revenue),
            backgroundColor: ['#21273d', '#b9d4f1', '#10b981', '#f59e0b', '#ef4444']
        }];
        servicesChart.update();
    }
    
    function updateSummaryMetrics(data) {
        document.getElementById('total-revenue').textContent = `$${data.totalRevenue.toLocaleString()}`;
        document.getElementById('avg-daily-revenue').textContent = `$${data.avgDailyRevenue.toLocaleString()}`;
        document.getElementById('avg-occupancy').textContent = `${data.avgOccupancy}%`;
        document.getElementById('avg-adr').textContent = `$${data.avgAdr.toLocaleString()}`;
        document.getElementById('room-revenue').textContent = `$${data.roomRevenue.toLocaleString()}`;
        document.getElementById('extras-revenue').textContent = `$${data.extrasRevenue.toLocaleString()}`;
        document.getElementById('top-service').textContent = data.topServices[0]?.name || '-';
        document.getElementById('top-service-revenue').textContent = `$${data.topServices[0]?.revenue.toLocaleString() || '0.00'}`;
    }
    
    function generateMockData(dateRange, property, metric, breakdown) {
        // This would be replaced with actual data processing from the uploaded files
        // For now, we'll generate mock data that simulates what we'd get from the real data
        
        const days = dateRange === 'custom' ? 30 : parseInt(dateRange); // Simplified for demo
        const dates = [];
        const revenue = [];
        const occupancy = [];
        const adr = [];
        
        for (let i = 0; i < days; i++) {
            dates.push(new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toLocaleDateString());
            revenue.push(Math.round(5000 + Math.random() * 15000));
            occupancy.push(Math.round(60 + Math.random() * 40));
            adr.push(Math.round(150 + Math.random() * 100));
        }
        
        // Based on the actual data files we saw, we can model some realistic values
        const roomRevenue = 3400.70 + 4924.75 + 7189.58; // From revenue_summary files
        const extrasRevenue = 60 + 873.26 + 8347.33; // From extras and service sales
        const taxes = 602.49 + 517.06 + 1375.02;
        const serviceRevenue = 907.5; // From product sales
        
        // Top services from the service sales data
        const topServices = [
            { name: 'Massages', revenue: 2745 },
            { name: 'Manicure/Pedicure', revenue: 2645 },
            { name: 'Medical Spa', revenue: 1117.33 },
            { name: 'Facials', revenue: 430 },
            { name: 'Skin Care', revenue: 260 }
        ];
        
        return {
            dates,
            revenue,
            occupancy,
            adr,
            roomRevenue,
            extrasRevenue,
            taxes,
            serviceRevenue,
            totalRevenue: revenue.reduce((a, b) => a + b, 0),
            avgDailyRevenue: Math.round(revenue.reduce((a, b) => a + b, 0) / days),
            avgOccupancy: Math.round(occupancy.reduce((a, b) => a + b, 0) / days),
            avgAdr: Math.round(adr.reduce((a, b) => a + b, 0) / days),
            topServices
        };
    }
    
    function createChartOptions(title, prefix = '', dualAxis = false) {
        const scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return prefix + value;
                    }
                }
            }
        };
        
        if (dualAxis) {
            scales.y1 = {
                position: 'right',
                beginAtZero: true,
                grid: {
                    drawOnChartArea: false
                },
                ticks: {
                    callback: function(value) {
                        return prefix + value;
                    }
                }
            };
        }
        
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${prefix}${context.raw}`;
                        }
                    }
                }
            },
            scales
        };
    }
});

// Add this function to your upload.js file
function getFileIcon(filename) {
    const extension = filename.toLowerCase().split('.').pop();
    
    switch (extension) {
        case 'pdf':
            return 'fa-file-pdf';
        case 'xlsx':
        case 'xls':
            return 'fa-file-excel';
        case 'csv':
            return 'fa-file-csv';
        default:
            return 'fa-file';
    }
}

// Update your file display function to use the appropriate icon
function displayUploadedFile(filename, fileInfo) {
    const filesList = document.getElementById('filesList');
    const fileIcon = getFileIcon(filename);
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <div class="file-info">
            <div class="file-icon">
                <i class="fa-solid ${fileIcon}"></i>
            </div>
            <div class="file-details">
                <div class="file-name">${filename}</div>
                <div class="file-meta">${fileInfo.target_table} • ${fileInfo.rows_processed} records • ${new Date().toLocaleDateString()}</div>
            </div>
        </div>
        <div class="file-status success">
            <i class="fa-solid fa-check-circle"></i>
            Processed
        </div>
    `;
    
    // Add to top of list
    filesList.insertBefore(fileItem, filesList.firstChild);
}