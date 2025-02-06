from django.shortcuts import render
from cart.cart import Cart


def checkout(request):
    """Handle the checkout process."""
    cart = Cart(request)
    return render(request, "payments/checkout_shop.html", {"cart": cart})
