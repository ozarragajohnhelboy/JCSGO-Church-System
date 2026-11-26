// Group Detail Page JavaScript

function addMemberToGroup(groupId) {
    const userId = prompt('Enter user ID to add to this group:');
    if (userId && !isNaN(userId)) {
        $.ajax({
            url: `/members/ajax/add-to-group/${userId}/${groupId || window.groupId}/`,
            method: 'POST',
            data: {
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function (response) {
                if (response.success) {
                    location.reload();
                } else {
                    showError('Failed to add member to group');
                }
            },
            error: function () {
                showError('Failed to add member to group');
            }
        });
    }
}

function removeFromGroup(userId, groupId) {
    window.appConfirm('Remove this member from the group?', {
        title: 'Remove member',
        confirmLabel: 'Remove',
        danger: true,
    }).then(function (ok) {
        if (!ok) {
            return;
        }
        $.ajax({
            url: `/members/ajax/remove-from-group/${userId}/${groupId || window.groupId}/`,
            method: 'POST',
            data: {
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function (response) {
                if (response.success) {
                    location.reload();
                } else {
                    showError('Failed to remove member from group');
                }
            },
            error: function () {
                showError('Failed to remove member from group');
            }
        });
    });
}

function exportGroupMembers(groupId) {
    window.appAlert('Export functionality will be implemented here', {
        title: 'Export members',
    });
}

function showError(message) {
    if (typeof window.appAlert === 'function') {
        window.appAlert(message, { title: 'Error', danger: true });
    } else if (typeof window.JCSGOCMS !== 'undefined' && window.JCSGOCMS.showError) {
        window.JCSGOCMS.showError(null, message);
    }
}
