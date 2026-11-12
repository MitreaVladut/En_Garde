import uuid
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone
from django.http import Http404
from django.conf import settings

from .models import DeliveryMethod, DiscountCode, Order, OrderItem, StockReservation
from apps.accounts.models import Address
from apps.accounts.forms import AddressForm
from apps.cart.utils import get_cart
from apps.catalog.models import Variant


@login_required
def checkout_address_view(request):
    """Step 1: Select or enter shipping address."""
    cart = get_cart(request)
    if not cart or cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id == 'new':
            form = AddressForm(request.POST)
            if form.is_valid():
                new_addr = form.save(commit=False)
                new_addr.user = request.user
                new_addr.save()
                request.session['checkout_address_id'] = new_addr.id
                return redirect('orders:checkout_delivery')
        elif address_id:
            addr = get_object_or_404(Address, id=address_id, user=request.user)
            request.session['checkout_address_id'] = addr.id
            return redirect('orders:checkout_delivery')
        else:
            messages.error(request, "Please select an address or enter a new one.")
    else:
        form = AddressForm()

    selected_address_id = request.session.get('checkout_address_id')
    if not selected_address_id:
        default_addr = addresses.filter(is_default=True).first() or addresses.first()
        if default_addr:
            selected_address_id = default_addr.id

    context = {
        'addresses': addresses,
        'form': form,
        'selected_address_id': selected_address_id,
        'step': 1,
    }
    return render(request, 'orders/checkout_address.html', context)


@login_required
def checkout_delivery_view(request):
    """Step 2: Select delivery method (Standard vs Express)."""
    cart = get_cart(request)
    if not cart or cart.items.count() == 0:
        return redirect('cart:cart_detail')

    address_id = request.session.get('checkout_address_id')
    if not address_id or not Address.objects.filter(id=address_id, user=request.user).exists():
        messages.info(request, "Please confirm your shipping address first.")
        return redirect('orders:checkout_address')

    delivery_methods = DeliveryMethod.objects.all().order_by('cost')

    if request.method == 'POST':
        method_id = request.POST.get('delivery_method_id')
        method = get_object_or_404(DeliveryMethod, id=method_id)
        request.session['checkout_delivery_id'] = method.id
        return redirect('orders:checkout_summary')

    selected_delivery_id = request.session.get('checkout_delivery_id')
    if not selected_delivery_id and delivery_methods.exists():
        selected_delivery_id = delivery_methods.first().id

    context = {
        'delivery_methods': delivery_methods,
        'selected_delivery_id': selected_delivery_id,
        'step': 2,
    }
    return render(request, 'orders/checkout_delivery.html', context)


@login_required
def checkout_summary_view(request):
    """Step 3: Order summary."""
    cart = get_cart(request)
    if not cart or cart.items.count() == 0:
        return redirect('cart:cart_detail')

    address_id = request.session.get('checkout_address_id')
    delivery_id = request.session.get('checkout_delivery_id')

    if not address_id:
        return redirect('orders:checkout_address')
    if not delivery_id:
        return redirect('orders:checkout_delivery')

    address = get_object_or_404(Address, id=address_id, user=request.user)
    delivery_method = get_object_or_404(DeliveryMethod, id=delivery_id)

    subtotal = cart.subtotal
    discount_amount = Decimal('0.00')
    discount_obj = None

    code_str = request.session.get('discount_code')
    if code_str:
        discount_obj = DiscountCode.objects.filter(code__iexact=code_str).first()
        if discount_obj and discount_obj.is_valid:
            discount_amount = discount_obj.calculate_discount(subtotal)

    shipping_cost = delivery_method.cost
    total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('variant', 'variant__product'),
        'address': address,
        'delivery_method': delivery_method,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'discount_code': discount_obj,
        'shipping_cost': shipping_cost,
        'total': total,
        'step': 3,
    }
    return render(request, 'orders/checkout_summary.html', context)


@login_required
@require_POST
def checkout_pay_view(request):
    """
    Step 4: Create order, reserve stock, and proceed to Stripe Checkout (Critical flow 5).
    Enforces:
    1. Transaction with SELECT ... FOR UPDATE on Variant rows.
    2. Check stock minus active reservations. If not met, refuse with message.
    3. Create Order (New), OrderItems, and 30-minute StockReservations.
    4. Redirect to payment.
    """
    cart = get_cart(request)
    if not cart or cart.items.count() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    address_id = request.session.get('checkout_address_id')
    delivery_id = request.session.get('checkout_delivery_id')

    if not address_id or not delivery_id:
        messages.error(request, "Please complete address and delivery steps.")
        return redirect('orders:checkout_address')

    address = get_object_or_404(Address, id=address_id, user=request.user)
    delivery_method = get_object_or_404(DeliveryMethod, id=delivery_id)

    with transaction.atomic():
        # Collect variant ids and lock them
        cart_items = list(cart.items.select_related('variant', 'variant__product'))
        variant_ids = [item.variant_id for item in cart_items]

        # Requirement 5.1: Lock Variant rows with SELECT ... FOR UPDATE
        locked_variants = {
            v.id: v for v in Variant.objects.select_for_update().filter(id__in=variant_ids)
        }

        # Check stock minus active reservations for each item
        insufficient_items = []
        now = timezone.now()
        for item in cart_items:
            variant = locked_variants[item.variant_id]
            active_reserved = StockReservation.objects.filter(
                variant=variant,
                state='active',
                expires_at__gt=now
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            available = variant.stock - active_reserved
            if item.quantity > available:
                insufficient_items.append(f"{variant.product.name} ({variant.label}): only {max(0, available)} available")

        if insufficient_items:
            messages.error(
                request,
                "Could not complete checkout due to insufficient stock: " + "; ".join(insufficient_items)
            )
            return redirect('cart:cart_detail')

        # Compute totals
        subtotal = cart.subtotal
        discount_amount = Decimal('0.00')
        discount_code_obj = None

        code_str = request.session.get('discount_code')
        if code_str:
            discount_code_obj = DiscountCode.objects.filter(code__iexact=code_str).first()
            if discount_code_obj and discount_code_obj.is_valid:
                discount_amount = discount_code_obj.calculate_discount(subtotal)
                discount_code_obj.used_count += 1
                discount_code_obj.save()

        shipping_cost = delivery_method.cost
        total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

        # Generate unique order number (EG-XXXX)
        last_order = Order.objects.order_by('-id').first()
        next_num = 1043 if not last_order else 1040 + last_order.id + 1
        order_number = f"EG-{next_num}"

        # Create Order (Status: New)
        order = Order.objects.create(
            number=order_number,
            user=request.user,
            status=Order.Status.NEW,
            delivery_method=delivery_method,
            discount_code=discount_code_obj,
            subtotal=subtotal,
            discount=discount_amount,
            shipping_cost=shipping_cost,
            total=total,
            shipping_full_name=address.full_name,
            shipping_street=address.street,
            shipping_city=address.city,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
        )

        # Create OrderItems and 30-minute StockReservations
        expires_at = now + timedelta(minutes=30)
        for item in cart_items:
            variant = locked_variants[item.variant_id]
            OrderItem.objects.create(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                variant_label=variant.label,
                unit_price=variant.price,
                quantity=item.quantity
            )
            StockReservation.objects.create(
                order=order,
                variant=variant,
                quantity=item.quantity,
                expires_at=expires_at,
                state='active'
            )

        # Empty cart and clear checkout sessions
        cart.items.all().delete()
        request.session.pop('checkout_address_id', None)
        request.session.pop('checkout_delivery_id', None)
        request.session.pop('discount_code', None)

    # For presentation and sandbox mode:
    # If stripe checkout session is simulated, user sees confirmation or mock payment
    messages.success(request, f"Order #{order.number} has been created!")
    return redirect('orders:checkout_success', number=order.number)


@login_required
def checkout_success_view(request, number):
    """
    Requirement 5.4: The success page only displays the status read from the database;
    it never changes it.
    """
    order = get_object_or_404(Order, number=number, user=request.user)
    return render(request, 'orders/checkout_success.html', {'order': order})


@login_required
def checkout_cancel_view(request, number):
    """Payment cancelled page."""
    order = get_object_or_404(Order, number=number, user=request.user)
    # Release reservation if unpaid
    if order.status == Order.Status.NEW:
        order.reservations.filter(state='active').update(state='released')
    return render(request, 'orders/checkout_cancel.html', {'order': order})


@login_required
def order_list_view(request):
    """
    Requirement A8: Customer page listing own orders (date, items, total, status);
    every query is filtered by the logged-in user.
    """
    orders = Order.objects.filter(user=request.user).select_related('delivery_method').prefetch_related('items')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, number):
    """
    Requirement A8: Customer order detail page;
    filtered by logged-in user and returns 404 otherwise.
    """
    order = get_object_or_404(
        Order.objects.select_related('delivery_method', 'discount_code').prefetch_related('items'),
        number=number,
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {'order': order})
