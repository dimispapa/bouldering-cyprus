from django.shortcuts import redirect
from django.contrib import messages
from datetime import datetime
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def validate_item_stock(item, request=None):
    """
    Validate items in the cart.
    """
    # Validate product
    if item['type'] == 'product':
        product = item['item']
        quantity = item['quantity']
        if not product.has_stock(quantity):
            logger.error(f"Insufficient stock for product {product.id}")
            # If request, return error message and redirect
            if request:
                messages.error(
                    request,
                    f"Sorry, only {product.stock} units available for "
                    f"{product.name}")
                return redirect("cart_detail")
            # If no request, return JSON response
            else:
                return JsonResponse(
                    {'error': 'Some items are no longer available'},
                    status=400)

    # Validate rental
    elif item['type'] == 'rental':
        crashpad = item['item']
        check_in = datetime.strptime(item['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(item['check_out'], '%Y-%m-%d').date()
        if not crashpad.is_available(check_in, check_out):
            logger.error(f"Crashpad {crashpad.id} no longer available")
            # If request, return error message and redirect
            if request:
                messages.error(
                    request,
                    f"Sorry, {crashpad.name} is no longer available for "
                    f"the selected dates")
                return redirect("cart_detail")
            # If no request, return JSON response
            else:
                return JsonResponse(
                    {'error': 'Selected rental dates are no longer available'},
                    status=400)
