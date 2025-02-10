import stripe
from django.urls import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from orders.forms import OrderForm
from cart.cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(cart):
    try:
        # Calculate the total amount
        stripe_total = round(cart.cart_total() * 100)
        print(stripe_total)
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
    intent = create_payment_intent(cart)

    # Render the checkout page with cart and order form objects
    context = {
        "cart": cart,
        "order_form": OrderForm(
            stripe_public_key=settings.STRIPE_PUBLIC_KEY,
            stripe_client_secret=intent.client_secret,
        ),
    }
    return render(request, "payments/checkout.html", context)


def checkout_success(request):
    """Handle the checkout success process."""
    return render(request, "payments/checkout_success.html")
