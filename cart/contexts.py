from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    return {
        'cart_item_count': len(cart),
        'cart_total_price': cart.cart_total(),
    }
