document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const pageContent = document.getElementById('page-content-wrapper');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            pageContent.classList.toggle('active');
        });
    }

    // Close sidebar when clicking/tapping outside on mobile
    if (sidebar && pageContent) {
        pageContent.addEventListener('click', function (e) {
            if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                pageContent.classList.remove('active');
            }
        });
    }

    // Swipe right to open sidebar on mobile
    let touchStartX = 0;
    document.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    document.addEventListener('touchend', function (e) {
        if (window.innerWidth <= 768 && !sidebar.classList.contains('active')) {
            const dx = e.changedTouches[0].screenX - touchStartX;
            if (dx > 80) {
                sidebar.classList.add('active');
                pageContent.classList.add('active');
            }
        }
    });

    function updateNotifBadges(count) {
        const badges = ['notif-badge', 'notif-count'];
        badges.forEach(function(id) {
            const el = document.getElementById(id);
            if (!el) return;
            if (count > 0) {
                el.textContent = count;
                el.style.display = 'inline';
            } else {
                el.style.display = 'none';
            }
        });
    }

    const navbarBadge = document.getElementById('notif-badge');
    if (navbarBadge) {
        fetch('/notifications/unread-count')
            .then(function(r) { return r.json(); })
            .then(function(data) { updateNotifBadges(data.count); })
            .catch(function() {});
    }

    const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
    autoDismissAlerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });

    const bulkCheckAll = document.getElementById('checkAll');
    if (bulkCheckAll) {
        bulkCheckAll.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.member-checkbox');
            checkboxes.forEach(cb => cb.checked = bulkCheckAll.checked);
        });
    }

    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
