from django.shortcuts import render, get_object_or_404, redirect
from shop.models import Product
from .cart import Cart


def cart_add(request, product_id):
    """Add a product to the cart."""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    # Use quantity=1 for now, but you can add a quantity form to the template
    cart.add(product=product, quantity=1, update_quantity=False)
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
