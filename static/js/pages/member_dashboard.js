// Member Dashboard Page JavaScript

function recordAttendance() {
    if (confirm('Record your attendance for today?')) {
        if (!window.userId) {
            alert('User ID not found');
            return;
        }

        fetch(`/members/ajax/record-attendance/${window.userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Attendance recorded successfully!');
                    location.reload();
                } else {
                    alert('Error recording attendance: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error recording attendance');
            });
    }
}

function leaveGroup() {
    if (confirm('Are you sure you want to leave this group?')) {
        // This would need to be implemented in the backend
        alert('Leave group functionality will be implemented in Phase 4');
    }
}
