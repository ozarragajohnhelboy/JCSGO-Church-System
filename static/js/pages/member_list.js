function openTimerOrRegularModalFromBtn(button) {
    const userId = button.dataset.userId;
    const currentStatus = button.dataset.timerStatus;
    const fullName = button.dataset.fullName;
    openTimerOrRegularModal(userId, currentStatus, fullName);
}

function openTimerOrRegularModal(userId, currentStatus, fullName) {
    document.getElementById('trUserId').value = userId;
    document.getElementById('trTimer').value = String(currentStatus || 1);
    document.getElementById('trAction').value = 'TIMER';
    document.getElementById('trTimerSection').style.display = '';
    document.getElementById('trRegularSection').style.display = 'none';
    document.getElementById('trModalTitle').innerText = `Update ${fullName}`;
    const modal = new bootstrap.Modal(document.getElementById('timerRegularModal'));
    modal.show();
}

document.addEventListener('DOMContentLoaded', function () {
    const actionSelect = document.getElementById('trAction');
    if (actionSelect) {
        actionSelect.addEventListener('change', function () {
            const isRegular = this.value === 'REGULAR';
            document.getElementById('trTimerSection').style.display = isRegular ? 'none' : '';
            document.getElementById('trRegularSection').style.display = isRegular ? '' : 'none';
        });
    }
});

function submitTimerOrRegular() {
    const userId = document.getElementById('trUserId').value;
    const action = document.getElementById('trAction').value;

    if (action === 'REGULAR') {
        const role = document.getElementById('trRole').value;
        $.ajax({
            url: `/members/ajax/update-user-role/${userId}/`,
            method: 'POST',
            data: {
                role: role,
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function (response) {
                if (response.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('timerRegularModal'));
                    modal.hide();

                    showSuccess('Member status updated successfully');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showError('Failed to update member status');
                }
            },
            error: function () {
                showError('Failed to update member status');
            }
        });
    } else {
        const timerStatus = document.getElementById('trTimer').value;
        $.ajax({
            url: `/members/ajax/update-timer-status/${userId}/`,
            method: 'POST',
            data: {
                timer_status: timerStatus,
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function (response) {
                if (response.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('timerRegularModal'));
                    modal.hide();

                    showSuccess('Timer status updated successfully');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showError('Failed to update timer status');
                }
            },
            error: function () {
                showError('Failed to update timer status');
            }
        });
    }
}

function recordAttendance(userId) {
    if (confirm('Record attendance for this member?')) {
        $.ajax({
            url: `/members/ajax/record-attendance/${userId}/`,
            method: 'POST',
            data: {
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function (response) {
                if (response.success) {
                    showSuccess('Attendance recorded successfully');
                } else {
                    showError('Failed to record attendance');
                }
            },
            error: function () {
                showError('Failed to record attendance');
            }
        });
    }
}
