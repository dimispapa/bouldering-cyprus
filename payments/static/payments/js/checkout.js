document.addEventListener('DOMContentLoaded', () => {
  // Retrieve the Stripe public key and client secret from the hidden input
  const stripePublicKey = document.getElementById('stripe-public-key').value
  const clientSecret = document.getElementById('stripe-client-secret').value

  // Initialize Stripe with your public key
  const stripe = Stripe(stripePublicKey)

  // Initialize Elements with appearance and client secret
  const appearance = {
    theme: 'stripe'
  }
  let elements = stripe.elements({ appearance, clientSecret })

  // Create a Payment Element
  const paymentElementOptions = {
    layout: 'tabs'
  }
  const paymentElement = elements.create('payment', paymentElementOptions)
  paymentElement.mount('#payment-element')

  // Create an Express Checkout Element
  const expressCheckoutOptions = {}
  const expressCheckoutElement = elements.create('expressCheckout', expressCheckoutOptions)
  expressCheckoutElement.mount('#express-checkout-element')

  // Handle the submit button
  document
    .querySelector("#payment-form")
    .addEventListener("submit", async (e) => {
      // Get the client secret from the hidden input
      const clientSecret = document.getElementById('stripe-client-secret').value;
      await handleSubmit(e, clientSecret);
    });
});

// Function to handle the submit button and payment processing workflow
async function handleSubmit(e, clientSecret) {
  e.preventDefault();
  const baseUrl = window.location.origin;
  setLoading(true);

  // Get the form data
  const form = document.getElementById('payment-form');
  const formData = new FormData(form);

  try {
    // Store form data in session
    const response = await fetch('/checkout/store-form/', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to store form data');
    }

    // Proceed with payment
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${baseUrl}/payments/checkout/success/?payment_intent_client_secret=${clientSecret}`,
      },
    });

    if (error) {
      showError(error.message);
    }
  } catch (err) {
    showError('An error occurred. Please try again.');
  } finally {
    setLoading(false);
  }
}

// Show an error message
function showError(messageText) {
  // Get the existing toast element
  const toastElement = document.querySelector('.toast');
  const paymentErrors = document.getElementById('payment-errors');
  
  // Update the toast body with the new message
  const toastBody = toastElement.querySelector('.toast-body');
  toastBody.textContent = messageText;
  
  // Update the payment errors with the new message
  paymentErrors.classList.remove('hidden');
  paymentErrors.textContent = messageText;

  // Hide the payment errors after 4 seconds
  setTimeout(function () {
    paymentErrors.classList.add("hidden");
    paymentErrors.textContent = "";
  }, 10000);
  
  // Get the existing Bootstrap toast instance
  const toast = bootstrap.Toast.getInstance(toastElement);
  if (toast) {
    toast.show();
  }
}

// Set the loading state
function setLoading(isLoading) {
  const submitButton = document.getElementById('submit');
  const buttonText = document.getElementById('button-text');
  const spinner = document.getElementById('spinner');

  if (isLoading) {
    submitButton.disabled = true;
    buttonText.textContent = 'Processing...';
    spinner.classList.remove('hidden');
  } else {
    submitButton.disabled = false;
    buttonText.textContent = 'Place order';
    spinner.classList.add('hidden');
  }
}