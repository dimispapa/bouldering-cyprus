from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
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
        messages.success(
            request,
            f"{product.name} was added to your cart.",
            extra_tags="Cart updated",
        )
    return redirect("cart_detail")


def cart_remove(request, product_id):
    """Remove a product from the cart."""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.success(
        request,
        f"{product.name} was removed from your cart.",
        extra_tags="Cart updated",
    )
    return redirect("cart_detail")


def cart_detail(request):
    """Display the cart's contents."""
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart})


def cart_update(request):
    """Process the cart to either update quantities or checkout."""
    cart = Cart(request)
    if request.method == "POST":
        # Loop over all items in the cart and update quantities
        for item in cart:
            # Construct the key name dynamically
            input_name = f'quantity_{item["product"].id}'
            new_qty = request.POST.get(input_name)
            if new_qty:
                try:
                    new_qty = int(new_qty)
                except ValueError:
                    new_qty = item["quantity"]
                # Update the quantity; remove if new_qty == 0
                if new_qty > 0:
                    cart.add(
                        product=item["product"], quantity=new_qty, update_quantity=True
                    )
                else:
                    cart.remove(item["product"])
                messages.success(
                    request, "Your cart has been updated.", extra_tags="Cart updated"
                )
        # Determine which action was requested
        action = request.POST.get("action")
        if action == "checkout":
            # Redirect to checkout
            return redirect("checkout")
        # Otherwise, stay on the cart page
        return redirect("cart_detail")
    # For GET requests, simply display the cart
    return render(request, "cart/detail.html", {"cart": cart})
