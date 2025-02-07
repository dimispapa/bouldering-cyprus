import stripe
from django.urls import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from cart.cart import Cart

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


def create_payment_intent(request, cart):
    try:
        # Calculate the total amount
        stripe_total = round(cart.get_total_price() * 100)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )
        return intent
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=403)


def checkout(request):
    """Handle the checkout process."""
    # Check if the cart is empty
    cart = Cart(request)
    if not len(cart):
        messages.error(request, "Your cart is empty.")
        return redirect(reverse("cart_detail"))

    # Create a PaymentIntent
    intent = create_payment_intent(request, cart)
    # Render the checkout page
    context = {
        "cart": cart,
        "stripe_public_key": settings.STRIPE_TEST_PUBLIC_KEY,
        "stripe_client_secret": intent.client_secret,
    }
    return render(request, "payments/checkout.html", context)
