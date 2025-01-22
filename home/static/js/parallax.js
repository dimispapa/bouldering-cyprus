document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box') // Text boxes
  const heroImages = document.querySelectorAll('.hero-image') // Hero images
  const scrollDownArrows = document.querySelectorAll('.scroll-down-arrow') // Down arrows
  const scrollToTopArrow = document.querySelector('.scroll-to-top-arrow') // Up arrow
  const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0 // Navbar height

  // Function to update hero image visibility
  const updateHeroImage = index => {
    heroImages.forEach((image, i) => {
      if (i === index) {
        image.classList.add('visible')
      } else {
        image.classList.remove('visible')
      }
    })
  }

  // Smooth scrolling function
  const smoothScrollTo = targetElement => {
    const targetPosition =
      targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
  }

  // Add click event listeners to each down arrow
  scrollDownArrows.forEach((arrow, index) => {
    arrow.addEventListener('click', e => {
      e.preventDefault()

      // Scroll to the corresponding text box
      if (textBoxes[index]) {
        smoothScrollTo(textBoxes[index])
      }
    })
  })

  // IntersectionObserver for text boxes
  const textBoxObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        const index = Array.from(textBoxes).indexOf(entry.target)

        if (entry.isIntersecting) {
          // Show the current text box
          entry.target.classList.add('visible')

          // Update hero image based on text box index
          updateHeroImage(index)

          // Hide the current down arrow
          if (scrollDownArrows[index]) {
            scrollDownArrows[index].style.display = 'none'
          }
        }
      })
    },
    {
      threshold: 0.5 // Trigger when 50% of the text box is visible
    }
  )

  // Observe each text box
  textBoxes.forEach(box => textBoxObserver.observe(box))

  // Scroll-to-Top Arrow Logic
  scrollToTopArrow.addEventListener('click', e => {
    e.preventDefault()

    // Scroll to the top of the page
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  })

  // Initialize visibility
  updateHeroImage(0) // Ensure the first hero image is visible
  scrollDownArrows.forEach((arrow, index) => {
    if (index === 0) {
      arrow.style.display = 'block' // Show the first arrow
    } else {
      arrow.style.display = 'none' // Hide all other arrows initially
    }
  })
})
