from django.shortcuts import render, get_object_or_404, redirect
from shop.models import Product
from .cart import Cart


def cart_add(request, product_id):
    """Add a product to the cart."""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity"))
        except ValueError:
            quantity = 1
        cart.add(product=product, quantity=quantity)
    return redirect("cart_detail")


def cart_remove(request, product_id):
    """Remove a product from the cart."""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return redirect("cart_detail")


def cart_detail(request):
    """Display the cart's contents."""
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart})
