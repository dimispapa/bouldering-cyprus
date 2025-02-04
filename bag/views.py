from django.shortcuts import render, get_object_or_404, redirect
from carton.cart import Cart
from shop.models import Product


def add_to_bag(request, product_id):
    """Add a product to the shopping cart"""
    # Get the product
    product = get_object_or_404(Product, id=product_id)
    # Add it to the cart
    cart = Cart(request.session)
    cart.add(product, price=product.price)

    # Redirect to the cart page
    return redirect("bag")


def bag(request):
    """Display the shopping cart"""
    cart = Cart(request.session)
    return render(request, "bag.html", {"cart": cart})
