import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from shop.models import Product
from rentals.models import Crashpad
from .cart import Cart
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
import json

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, item_type):
    """Add a product or rental to the cart."""
    cart = Cart(request)

    try:
        if item_type == 'product':
            # Handle product addition
            product_id = int(request.POST.get('product_id'))
            quantity = int(request.POST.get('quantity', 1))
            product = get_object_or_404(Product, id=product_id)

            # Check stock availability
            current_qty = cart.cart.get(f"product_{product_id}",
                                        {}).get('quantity', 0)
            potential_total = current_qty + quantity

            if not product.has_stock(potential_total):
                logger.warning(
                    f'Product {product.name} has insufficient stock. '
                    f'User tried to add {quantity} units '
                    f'(cart has {current_qty}) - stock: {product.stock}')
                if product.stock == 0:
                    messages.error(request,
                                   f'Sorry, {product.name} is out of stock')
                else:
                    messages.error(
                        request,
                        f'Sorry, only {product.stock} units available '
                        f'for {product.name} (you have {current_qty} in cart)')
                return redirect('shop')

            cart.add(item=product, quantity=quantity, item_type='product')
            messages.success(request,
                             f"{product.name} was added to your cart.",
                             extra_tags="Cart updated")

        elif item_type == 'rental':
            # Handle rental addition
            data = json.loads(request.body)
            crashpad_ids = data.get('crashpad_ids', [])
            check_in = data.get('check_in')
            check_out = data.get('check_out')

            if not all([crashpad_ids, check_in, check_out]):
                return JsonResponse({'error': 'Missing required data'},
                                    status=400)

            for crashpad_id in crashpad_ids:
                crashpad = get_object_or_404(Crashpad, id=crashpad_id)
                cart.add(item=crashpad,
                         quantity=1,
                         item_type='rental',
                         dates={
                             'check_in': check_in,
                             'check_out': check_out
                         })

            messages.success(request,
                             "Crashpad(s) added to your cart.",
                             extra_tags="Cart updated")
            return JsonResponse({'status': 'success'})

        else:
            raise ValueError(f"Invalid item type: {item_type}")

    except Exception as e:
        logger.error(f"Error adding item to cart: {e}")
        if item_type == 'rental':
            return JsonResponse({'error': str(e)}, status=400)
        messages.error(request, "Error adding item to cart")
        return redirect('shop')

    return redirect('cart_detail')


@require_GET
def cart_remove(request, item_type, item_id):
    """Remove a product or rental from the cart."""
    cart = Cart(request)
    if item_type == 'product':
        item = get_object_or_404(Product, id=item_id)
    else:
        item = get_object_or_404(Crashpad, id=item_id)

    cart.remove(item, item_type)
    messages.success(
        request,
        f"{item.name} was removed from your cart.",
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
                item_type = item['type']
                item_id = item['item'].id
                input_name = f'quantity_{item_type}_{item_id}'
                new_qty = request.POST.get(input_name)

                # Skip rental items as they don't have editable quantities
                if item_type == 'rental':
                    continue

                if new_qty:
                    try:
                        new_qty = int(new_qty)
                        if new_qty > 0:
                            # Perform stock validation for products
                            if item_type == 'product':
                                product = get_object_or_404(Product,
                                                            id=item_id)
                                if not product.has_stock(new_qty):
                                    messages.error(
                                        request,
                                        f'Sorry, only {product.stock} '
                                        f'units available for {product.name}')
                                    update_successful = False
                                    continue
                            # Add the item to the cart with the new quantity
                            cart.add(item=item['item'],
                                     quantity=new_qty,
                                     update_quantity=True,
                                     item_type=item_type,
                                     dates=item.get('dates'))
                        # If the quantity is 0, remove the item from the cart
                        else:
                            cart.remove(item['item'], item_type)
                    except ValueError:
                        continue

            if update_successful:
                messages.success(
                    request,
                    "Your cart has been updated.",
                    extra_tags="Cart updated",
                )

        # If the action is to checkout, redirect to checkout
        elif action == "checkout":
            return redirect("checkout")

    return redirect("cart_detail")
