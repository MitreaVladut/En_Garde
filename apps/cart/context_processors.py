from .utils import get_cart


def cart_context(request):
    cart = get_cart(request)
    cart_count = cart.total_items if cart else 0
    return {
        'cart_count': cart_count,
        'current_cart': cart,
    }
