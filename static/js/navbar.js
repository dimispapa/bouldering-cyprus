document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar');

  // Function to toggle navbar transparency only for desktop
  const toggleNavbarTransparency = () => {
    if (window.innerWidth > 768) {
      if (window.scrollY > 20) {
        navbar.classList.add('navbar-scrolled'); // Apply solid background
      } else {
        navbar.classList.remove('navbar-scrolled'); // Keep it transparent
      }
    } else {
      navbar.classList.add('navbar-scrolled'); // Always solid on mobile
    }
  };

  // Run function on scroll
  window.addEventListener('scroll', toggleNavbarTransparency);

  // Run function on page load to set initial state
  toggleNavbarTransparency();

  // Run function on window resize to adapt behavior
  window.addEventListener('resize', toggleNavbarTransparency);
});