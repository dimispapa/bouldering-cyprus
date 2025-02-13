from decimal import Decimal
from .cart import Cart
from django.conf import settings


def cart_summary(request):
    cart = Cart(request)
    cart_items = [{
        "product":
        item["product"],
        "quantity":
        item["quantity"],
        "total_price":
        item["total_price"],
        "image_url":
        item["product"].image.url if item["product"].image else None,
    } for item in cart]

    cart_total = Decimal(str(cart.cart_total()))

    if cart_total < settings.FREE_DELIVERY_THRESHOLD:
        delivery_cost = Decimal(
            str(settings.STANDARD_DELIVERY_PERCENTAGE * cart_total / 100))
    else:
        delivery_cost = Decimal('0')
    grand_total = cart_total + delivery_cost

    return {
        "cart_items": cart_items,
        "cart_item_count": len(cart),
        "cart_total": cart_total,
        "delivery_cost": delivery_cost,
        "grand_total": grand_total,
        "free_delivery_threshold": settings.FREE_DELIVERY_THRESHOLD,
    }
