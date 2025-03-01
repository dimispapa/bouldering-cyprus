from .cart import Cart
from django.conf import settings
from decimal import Decimal


def cart_summary(request):
    cart = Cart(request)
    cart_items = [{
        "item":
        item["item"],
        "quantity":
        item["quantity"],
        "total_price":
        item["total_price"],
        "type":
        item["type"],
        "image_url":
        item["item"].image.url if item["item"].image else None,
        "dates":
        item.get("dates", None),
        "check_in":
        item.get("check_in"),
        "check_out":
        item.get("check_out"),
        "rental_days":
        item.get("rental_days"),
        "daily_rate":
        item.get("daily_rate"),
    } for item in cart]

    cart_total = cart.cart_total()

    # Determine order type
    has_products = cart.has_products()
    has_rentals = cart.has_rentals()

    if has_products and has_rentals:
        order_type = 'MIXED'
    elif has_products:
        order_type = 'PRODUCTS_ONLY'
    elif has_rentals:
        order_type = 'RENTALS_ONLY'
    else:
        order_type = None

    # Calculate delivery cost only if there are products
    delivery_cost = Decimal('0')
    if has_products:
        if cart_total < settings.FREE_DELIVERY_THRESHOLD:
            delivery_cost = (Decimal(settings.STANDARD_DELIVERY_PERCENTAGE) *
                             cart_total / Decimal('100'))
        else:
            delivery_cost = Decimal('0')

    # Add handling fee if there are rentals
    handling_fee = Decimal(str(
        settings.RENTAL_HANDLING_FEE)) if has_rentals else Decimal('0')

    # Calculate subtotals
    product_items_sum = sum(item["total_price"] for item in cart_items
                            if item["type"] == "product")
    rental_items_sum = sum(item["total_price"] for item in cart_items
                           if item["type"] == "rental")
    product_items_subtotal = product_items_sum + delivery_cost
    rental_items_subtotal = rental_items_sum + handling_fee

    # Calculate grand total
    grand_total = cart_total + delivery_cost + handling_fee

    return {
        "cart_items": cart_items,
        "cart_item_count": len(cart),
        "cart_total": cart_total,
        "delivery_cost": delivery_cost,
        "handling_fee": handling_fee,
        "grand_total": grand_total,
        "product_items_sum": product_items_sum,
        "product_items_subtotal": product_items_subtotal,
        "rental_items_sum": rental_items_sum,
        "rental_items_subtotal": rental_items_subtotal,
        "free_delivery_threshold": settings.FREE_DELIVERY_THRESHOLD,
        "order_type": order_type,
        "has_products": has_products,
        "has_rentals": has_rentals,
        "contact_email": settings.DEFAULT_FROM_EMAIL,
        "whatsapp_number": settings.WHATSAPP_NUMBER,
        "crashpad_pickup_address": settings.CRASHPAD_PICKUP_ADDRESS,
    }
