document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box')
  const heroImages = document.querySelectorAll('.hero-image')

  // Ensure the number of hero images matches the number of text boxes
  if (heroImages.length < textBoxes.length) {
    console.warn('Not enough hero images for the text boxes.')
  }

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

  // IntersectionObserver for text boxes
  const textBoxObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible') // Show the text box

          // Find the index of the visible text box
          const index = Array.from(textBoxes).indexOf(entry.target)

          // Update hero image based on text box index
          updateHeroImage(index)
        }
      })
    },
    {
      threshold: 0.5 // Trigger when 50% of the text box is visible
    }
  )

  // Observe each text box
  textBoxes.forEach(box => textBoxObserver.observe(box))

  // Initialize the first hero image
  updateHeroImage(0)
})
