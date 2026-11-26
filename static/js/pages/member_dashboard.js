function recordAttendance() {
    window.appConfirm('Record your attendance for today?', {
        title: 'Record attendance',
        confirmLabel: 'Record',
    }).then(function (ok) {
        if (!ok) {
            return;
        }
        if (!window.userId) {
            window.appAlert('User ID not found', { title: 'Attendance', danger: true });
            return;
        }

        fetch('/members/ajax/record-attendance/' + window.userId + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success) {
                    return window.appAlert('Attendance recorded successfully!', {
                        title: 'Attendance',
                    }).then(function () {
                        location.reload();
                    });
                }
                window.appAlert('Error recording attendance: ' + data.message, {
                    title: 'Attendance',
                    danger: true,
                });
            })
            .catch(function (error) {
                console.error('Error:', error);
                window.appAlert('Error recording attendance', {
                    title: 'Attendance',
                    danger: true,
                });
            });
    });
}
