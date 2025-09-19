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
    if (confirm('Remove this member from the group?')) {
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
    }
}

function exportGroupMembers(groupId) {
    // You can implement group member export functionality here
    alert('Export functionality will be implemented here');
}

function showError(message) {
    // Use the global showError function if available, otherwise create a simple alert
    if (typeof window.JCSGOCMS !== 'undefined' && window.JCSGOCMS.showError) {
        window.JCSGOCMS.showError(null, message);
    } else {
        alert(message);
    }
}
