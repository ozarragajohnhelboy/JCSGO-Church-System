// Care Group Detail Page JavaScript

function showAlert(type, title, message) {
    // Create a temporary alert element that matches Django's message format
    const alertContainer = document.querySelector('.position-fixed.top-0.end-0.p-3');
    if (!alertContainer) {
        // If no alert container exists, create one
        const container = document.createElement('div');
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }

    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show shadow-sm border-0" role="alert" style="border-radius: 12px; min-width: 300px; max-width: 500px;">
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi bi-${type === 'success' ? 'check-circle-fill text-success' : type === 'danger' ? 'exclamation-triangle-fill text-danger' : type === 'info' ? 'info-circle-fill text-info' : 'exclamation-circle-fill text-warning'} fs-4"></i>
                </div>
                <div class="flex-grow-1">
                    <strong class="me-2">${title}!</strong>
                    <div class="small">${message}</div>
                </div>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        </div>
    `;

    const container = document.querySelector('.position-fixed.top-0.end-0.p-3');
    container.insertAdjacentHTML('beforeend', alertHtml);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

function showAddMemberModal() {
    if (window.availableMembers) {
        new bootstrap.Modal(document.getElementById('addMemberModal')).show();
    } else {
        showAlert('info', 'No Available Members', 'All members are already in care groups. There are no available members to add at this time.');
    }
}

function removeMember(memberId, memberName) {
    // Create confirmation modal
    const modalHtml = `
        <div class="modal fade" id="confirmRemoveModal" tabindex="-1" aria-labelledby="confirmRemoveModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmRemoveModalLabel">
                            <i class="bi bi-exclamation-triangle text-warning me-2"></i>
                            Confirm Removal
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to remove <strong>${memberName}</strong> from this care group?</p>
                        <p class="text-muted small">This action cannot be undone.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" onclick="confirmRemove(${memberId})">
                            <i class="bi bi-person-dash me-1"></i>Remove Member
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('confirmRemoveModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('confirmRemoveModal'));
    modal.show();

    // Clean up modal after it's hidden
    document.getElementById('confirmRemoveModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

function confirmRemove(memberId) {
    if (window.removeMemberUrl) {
        window.location.href = window.removeMemberUrl.replace('0', memberId);
    }
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
