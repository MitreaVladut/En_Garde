from .models import Cart, CartItem


def get_cart(request):
    """Retrieve existing cart for authenticated user or anonymous session, or None."""
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key).first()


def get_or_create_cart(request):
    """Retrieve or create cart for authenticated user or anonymous session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def merge_guest_cart(request, user, old_session_key=None):
    """
    Merges a guest session cart into the user's permanent cart upon login (Requirement A3).
    Ensures quantities do not exceed available stock and persists after logout.
    """
    session_key = old_session_key or request.session.session_key
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in guest_cart.items.all():
        available = item.variant.get_available_stock()
        existing_item = user_cart.items.filter(variant=item.variant).first()
        if existing_item:
            new_qty = min(existing_item.quantity + item.quantity, available)
            if new_qty > 0:
                existing_item.quantity = new_qty
                existing_item.save()
            item.delete()
        else:
            if available > 0:
                item.quantity = min(item.quantity, available)
                item.cart = user_cart
                item.save()
            else:
                item.delete()

    guest_cart.delete()
