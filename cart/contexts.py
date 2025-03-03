from .cart import Cart
from django.conf import settings
from decimal import Decimal
from shop.models import Product
from rentals.models import Crashpad


def cart_summary(request):
    cart = Cart(request)

    # Prefetch product and crashpad objects to avoid N+1 queries
    product_ids = []
    crashpad_ids = []

    # First pass: collect all IDs
    for item in cart:
        if item.get("type") == "product" and "product_id" in item:
            product_ids.append(item["product_id"])
        elif item.get("type") == "rental" and "crashpad_id" in item:
            crashpad_ids.append(item["crashpad_id"])

    # Fetch all products and crashpads in bulk
    products = {}
    crashpads = {}

    if product_ids:
        products = {
            p.id: p
            for p in Product.objects.filter(
                id__in=product_ids).prefetch_related('gallery_images')
        }

    if crashpad_ids:
        crashpads = {
            cp.id: cp
            for cp in Crashpad.objects.filter(
                id__in=crashpad_ids).prefetch_related('gallery_images')
        }

    # Second pass: create cart items with prefetched objects
    cart_items = []
    for item in cart:
        item_type = item.get("type")
        item_obj = None

        # Use the prefetched objects
        if item_type == "product" and "product_id" in item and item[
                "product_id"] in products:
            item_obj = products[item["product_id"]]
        elif item_type == "rental" and "crashpad_id" in item and item[
                "crashpad_id"] in crashpads:
            item_obj = crashpads[item["crashpad_id"]]
        else:
            # If we can't find the object in our prefetched dictionaries,
            # use the original
            item_obj = item.get("item")

        # Create the cart item dictionary
        cart_item = {
            "item":
            item_obj,
            "quantity":
            item["quantity"],
            "total_price":
            item["total_price"],
            "type":
            item_type,
            "image_url":
            item_obj.image.url if item_obj and hasattr(item_obj, 'image')
            and item_obj.image else None,
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
        }
        cart_items.append(cart_item)

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
