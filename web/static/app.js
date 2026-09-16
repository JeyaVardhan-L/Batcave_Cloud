// Batcave Cloud - Home-Lab Console Interactive Helpers
document.addEventListener('DOMContentLoaded', () => {
    // 1. Highlight Active Nav Item based on current path
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll('nav a');
    let matched = false;

    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
            matched = true;
        }
    });

    if (!matched) {
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '/' && currentPath.startsWith(href)) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    }
});
