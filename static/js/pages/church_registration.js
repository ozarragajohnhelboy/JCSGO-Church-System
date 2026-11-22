$(document).ready(function () {
    var churchDomain = window.registrationChurchDomain || '';

    $('#email-prefix').on('input', function () {
        var prefix = $(this).val();
        if (prefix) {
            $('#email-preview').text(prefix + '@' + churchDomain + '.jcsgo.com');
        } else {
            $('#email-preview').text('');
        }
    });

    $('#email-prefix').trigger('input');

    // After a failed submit, bring the first field error into view so it is not missed below the fold.
    var firstError = document.querySelector('.registration-card .text-danger');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
