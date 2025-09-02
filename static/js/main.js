// Main JavaScript file for JCSGO CMS

// CSRF Token handling for AJAX requests
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Setup AJAX CSRF token for all requests
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs (same domain)
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    }
});

// Global functions
function showLoading(element) {
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
}

function showError(element, message) {
    if (element) {
        element.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> ${message}</div>`;
    }
}

function showSuccess(element, message) {
    if (element) {
        element.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> ${message}</div>`;
    }
}

// Chart.js global configuration
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
    Chart.defaults.color = '#6c757d';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Dashboard refresh functionality
function refreshDashboard() {
    location.reload();
}

// Auto-refresh dashboard every 5 minutes (300000 ms)
setInterval(function () {
    // Only refresh if user is on dashboard page
    if (window.location.pathname.includes('/dashboard/')) {
        refreshDashboard();
    }
}, 300000);

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Export functions
window.JCSGOCMS = {
    formatNumber: formatNumber,
    formatDate: formatDate,
    formatDateTime: formatDateTime,
    showLoading: showLoading,
    showError: showError,
    showSuccess: showSuccess,
    refreshDashboard: refreshDashboard
};

// Direct logout
function confirmLogout() {
    window.location.href = logoutUrl;
}

// Auto-dismiss alerts after 5 seconds
$(document).ready(function () {
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// Enhanced alert animations
$('.alert').on('close.bs.alert', function () {
    $(this).fadeOut('slow');
});



// Church selection functionality
function selectChurch(churchDomain) {
    window.location.href = `/login/${churchDomain}/`;
}

// Email preview functionality for registration
function updateEmailPreview() {
    var prefix = $('#email-prefix').val();
    if (prefix) {
        var fullEmail = prefix + '@' + churchDomain + '.jcsgo.com';
        $('#email-preview').text(fullEmail);
    } else {
        $('#email-preview').text('');
    }
}

// Email preview functionality for login
function updateLoginEmailPreview() {
    var prefix = $('#login-email-prefix').val();
    if (prefix) {
        var fullEmail = prefix + '@' + churchDomain + '.jcsgo.com';
        $('#email-preview').text(fullEmail);
    } else {
        $('#email-preview').text('');
    }
}

// Initialize email preview on page load
$(document).ready(function () {
    // Registration email preview
    if ($('#email-prefix').length) {
        $('#email-prefix').on('input', updateEmailPreview);
        updateEmailPreview();
    }

    // Login email preview
    if ($('#login-email-prefix').length) {
        $('#login-email-prefix').on('input', updateLoginEmailPreview);
        updateLoginEmailPreview();
    }

}); 