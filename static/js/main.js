function getCSRFToken() {
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    const hiddenToken = document.querySelector('#csrf-token');
    if (hiddenToken) {
        return hiddenToken.value;
    }
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    }
});
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar) {
        sidebar.classList.toggle('show');

        if (sidebar.classList.contains('show')) {
            sidebarToggle.innerHTML = '<i class="bi bi-x"></i>';
        } else {
            sidebarToggle.innerHTML = '<i class="bi bi-list"></i>';
        }
    }
}
document.addEventListener('click', function (event) {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebar.classList.contains('show') &&
        !sidebar.contains(event.target) &&
        !sidebarToggle.contains(event.target)) {
        sidebar.classList.remove('show');
        sidebarToggle.innerHTML = '<i class="bi bi-list"></i>';
    }
});

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

if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
    Chart.defaults.color = '#6c757d';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
}

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

function refreshDashboard() {
    location.reload();
}

setInterval(function () {
    if (window.location.pathname.includes('/dashboard/')) {
        refreshDashboard();
    }
}, 300000);
document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebarToggle) {
        if (window.innerWidth < 768) {
            sidebar.classList.remove('show');
        }

        window.addEventListener('resize', function () {
            if (window.innerWidth >= 768) {
                sidebar.classList.remove('show');
                sidebarToggle.innerHTML = '<i class="bi bi-list"></i>';
            }
        });
    }
});

window.JCSGOCMS = {
    formatNumber: formatNumber,
    formatDate: formatDate,
    formatDateTime: formatDateTime,
    showLoading: showLoading,
    showError: showError,
    showSuccess: showSuccess,
    refreshDashboard: refreshDashboard,
    toggleSidebar: toggleSidebar
};

function confirmLogout() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = window.logoutUrl || '/logout/';
    
    const csrfTokenValue = getCSRFToken();
    if (csrfTokenValue) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfTokenValue;
        form.appendChild(csrfInput);
    }
    
    document.body.appendChild(form);
    form.submit();
}

$(document).ready(function () {
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);
});

$('.alert').on('close.bs.alert', function () {
    $(this).fadeOut('slow');
});

function selectChurch(churchDomain) {
    window.location.href = `/login/${churchDomain}/`;
}

function updateEmailPreview() {
    var prefix = $('#email-prefix').val();
    if (prefix) {
        var fullEmail = prefix + '@' + churchDomain + '.jcsgo.com';
        $('#email-preview').text(fullEmail);
    } else {
        $('#email-preview').text('');
    }
}

function updateLoginEmailPreview() {
    var prefix = $('#login-email-prefix').val();
    if (prefix) {
        var fullEmail = prefix + '@' + churchDomain + '.jcsgo.com';
        $('#email-preview').text(fullEmail);
    } else {
        $('#email-preview').text('');
    }
}

$(document).ready(function () {
    if ($('#email-prefix').length) {
        $('#email-prefix').on('input', updateEmailPreview);
        updateEmailPreview();
    }

    if ($('#login-email-prefix').length) {
        $('#login-email-prefix').on('input', updateLoginEmailPreview);
        updateLoginEmailPreview();
    }
}); 