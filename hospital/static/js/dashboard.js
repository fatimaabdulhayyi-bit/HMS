document.addEventListener("DOMContentLoaded", function () {
    const menuItems = document.querySelectorAll(".menu li a");
    const currentPath = window.location.pathname; // example: /patient/appointments/

    menuItems.forEach(link => {
    const linkPath = link.getAttribute("href");
    if (currentPath === linkPath || currentPath.endsWith(linkPath)) {
        link.parentElement.classList.add("active");
    } else {
        link.parentElement.classList.remove("active");
    }
});
});

document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebarMenu");
  const toggleBtn = document.getElementById("sidebarToggle");
    const closeBtn = document.getElementById("sidebarClose");
    
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("show");
  });
    
  closeBtn.addEventListener("click", () => {
    sidebar.classList.remove("show");
 });
    
});

document.getElementById("notificationBtn").addEventListener("click", function () {
    alert("Show notification list here");
});



