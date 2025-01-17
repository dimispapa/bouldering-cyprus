document.addEventListener('DOMContentLoaded', () => {
  const navbar = document.querySelector('.navbar')

  const toggleNavbarState = () => {
    if (window.scrollY > 50) {
      navbar.classList.add('navbar-scrolled') // Add scrolled state
      navbar.classList.remove('navbar-transparent') // Remove transparent state
    } else {
      navbar.classList.add('navbar-transparent') // Add transparent state
      navbar.classList.remove('navbar-scrolled') // Remove scrolled state
    }
  }

  // Run on page load and on scroll
  toggleNavbarState()
  window.addEventListener('scroll', toggleNavbarState)
})
