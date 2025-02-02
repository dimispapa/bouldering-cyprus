document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box') // Text boxes
  const heroImages = document.querySelectorAll('.hero-image') // Hero images
  const scrollDownArrow = document.getElementById('scroll-down-arrow') // Down arrow
  const scrollToTopArrow = document.getElementById('scroll-to-top-arrow') // Up arrow
  const navbarHeight =
    document.querySelector('.navbar')?.offsetHeight + 100 || 0 // Navbar height

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

  // Smooth scrolling function taking into account the navbar height
  const smoothScrollTo = targetElement => {
    // Calculate the target position
    const targetPosition =
      targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight

    // Scroll to the target position
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
  }

  // Scroll-down functionality to move to the next text box
  scrollDownArrow.addEventListener('click', e => {
    e.preventDefault()

    // get the current target
    let currentTargetId = scrollDownArrow.getAttribute('data-target')
    let currentTarget = document.getElementById(currentTargetId)
    let currentIndex = [...textBoxes].indexOf(currentTarget)

    // If there is a next text box, scroll to it
    if (currentIndex < textBoxes.length) {
      smoothScrollTo(currentTarget)
    }
  })

  // IntersectionObserver to track text boxes and update scroll arrow
  const textBoxObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        // Get the index of the text box
        const index = [...textBoxes].indexOf(entry.target)

        // If the text box is intersecting, add the visible class
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')

          // Update scroll-down arrow target to the next text box
          if (index < textBoxes.length - 1) {
            scrollDownArrow.setAttribute('data-target', textBoxes[index + 1].id)
            scrollDownArrow.classList.remove('hidden')
          } else {
            // Hide the scroll-down arrow on the last text box
            scrollDownArrow.classList.add('hidden')
          }

          // Update hero image based on text box index
          updateHeroImage(index)
        }
      })
    },
    { threshold: 0.5 } // Trigger when 50% of the text box is visible
  )

  // Observe each text box
  textBoxes.forEach(box => textBoxObserver.observe(box))

  // Scroll-to-Top Arrow Logic
  scrollToTopArrow.addEventListener('click', e => {
    e.preventDefault()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  })

  // Side Navigation Click Event Listeners
  document.querySelectorAll('.side-navigation li').forEach(dot => {
    dot.addEventListener('click', function () {
      let textBox = document.querySelector(dot.getAttribute('data-target'))
      smoothScrollTo(textBox)
    })
  })

  // Initialize visibility
  updateHeroImage(0) // Ensure the first hero image is visible
})
