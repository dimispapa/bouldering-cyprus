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
})
