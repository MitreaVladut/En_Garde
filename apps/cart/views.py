from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Cart, CartItem
from .utils import get_cart, get_or_create_cart
from apps.catalog.models import Variant
from apps.orders.models import DiscountCode


def cart_detail_view(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related('variant', 'variant__product').prefetch_related('variant__product__images') if cart else []

    subtotal = cart.subtotal if cart else Decimal('0.00')
    discount_amount = Decimal('0.00')
    applied_discount = None

    discount_code_str = request.session.get('discount_code')
    if discount_code_str and subtotal > 0:
        applied_discount = DiscountCode.objects.filter(code__iexact=discount_code_str).first()
        if applied_discount and applied_discount.is_valid:
            discount_amount = applied_discount.calculate_discount(subtotal)
        else:
            request.session.pop('discount_code', None)
            applied_discount = None

    total = max(Decimal('0.00'), subtotal - discount_amount)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'applied_discount': applied_discount,
        'total': total,
    }
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def cart_add_view(request):
    variant_id = request.POST.get('variant_id')
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    variant = get_object_or_404(Variant, id=variant_id)
    available_stock = variant.get_available_stock()

    cart = get_or_create_cart(request)
    cart_item, created = cart.items.get_or_create(variant=variant, defaults={'quantity': 0})

    new_quantity = cart_item.quantity + quantity

    # Requirement A3: quantities above available stock are rejected
    if new_quantity > available_stock:
        messages.error(
            request,
            f"Cannot add {quantity} of {variant.product.name} ({variant.label}). Only {available_stock} currently available in stock."
        )
        if created:
            cart_item.delete()
        return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))

    cart_item.quantity = new_quantity
    cart_item.save()

    messages.success(request, f"Added {variant.product.name} ({variant.label}) to your cart.")
    return redirect('cart:cart_detail')


@require_POST
def cart_update_view(request, item_id):
    cart = get_cart(request)
    if not cart:
        return redirect('cart:cart_detail')

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get('action')
    available_stock = cart_item.variant.get_available_stock()

    if action == 'increase':
        if cart_item.quantity + 1 > available_stock:
            messages.warning(request, f"Cannot add more. Only {available_stock} available in stock.")
        else:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
    elif 'quantity' in request.POST:
        try:
            qty = int(request.POST.get('quantity'))
            if qty <= 0:
                cart_item.delete()
                messages.info(request, "Item removed from cart.")
            elif qty > available_stock:
                messages.warning(request, f"Requested quantity exceeds available stock ({available_stock}). Set to maximum available.")
                cart_item.quantity = available_stock
                cart_item.save()
            else:
                cart_item.quantity = qty
                cart_item.save()
        except (ValueError, TypeError):
            pass

    return redirect('cart:cart_detail')


@require_POST
def cart_remove_view(request, item_id):
    cart = get_cart(request)
    if cart:
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        messages.info(request, "Item removed from cart.")
    return redirect('cart:cart_detail')


@require_POST
def cart_discount_view(request):
    # Requirement B5: Discount codes with expiry and max uses, validated on server
    code = request.POST.get('code', '').strip().upper()
    if not code:
        request.session.pop('discount_code', None)
        messages.info(request, "Discount code removed.")
        return redirect('cart:cart_detail')

    discount = DiscountCode.objects.filter(code__iexact=code).first()
    if discount and discount.is_valid:
        request.session['discount_code'] = discount.code
        messages.success(request, f"Discount code '{discount.code}' applied!")
    else:
        request.session.pop('discount_code', None)
        messages.error(request, f"Invalid or expired discount code '{code}'.")

    return redirect('cart:cart_detail')
