document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box') // Text boxes
  const heroImages = document.querySelectorAll('.hero-image') // Hero images
  const scrollDownArrow = document.getElementById('scroll-down-arrow') // Down arrow
  const scrollToTopArrow = document.getElementById('scroll-to-top-arrow') // Up arrow
  const navbarHeight = document.querySelector('.navbar')?.offsetHeight + 100 || 0 // Navbar height

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
    const targetPosition =
      targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
  }

  // Add click event listeners to each down arrow
  scrollDownArrow.addEventListener('click', e => {
    e.preventDefault()

    // Scroll to the corresponding text box
    const targetElement = document.querySelector(scrollDownArrow.getAttribute('data-target'))
    smoothScrollTo(targetElement)
  })

  // IntersectionObserver for text boxes
  const textBoxObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        const index = Array.from(textBoxes).indexOf(entry.target)

        if (entry.isIntersecting) {
          // Show the current text box
          entry.target.classList.add('visible')

          // Hide the scroll down arrow
          if (index === 0) {
            scrollDownArrow.classList.add('hidden')
          }

          // Update hero image based on text box index
          updateHeroImage(index)
        }
        else if (index === 0) {
          // Unhide the scroll down arrow
          scrollDownArrow.classList.remove('hidden')
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

  // Add click event listeners to each side navigation dot
  document.querySelectorAll('.side-navigation li').forEach(function(dot) {
    dot.addEventListener('click', function() {
      let textBox = document.querySelector(dot.getAttribute('data-target'));
      smoothScrollTo(textBox);
    });
  });

  // Initialize visibility
  updateHeroImage(0) // Ensure the first hero image is visible
})
