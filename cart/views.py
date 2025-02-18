import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from shop.models import Product
from .cart import Cart
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def cart_add(request, product_id):
    """Add a product to the cart."""
    # Initialize the cart
    cart = Cart(request)
    # Get the product added to the cart
    product = get_object_or_404(Product, id=product_id)
    # Get the post quantity
    quantity = int(request.POST.get('quantity', 1))

    # Calculate potential new total (current cart quantity + new quantity)
    # Get current quantity, default to 0 if product not in cart
    current_qty = cart.cart.get(str(product.id), {}).get('quantity', 0)
    potential_total = current_qty + quantity

    # Check if the potential total exceeds available stock
    if not product.has_stock(potential_total):
        logger.warning(f'Product {product.name} has insufficient stock. '
                       f'A user tried to add {quantity} units '
                       f'(cart already has {current_qty}) - '
                       f'available stock: {product.stock}')
        if product.stock == 0:
            messages.error(request, f'Sorry, {product.name} is out of stock')
        else:
            messages.error(
                request, f'Sorry, only {product.stock} units available '
                f'for {product.name} (you already have {current_qty} in cart)')
        return redirect('shop')

    # If stock check passes, add to cart
    cart.add(product=product, quantity=quantity)

    messages.success(
        request,
        f"{product.name} was added to your cart.",
        extra_tags="Cart updated",
    )
    return redirect('cart_detail')


@require_GET
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


@require_GET
def cart_detail(request):
    """Display the cart's contents."""
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})


def cart_update(request):
    """Process the cart to either update quantities or checkout."""
    cart = Cart(request)
    if request.method == "POST":
        # Determine which action was requested
        action = request.POST.get("action")

        # If the action is to update the cart, update the quantities
        if action == "update":
            update_successful = True
            # Loop over all items in the cart and update quantities
            for item in cart:
                # Construct the key name dynamically
                product = item["product"]
                input_name = f'quantity_{product.id}'
                new_qty = request.POST.get(input_name)
                if new_qty:
                    try:
                        new_qty = int(new_qty)
                    except ValueError:
                        continue

                    # Check if the quantity is greater than 0
                    if new_qty > 0:
                        # Check if the product has sufficient stock
                        if not product.has_stock(new_qty):
                            if product.stock == 0:
                                messages.error(
                                    request,
                                    f'Sorry, {product.name} is out of stock',
                                    extra_tags="Item not available",
                                )
                            else:
                                messages.error(
                                    request,
                                    f'Sorry, only {product.stock} units '
                                    f'available for {product.name}',
                                    extra_tags="Not enough stock",
                                )
                            update_successful = False
                            # If the quantity is not valid,
                            # continue to the next item
                            continue
                        # If the quantity is greater than 0, update the cart
                        cart.add(
                            product=product,
                            quantity=new_qty,
                            update_quantity=True,
                        )
                    # If the quantity is 0, remove the product from the cart
                    else:
                        cart.remove(product)
            # If the update was successful, show a success message
            if update_successful:
                messages.success(
                    request,
                    "Your cart has been updated.",
                    extra_tags="Cart updated",
                )

        # If the action is to checkout, redirect to checkout
        elif action == "checkout":
            return redirect("checkout")

        # Otherwise, stay on the cart page
        return redirect("cart_detail")

    # For GET requests, simply display the cart
    return render(request, "cart/cart_detail.html", {"cart": cart})
