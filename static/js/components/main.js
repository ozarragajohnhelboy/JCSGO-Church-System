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
function getSidebarElement() {
    return document.getElementById('sidebar') || document.querySelector('.col-md-3.col-lg-2');
}

function setSidebarOpen(isOpen) {
    const sidebar = getSidebarElement();
    const sidebarToggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('mobileOverlay');

    if (!sidebar) {
        return;
    }

    sidebar.classList.toggle('show', isOpen);
    document.body.classList.toggle('sidebar-open', isOpen);

    if (sidebarToggle) {
        sidebarToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        sidebarToggle.innerHTML = isOpen
            ? '<i class="bi bi-x-lg" aria-hidden="true"></i>'
            : '<i class="bi bi-list" aria-hidden="true"></i>';
    }

    if (overlay) {
        overlay.classList.toggle('show', isOpen);
    }

    document.body.style.overflow = isOpen ? 'hidden' : '';
}

function toggleSidebar(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const sidebar = getSidebarElement();
    if (!sidebar) {
        return;
    }

    setSidebarOpen(!sidebar.classList.contains('show'));
}

document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('mobileOverlay');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            setSidebarOpen(false);
        });
    }
});

document.addEventListener('click', function (event) {
    const sidebar = getSidebarElement();
    const sidebarToggle = document.getElementById('sidebarToggle');

    if (sidebar && sidebar.classList.contains('show') &&
        !sidebar.contains(event.target) &&
        (!sidebarToggle || !sidebarToggle.contains(event.target))) {
        setSidebarOpen(false);
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
    const sidebar = getSidebarElement();
    if (sidebar) {
        if (window.innerWidth < 992) {
            setSidebarOpen(false);
        }

        window.addEventListener('resize', function () {
            if (window.innerWidth >= 992) {
                setSidebarOpen(false);
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
        $('.toast-alerts .alert').fadeOut('slow');
    }, 5000);
});

$('.toast-alerts .alert').on('close.bs.alert', function () {
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