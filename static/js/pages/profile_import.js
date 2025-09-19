// Profile Import Page JavaScript

function downloadTemplate() {
    // Create a sample CSV template
    const csvContent = 'email,first_name,last_name,phone_number,address,birth_date\n' +
        'john.doe@example.com,John,Doe,+1234567890,123 Main St,1990-01-15\n' +
        'jane.smith@example.com,Jane,Smith,+1234567891,456 Oak Ave,1985-05-20';

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'profile_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
