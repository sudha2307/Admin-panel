function showSection(sectionId) {
    // Remove active class from all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Add active class to the selected section
    document.getElementById(sectionId).classList.add('active');

    // Update active state on sidebar menu
    document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.sidebar-menu .menu-item[onclick="showSection('${sectionId}')"]`).classList.add('active');
}
