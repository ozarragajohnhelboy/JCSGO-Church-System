document.addEventListener('DOMContentLoaded', function() {
    if (window.innerWidth < 992) {
        const btnGroups = document.querySelectorAll('.btn-group');
        
        btnGroups.forEach(function(group) {
            group.addEventListener('click', function(e) {
                if (e.target === group || e.target === group.firstChild) {
                    e.stopPropagation();
                    
                    document.querySelectorAll('.btn-group.show').forEach(function(otherGroup) {
                        if (otherGroup !== group) {
                            otherGroup.classList.remove('show');
                        }
                    });
                    
                    group.classList.toggle('show');
                }
            });
        });
        
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.btn-group')) {
                document.querySelectorAll('.btn-group.show').forEach(function(group) {
                    group.classList.remove('show');
                });
            }
        });
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth >= 992) {
        document.querySelectorAll('.btn-group.show').forEach(function(group) {
            group.classList.remove('show');
        });
    }
});

