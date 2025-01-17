document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar')

  const toggleNavbarBackground = () => {
    if (window.scrollY > 50) {
      navbar.classList.add('navbar-scrolled') // Add solid background
      navbar.classList.remove('navbar-transparent') // Remove transparency
    } else {
      navbar.classList.add('navbar-transparent') // Restore transparency
      navbar.classList.remove('navbar-scrolled') // Remove solid background
    }
  }

  // Run on page load and on scroll
  toggleNavbarBackground()
  window.addEventListener('scroll', toggleNavbarBackground)
})
