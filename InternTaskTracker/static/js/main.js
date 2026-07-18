document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('show');
        backdrop?.classList.remove('show');
        toggle?.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('sidebar-open');
    }

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('show');
        backdrop?.classList.add('show');
        toggle?.setAttribute('aria-expanded', 'true');
        document.body.classList.add('sidebar-open');
    }

    if (toggle && sidebar) {
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
        backdrop?.addEventListener('click', closeSidebar);
        sidebar.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', closeSidebar);
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeSidebar();
        });
    }

    // Keep important/long alerts visible longer, but dismiss routine feedback.
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        const delay = alert.textContent.length > 180 ? 10000 : 5000;
        setTimeout(function () {
            if (document.body.contains(alert)) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, delay);
    });

    // Confirm consequential actions such as submitting work for review.
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!window.confirm(form.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Prevent accidental duplicate submissions and show immediate feedback.
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (e.defaultPrevented || !form.checkValidity()) return;
            const button = form.querySelector('button[type="submit"][data-submitting-text]');
            if (!button || button.disabled) return;
            button.dataset.originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>${button.dataset.submittingText}`;
        });
    });
});
