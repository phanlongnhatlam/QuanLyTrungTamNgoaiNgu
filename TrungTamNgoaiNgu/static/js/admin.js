document.addEventListener("DOMContentLoaded", function() {
    const menuToggle = document.getElementById("menuToggle");
    const wrapper = document.getElementById("wrapper");

    // Kiểm tra xem nút có tồn tại không để tránh lỗi ở các trang khác
    if (menuToggle && wrapper) {
        menuToggle.addEventListener("click", function(e) {
            e.preventDefault();
            wrapper.classList.toggle("toggled");
        });
    }
});