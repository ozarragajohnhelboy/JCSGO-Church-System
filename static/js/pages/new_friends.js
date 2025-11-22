document.addEventListener('DOMContentLoaded', function() {
    if (window.innerWidth < 992) {
        const tableBtnGroups = document.querySelectorAll('table .btn-group');
        
        tableBtnGroups.forEach(function(group) {
            const toggle = document.createElement('button');
            toggle.className = 'mobile-menu-toggle';
            toggle.innerHTML = '⋮';
            toggle.type = 'button';
            
            group.insertBefore(toggle, group.firstChild);
            
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                document.querySelectorAll('table .btn-group.show').forEach(function(otherGroup) {
                    if (otherGroup !== group) {
                        otherGroup.classList.remove('show');
                        const actions = otherGroup.querySelectorAll('.btn-action');
                        actions.forEach(function(action) {
                            action.style.top = '';
                            action.style.bottom = '';
                            action.style.left = '';
                            action.style.right = '';
                        });
                    }
                });
                
                group.classList.toggle('show');
                
                if (group.classList.contains('show')) {
                    const rect = toggle.getBoundingClientRect();
                    const actions = group.querySelectorAll('.btn-action');
                    const footer = document.querySelector('.footer');
                    const footerTop = footer ? footer.getBoundingClientRect().top : window.innerHeight;
                    const viewportHeight = window.innerHeight;
                    const availableSpace = footerTop - rect.bottom;
                    const totalDropdownHeight = actions.length * 44;
                    
                    let startTop = rect.bottom + 5;
                    
                    if (availableSpace < totalDropdownHeight) {
                        startTop = Math.max(10, footerTop - totalDropdownHeight - 10);
                    }
                    
                    actions.forEach(function(action, index) {
                        action.style.position = 'fixed';
                        action.style.top = (startTop + (index * 44)) + 'px';
                        action.style.right = '1rem';
                        action.style.left = 'auto';
                        action.style.bottom = 'auto';
                    });
                } else {
                    const actions = group.querySelectorAll('.btn-action');
                    actions.forEach(function(action) {
                        action.style.top = '';
                        action.style.bottom = '';
                        action.style.left = '';
                        action.style.right = '';
                    });
                }
            });
        });
        
        document.addEventListener('click', function(e) {
            if (!e.target.closest('table .btn-group')) {
                document.querySelectorAll('table .btn-group.show').forEach(function(group) {
                    group.classList.remove('show');
                    const actions = group.querySelectorAll('.btn-action');
                    actions.forEach(function(action) {
                        action.style.top = '';
                        action.style.bottom = '';
                        action.style.left = '';
                        action.style.right = '';
                    });
                });
            }
        });
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth >= 992) {
        document.querySelectorAll('table .btn-group.show').forEach(function(group) {
            group.classList.remove('show');
            const actions = group.querySelectorAll('.btn-action');
            actions.forEach(function(action) {
                action.style.top = '';
                action.style.bottom = '';
                action.style.left = '';
                action.style.right = '';
            });
        });
        
        document.querySelectorAll('table .mobile-menu-toggle').forEach(function(toggle) {
            toggle.remove();
        });
    } else {
        const tableBtnGroups = document.querySelectorAll('table .btn-group');
        tableBtnGroups.forEach(function(group) {
            if (!group.querySelector('.mobile-menu-toggle')) {
                const toggle = document.createElement('button');
                toggle.className = 'mobile-menu-toggle';
                toggle.innerHTML = '⋮';
                toggle.type = 'button';
                
                group.insertBefore(toggle, group.firstChild);
                
                toggle.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    document.querySelectorAll('table .btn-group.show').forEach(function(otherGroup) {
                        if (otherGroup !== group) {
                            otherGroup.classList.remove('show');
                            const actions = otherGroup.querySelectorAll('.btn-action');
                            actions.forEach(function(action) {
                                action.style.top = '';
                                action.style.bottom = '';
                                action.style.left = '';
                                action.style.right = '';
                            });
                        }
                    });
                    
                    group.classList.toggle('show');
                    
                    if (group.classList.contains('show')) {
                        const rect = toggle.getBoundingClientRect();
                        const actions = group.querySelectorAll('.btn-action');
                        const footer = document.querySelector('.footer');
                        const footerTop = footer ? footer.getBoundingClientRect().top : window.innerHeight;
                        const viewportHeight = window.innerHeight;
                        const availableSpace = footerTop - rect.bottom;
                        const totalDropdownHeight = actions.length * 44;
                        
                        let startTop = rect.bottom + 5;
                        
                        if (availableSpace < totalDropdownHeight) {
                            startTop = Math.max(10, footerTop - totalDropdownHeight - 10);
                        }
                        
                        actions.forEach(function(action, index) {
                            action.style.position = 'fixed';
                            action.style.top = (startTop + (index * 44)) + 'px';
                            action.style.right = '1rem';
                            action.style.left = 'auto';
                            action.style.bottom = 'auto';
                        });
                    } else {
                        const actions = group.querySelectorAll('.btn-action');
                        actions.forEach(function(action) {
                            action.style.top = '';
                            action.style.bottom = '';
                            action.style.left = '';
                            action.style.right = '';
                        });
                    }
                });
            }
        });
    }
});

