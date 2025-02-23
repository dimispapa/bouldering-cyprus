document.addEventListener('DOMContentLoaded', function () {
  const dateRangePicker = initializeDateRangePicker()
  const selectedCrashpads = new Set()

  function initializeDateRangePicker () {
    return $('#daterange').daterangepicker({
      autoUpdateInput: false,
      minDate: moment(),
      locale: {
        cancelLabel: 'Clear',
        format: 'DD-MMM-YYYY',
        separator: ' - '
      }
    })
  }

  // Date selection handlers
  $('#daterange').on('apply.daterangepicker', function (ev, picker) {
    $(this).val(
      picker.startDate.format('DD-MMM-YYYY') +
        ' - ' +
        picker.endDate.format('DD-MMM-YYYY')
    )
    fetchAvailableCrashpads(picker.startDate, picker.endDate)
  })

  $('#daterange').on('cancel.daterangepicker', function (ev, picker) {
    $(this).val('')
    $('#crashpads-container').hide()
    selectedCrashpads.clear()
    updateSelectionSummary()
  })

  async function fetchAvailableCrashpads (startDate, endDate) {
    const spinner = document.getElementById('loading-spinner')
    const container = document.getElementById('crashpads-container')

    try {
      showElement(spinner)
      hideElement(container)

      const response = await fetch(
        `/rentals/api/crashpads/available/?check_in=${startDate.format(
          'YYYY-MM-DD'
        )}&check_out=${endDate.format('YYYY-MM-DD')}`
      )

      if (!response.ok) throw new Error('Failed to fetch crashpads')

      const crashpads = await response.json()
      displayCrashpads(crashpads)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to load available crashpads. Please try again.')
    } finally {
      hideElement(spinner)
      showElement(container)
    }
  }

  function displayCrashpads (crashpads) {
    const container = document.getElementById('crashpads-list')
    const template = document.getElementById('crashpad-card-template')

    container.innerHTML = ''
    selectedCrashpads.clear()
    updateSelectionSummary()

    crashpads.forEach(crashpad => {
      const card = template.content.cloneNode(true)

      // Update image handling
      const mainImage = card.querySelector('.card-img-top')
      mainImage.src = crashpad.image || '/static/images/noimage.png'
      
      // Add gallery button handler
      const galleryBtn = card.querySelector('.gallery-btn')
      galleryBtn.addEventListener('click', (e) => {
        e.stopPropagation() // Prevent card selection
        showGallery(crashpad)
      })
      
      // Populate card data
      card.querySelector('.card-title').textContent = crashpad.name
      
      // Set up description and show more button
      const descriptionEl = card.querySelector('.description')
      const showMoreBtn = card.querySelector('.show-more-btn')
      descriptionEl.innerHTML = crashpad.description
      
      // Hide show more button if description is short
      if (crashpad.description.length <= 100) {
        showMoreBtn.style.display = 'none'
      } else {
        // Add click handler for show more button
        showMoreBtn.addEventListener('click', function(e) {
          e.stopPropagation() // Prevent card selection when clicking button
          const desc = this.previousElementSibling
          if (desc.classList.contains('truncated')) {
            desc.classList.remove('truncated')
            this.textContent = 'Show less'
          } else {
            desc.classList.add('truncated')
            this.textContent = 'Show more'
          }
        })
      }
      
      card.querySelector('.price').textContent = `€${crashpad.price_per_day}/day`

      const cardElement = card.querySelector('.crashpad-card')
      cardElement.dataset.crashpadId = crashpad.id

      // Add click handler for card selection
      cardElement.addEventListener('click', (e) => {
        // Only toggle selection if not clicking the show more button
        if (!e.target.classList.contains('show-more-btn')) {
          toggleCrashpadSelection(crashpad.id)
        }
      })

      container.appendChild(card)
    })
  }

  function toggleCrashpadSelection (crashpadId) {
    const card = document.querySelector(
      `.crashpad-card[data-crashpad-id="${crashpadId}"]`
    )
    const button = card.querySelector('.select-crashpad')

    if (selectedCrashpads.has(crashpadId)) {
      selectedCrashpads.delete(crashpadId)
      card.classList.remove('selected')
      button.textContent = 'Select'
      button.classList.remove('selected')
    } else {
      selectedCrashpads.add(crashpadId)
      card.classList.add('selected')
      button.classList.add('selected')
      button.textContent = 'Selected'
    }

    updateSelectionSummary()
  }

  function updateSelectionSummary () {
    const summary = document.getElementById('selection-summary')
    const count = document.getElementById('selected-count')

    if (selectedCrashpads.size > 0) {
      showElement(summary)
      count.textContent = `${selectedCrashpads.size} crashpad${
        selectedCrashpads.size > 1 ? 's' : ''
      } selected`
    } else {
      hideElement(summary)
    }
  }

  // Add to cart handler
  document.getElementById('add-to-cart').addEventListener('click', async () => {
    const dateRange = $('#daterange').data('daterangepicker')
    if (
      !dateRange.startDate ||
      !dateRange.endDate ||
      selectedCrashpads.size === 0
    ) {
      alert('Please select dates and at least one crashpad')
      return
    }

    // Here you'll integrate with your cart system
    console.log('Adding to cart:', {
      crashpad_ids: Array.from(selectedCrashpads),
      check_in: dateRange.startDate.format('YYYY-MM-DD'),
      check_out: dateRange.endDate.format('YYYY-MM-DD')
    })
  })

  function showGallery(crashpad) {
    const modal = new bootstrap.Modal(document.getElementById('galleryModal'))
    const carousel = document.querySelector('#galleryCarousel .carousel-inner')
    carousel.innerHTML = ''
    
    // Add main image
    const mainSlide = document.createElement('div')
    mainSlide.className = 'carousel-item active'
    mainSlide.innerHTML = `<img src="${crashpad.image}" class="d-block w-100" alt="${crashpad.name}">`
    carousel.appendChild(mainSlide)
    
    // Add gallery images
    crashpad.gallery_images?.forEach((image, index) => {
      const slide = document.createElement('div')
      slide.className = 'carousel-item'
      slide.innerHTML = `<img src="${image.image}" class="d-block w-100" alt="${crashpad.name} gallery image ${index + 1}">`
      carousel.appendChild(slide)
    })
    
    modal.show()
  }
})

function showElement (element) {
  element.classList.remove('hidden')
}

function hideElement (element) {
  element.classList.add('hidden')
}
