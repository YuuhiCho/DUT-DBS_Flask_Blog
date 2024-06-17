document.addEventListener('DOMContentLoaded', function () {
    // 导航栏固定
    handleNavbar();
});

// 导航栏在向下滚动时固定在页面顶部
function handleNavbar() {
    const navbar = document.querySelector('.navbar-default');
    const offsetTop = navbar.offsetTop;
    window.onscroll = function() {
        if (window.pageYOffset >= offsetTop) {
            navbar.classList.add('navbar-fixed-top');
        } else {
            navbar.classList.remove('navbar-fixed-top');
        }
    };
}