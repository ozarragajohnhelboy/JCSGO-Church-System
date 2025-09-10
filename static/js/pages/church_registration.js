$(document).ready(function () {
    // Email preview functionality
    $('#email-prefix').on('input', function () {
        var prefix = $(this).val()
        if (prefix) {
            var fullEmail = prefix + '@{{ church.domain }}.jcsgo.com'
            $('#email-preview').text(fullEmail)
        } else {
            $('#email-preview').text('')
        }
    })

    // Trigger on page load to show initial preview
    $('#email-prefix').trigger('input')
})