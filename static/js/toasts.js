document.addEventListener("DOMContentLoaded", function () {
  const toastElList = document.querySelectorAll(".toast");
  const option = { animation: true, autohide: true, delay: 10000 };
  const toastList = [...toastElList].map((toastEl) => new bootstrap.Toast(toastEl, option).show());
});

export function showToast({ title, message, icon = "info" }) {
  // Create the toast HTML
  const toastHtml = `
      <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
              <i class="fas fa-${icon} me-2"></i>
              <strong class="me-auto">${title}</strong>
              <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
          <div class="toast-body">
              ${message}
          </div>
      </div>
  `;

  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector(".toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container position-fixed top-0 end-0 p-3";
    document.body.appendChild(toastContainer);
  }

  // Add the new toast to the container
  toastContainer.insertAdjacentHTML("beforeend", toastHtml);

  // Initialize and show the toast
  const toastElement = toastContainer.lastElementChild;
  const toast = new bootstrap.Toast(toastElement);
  toast.show();

  // Remove toast from DOM after it's hidden
  toastElement.addEventListener("hidden.bs.toast", () => {
    toastElement.remove();
  });
}
