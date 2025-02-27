document.addEventListener('DOMContentLoaded', () => {
  // Retrieve the Stripe public key and client secret from the hidden input
  const stripePublicKey = document.getElementById('stripe-public-key').value
  const clientSecret = document.getElementById('stripe-client-secret').value

  // Initialize Stripe and Elements
  const { stripe, elements } = initStripe(stripePublicKey, clientSecret)

  // Handle the submit button
  document
    .getElementById('payment-form')
    .addEventListener('submit', async e => {
      await handleSubmit(e, stripe, elements)
    })
})

// Function to initialize Stripe and Elements
function initStripe(stripePublicKey, clientSecret) {
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
  const expressCheckoutElement = elements.create(
    'expressCheckout',
    expressCheckoutOptions
  )
  expressCheckoutElement.mount('#express-checkout-element')

  return { stripe, elements}
}

// Function to handle the submit button and payment processing workflow
async function handleSubmit(e, stripe, elements) {
  e.preventDefault();
  const form = e.target;
  setLoading(true);

  try {
    // Get the form data
    const formData = new FormData(form);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Store form data in PaymentIntent metadata
    const response = await fetch('/payments/store-order-metadata/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrfToken,
      }
    });

    if (!response.ok) {
      throw new Error('Failed to store order data');
    }

    // Construct absolute URL for return_url
    const returnUrl = new URL('/payments/checkout-success/', window.location.href).href;

    // Proceed with payment confirmation
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: returnUrl,
      },
    });

    if (error) {
      showError(error.message);
    }
    // Note: No need for form submission here as Stripe will handle the redirect

  } catch (err) {
    console.error('Error:', err);
    showError('An error occurred. Please try again.');
  } finally {
    setLoading(false);
  }
}

// Show an error message
function showError (messageText) {
  // Get the error message element
  const paymentErrors = document.getElementById('payment-errors')

  // Update the payment errors with the new message
  paymentErrors.classList.remove('hidden')
  paymentErrors.textContent = messageText

  // Hide the payment errors after 4 seconds
  setTimeout(function () {
    paymentErrors.classList.add('hidden')
    paymentErrors.textContent = ''
  }, 10000)
}

// Set the loading state
function setLoading (isLoading) {
  const submitButton = document.getElementById('submit')
  const buttonText = document.getElementById('button-text')
  const spinner = document.getElementById('spinner')

  if (isLoading) {
    submitButton.disabled = true
    buttonText.textContent = 'Processing...'
    spinner.classList.remove('hidden')
  } else {
    submitButton.disabled = false
    buttonText.textContent = 'Place order'
    spinner.classList.add('hidden')
  }
}
