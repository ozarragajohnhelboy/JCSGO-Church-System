$(document).ready(function () {
    // Church selector functionality
    $('#church-selector').change(function () {
        var selectedChurch = $(this).val();
        if (selectedChurch) {
            // Redirect to church-specific view
            window.location.href = '/dashboard/?church=' + selectedChurch;
        } else {
            // Show all churches
            window.location.href = '/dashboard/';
        }
    });
});