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