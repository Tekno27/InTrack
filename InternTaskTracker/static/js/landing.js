document.addEventListener("DOMContentLoaded", function () {
    const sections = document.querySelectorAll(".section");
    if (!("IntersectionObserver" in window) || !sections.length) return;

    const observer = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.18 }
    );

    sections.forEach(function (section) {
        section.classList.add("will-reveal");
        observer.observe(section);
    });
});
