// Care Group Detail Page JavaScript

function showAlert(type, title, message) {
    // Create a temporary alert element that matches Django's message format
    const alertContainer = document.querySelector('.position-fixed.top-0.end-0.p-3');
    if (!alertContainer) {
        // If no alert container exists, create one
        const container = document.createElement('div');
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '10001';
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

let searchTimeoutDetail = null;
let selectedMemberDetail = null;

function showAddMemberModal() {
    selectedMemberDetail = null;
    
    const memberSearch = document.getElementById('member_search_detail');
    const memberIdInput = document.getElementById('member_id_detail');
    const memberSuggestions = document.getElementById('member_suggestions_detail');
    const memberStatus = document.getElementById('member_status_detail');
    const submitBtn = document.getElementById('submitBtnDetail');
    
    if (memberSearch) {
        memberSearch.value = '';
        memberIdInput.value = '';
        memberSuggestions.innerHTML = '';
        memberSuggestions.style.display = 'none';
        memberStatus.innerHTML = '';
        submitBtn.disabled = true;
    }
    
    new bootstrap.Modal(document.getElementById('addMemberModal')).show();
}

document.addEventListener('DOMContentLoaded', function() {
    const memberSearch = document.getElementById('member_search_detail');
    const memberSuggestions = document.getElementById('member_suggestions_detail');
    const memberIdInput = document.getElementById('member_id_detail');
    const memberStatus = document.getElementById('member_status_detail');
    const submitBtn = document.getElementById('submitBtnDetail');
    const addMemberForm = document.getElementById('addMemberFormDetail');
    
    if (memberSearch && window.groupId) {
        memberSearch.addEventListener('input', function() {
            const query = this.value.trim();
            memberIdInput.value = '';
            selectedMemberDetail = null;
            submitBtn.disabled = true;
            memberStatus.innerHTML = '';
            
            if (query.length < 2) {
                memberSuggestions.innerHTML = '';
                memberSuggestions.style.display = 'none';
                return;
            }
            
            clearTimeout(searchTimeoutDetail);
            searchTimeoutDetail = setTimeout(() => {
                fetch(`/members/ajax/search-members/${window.groupId}/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            memberStatus.innerHTML = `<div class="text-danger small">${data.error}</div>`;
                            return;
                        }
                        
                        memberSuggestions.innerHTML = '';
                        
                        if (data.members && data.members.length > 0) {
                            data.members.forEach(member => {
                                const item = document.createElement('div');
                                item.className = 'list-group-item list-group-item-action';
                                
                                if (member.in_group) {
                                    item.classList.add('list-group-item-danger');
                                    item.innerHTML = `
                                        <div class="d-flex w-100 justify-content-between">
                                            <div>
                                                <strong>${member.name}</strong>
                                                <br><small class="text-muted">${member.role}</small>
                                            </div>
                                            <small class="text-danger">Already in "${member.group_name}"</small>
                                        </div>
                                    `;
                                } else {
                                    item.style.cursor = 'pointer';
                                    item.innerHTML = `
                                        <div class="d-flex w-100 justify-content-between">
                                            <div>
                                                <strong>${member.name}</strong>
                                                <br><small class="text-muted">${member.role}</small>
                                            </div>
                                        </div>
                                    `;
                                    item.addEventListener('click', function() {
                                        selectedMemberDetail = member;
                                        memberSearch.value = member.name;
                                        memberIdInput.value = member.id;
                                        memberSuggestions.style.display = 'none';
                                        memberStatus.innerHTML = `<div class="text-success small"><i class="bi bi-check-circle"></i> Selected: ${member.name}</div>`;
                                        submitBtn.disabled = false;
                                    });
                                }
                                
                                memberSuggestions.appendChild(item);
                            });
                            memberSuggestions.style.display = 'block';
                        } else {
                            memberSuggestions.innerHTML = '<div class="list-group-item text-muted">No members found</div>';
                            memberSuggestions.style.display = 'block';
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        memberStatus.innerHTML = '<div class="text-danger small">Error searching members</div>';
                    });
            }, 300);
        });
        
        document.addEventListener('click', function(e) {
            if (memberSearch && memberSuggestions && !memberSearch.contains(e.target) && !memberSuggestions.contains(e.target)) {
                memberSuggestions.style.display = 'none';
            }
        });
        
        if (addMemberForm) {
            addMemberForm.addEventListener('submit', function(e) {
                if (!memberIdInput.value) {
                    e.preventDefault();
                    showAlert('warning', 'No Member Selected', 'Please search and select a member to add.');
                    return;
                }
                
                if (selectedMemberDetail && selectedMemberDetail.in_group) {
                    e.preventDefault();
                    showAlert('danger', 'Member Already in Group', `This member is already in "${selectedMemberDetail.group_name}" care group.`);
                    return;
                }
            });
        }
    }
});

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
