document.addEventListener('DOMContentLoaded', () => {
  const textBoxes = document.querySelectorAll('.text-box')
  const heroImages = document.querySelectorAll('.hero-image')

  const updateHeroImage = index => {
    heroImages.forEach((image, i) => {
      image.classList.toggle('visible', i === index)
    })
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const index = [...textBoxes].indexOf(entry.target)
      if (entry.isIntersecting) {
        entry.target.classList.add('visible')
        updateHeroImage(index)
      }
    })
  })

  textBoxes.forEach(box => observer.observe(box))

  // JavaScript for dynamically updating the modal image
  document.querySelectorAll('.gallery-thumbnail').forEach(thumbnail => {
    thumbnail.addEventListener('click', function () {
      const imageSrc = this.getAttribute('data-bs-image')
      const modalImage = document.getElementById('modalImage')
      modalImage.src = imageSrc
    })
  })
})
