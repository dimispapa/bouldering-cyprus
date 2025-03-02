document.addEventListener('DOMContentLoaded', () => {
  let images = []
  let currentIndex = 0

  const modalImage = document.getElementById('modalImage')
  const prevBtn = document.getElementById('prevBtn')
  const nextBtn = document.getElementById('nextBtn')

  // Function to validate image URL
  function isValidImageUrl(url) {
    const pattern = /^(https?:\/\/.*\.(?:png|jpg|jpeg|gif|webp|svg))$/i;
    return pattern.test(url);
  }

  // Collect all gallery images dynamically
  document
    .querySelectorAll('.gallery-thumbnail')
    .forEach((thumbnail, index) => {
      const imageUrl = thumbnail.src;
      if (isValidImageUrl(imageUrl)) {
        images.push(imageUrl);
      }

      // Attach click event to set modal image dynamically
      thumbnail.addEventListener('click', function () {
        currentIndex = index
        modalImage.src = images[currentIndex]
        updateNavigationButtons()
      })
    })

  // Function to update navigation button visibility
  function updateNavigationButtons () {
    prevBtn.style.display = currentIndex === 0 ? 'none' : 'inline-block'
    nextBtn.style.display =
      currentIndex === images.length - 1 ? 'none' : 'inline-block'
  }

  // Previous Button Click Event
  prevBtn.addEventListener('click', function () {
    if (currentIndex > 0) {
      currentIndex--
      modalImage.src = images[currentIndex]
      updateNavigationButtons()
    }
  })

  // Next Button Click Event
  nextBtn.addEventListener('click', function () {
    if (currentIndex < images.length - 1) {
      currentIndex++
      modalImage.src = images[currentIndex]
      updateNavigationButtons()
    }
  })

  // Ensure buttons are updated initially when the modal opens
  updateNavigationButtons()
})
