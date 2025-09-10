// Church Statistics Page JavaScript

// Sample data - replace with actual data from your views
function initializeCharts() {
    // Role Distribution Chart
    const roleCtx = document.getElementById('roleChart');
    if (roleCtx) {
        const roleData = {
            labels: window.roleLabels || [],
            datasets: [{
                data: window.roleData || [],
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
            }]
        };

        new Chart(roleCtx, {
            type: 'doughnut',
            data: roleData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Timer Status Chart
    const timerCtx = document.getElementById('timerChart');
    if (timerCtx) {
        const timerData = {
            labels: window.timerLabels || [],
            datasets: [{
                data: window.timerData || [],
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#FF9F40']
            }]
        };

        new Chart(timerCtx, {
            type: 'doughnut',
            data: timerData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Growth Trend Chart (sample data)
    const growthCtx = document.getElementById('growthChart');
    if (growthCtx) {
        new Chart(growthCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Total Members',
                    data: window.growthData || [120, 135, 142, 158, 165, 172, 180, 188, 195, 203, 210, 218],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Capacity Chart (sample data)
    const capacityCtx = document.getElementById('capacityChart');
    if (capacityCtx) {
        new Chart(capacityCtx, {
            type: 'bar',
            data: {
                labels: ['Available', 'Nearly Full', 'Full'],
                datasets: [{
                    label: 'Groups',
                    data: window.capacityData || [0, 0, 0],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Wait for Chart.js to be loaded
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    } else {
        // If Chart.js is not loaded yet, wait a bit and try again
        setTimeout(initializeCharts, 100);
    }
});
