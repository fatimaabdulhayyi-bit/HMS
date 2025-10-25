document.addEventListener("DOMContentLoaded", function () {
    const menuItems = document.querySelectorAll(".menu li a");
    const currentPath = window.location.pathname; // example: /patient/appointments/

    menuItems.forEach(link => {
        const linkPath = link.getAttribute("href");
        // match only if path is same or ends with that path
        if (currentPath === linkPath || currentPath.endsWith(linkPath)) {
            link.parentElement.classList.add("active");
        } else {
            link.parentElement.classList.remove("active");
        }
    });
});
