document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box')
  const heroImages = document.querySelectorAll('.hero-image')

  // IntersectionObserver for hero images
  const heroImageObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible') // Show the current hero image
          console.log(`Image ${entry.target.id} became visible`)
        } else {
          entry.target.classList.remove('visible') // Hide the hero image
          console.log(`Image ${entry.target.id} is now hidden`)
        }
      })
    },
    {
      threshold: 0.5 // Trigger when 50% of the element is visible
    }
  )

  // Observe each hero image
  heroImages.forEach(image => heroImageObserver.observe(image))

  // IntersectionObserver for text boxes
  const textBoxObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible') // Add 'visible' class to trigger animation
          observer.unobserve(entry.target) // Stop observing once it's visible
        }
      })
    },
    {
      threshold: 0.5 // Trigger when 50% of the element is visible
    }
  )

  // Observe each text box
  textBoxes.forEach(box => textBoxObserver.observe(box))
})
