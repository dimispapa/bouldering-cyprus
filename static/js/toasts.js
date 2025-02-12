document.addEventListener('DOMContentLoaded', function () {
  const toastElList = document.querySelectorAll('.toast')
  const option = {animation: true, autohide: true, delay: 10000}
  const toastList = [...toastElList].map(toastEl =>
    new bootstrap.Toast(toastEl, option).show()
  )
})
