document.addEventListener('DOMContentLoaded', function () {
  const footerForm = document.getElementById('footer-newsletter-form')

  if (footerForm) {
    footerForm.addEventListener('submit', function (e) {
      e.preventDefault()

      const messageDiv = document.getElementById('newsletter-message')
      const formData = new FormData(footerForm)

      fetch(footerForm.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            messageDiv.innerHTML = `<div class="text-success">${data.message}</div>`
            footerForm.reset()
          } else {
            if (data.errors) {
              let errorMsg = ''
              for (const [key, value] of Object.entries(data.errors)) {
                errorMsg += `${value}<br>`
              }
              messageDiv.innerHTML = `<div class="text-danger">${errorMsg}</div>`
            } else {
              messageDiv.innerHTML = `<div class="text-danger">${data.message}</div>`
            }
          }
        })
        .catch(error => {
          messageDiv.innerHTML =
            '<div class="text-danger">An error occurred. Please try again.</div>'
          console.error('Error:', error)
        })
    })
  }
})
