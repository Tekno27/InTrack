document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            sidebar.classList.toggle('show');
        });
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('show') && !sidebar.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }

    // Auto-dismiss alerts after 4 seconds
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        }, 4000);
    });
});
