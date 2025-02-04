from carton.cart import Cart


def cart_item_count(request):
    cart = Cart(request.session)
    return {'cart_item_count': len(cart)}
