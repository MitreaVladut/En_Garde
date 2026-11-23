from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Count, Sum

from .decorators import staff_required
from .forms import ProductForm, VariantForm, CategoryForm
from apps.catalog.models import Product, Variant, Category, ProductImage
from apps.orders.models import Order, StockReservation


@staff_required
def dashboard_view(request):
    """Admin dashboard overview."""
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status=Order.Status.PAID).aggregate(s=Sum('total'))['s'] or 0
    pending_orders = Order.objects.filter(status=Order.Status.NEW).count()
    products_count = Product.objects.count()
    low_stock_variants = Variant.objects.filter(stock__lte=3).select_related('product')[:8]

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'products_count': products_count,
        'low_stock_variants': low_stock_variants,
        'recent_orders': Order.objects.order_by('-created_at')[:6],
    }
    return render(request, 'manage/dashboard.html', context)


# === CATEGORY CRUD ===
@staff_required
def category_list_view(request):
    categories = Category.objects.annotate(p_count=Count('products')).order_by('name')
    return render(request, 'manage/category_list.html', {'categories': categories})


@staff_required
def category_create_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created.")
            return redirect('manage:category_list')
    else:
        form = CategoryForm()
    return render(request, 'manage/category_form.html', {'form': form, 'title': 'Create New Category'})


@staff_required
def category_update_view(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated.")
            return redirect('manage:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'manage/category_form.html', {'form': form, 'title': 'Edit Category', 'category': category})


@staff_required
@require_POST
def category_delete_view(request, id):
    category = get_object_or_404(Category, id=id)
    name = category.name
    category.delete()
    messages.info(request, f"Category '{name}' deleted.")
    return redirect('manage:category_list')


# === PRODUCT CRUD ===
@staff_required
def product_list_view(request):
    products = Product.objects.select_related('category').prefetch_related('variants').order_by('-created_at')
    return render(request, 'manage/product_list.html', {'products': products})


@staff_required
def product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created. You can now add variants.")
            return redirect('manage:product_update', id=product.id)
    else:
        form = ProductForm()
    return render(request, 'manage/product_form.html', {'form': form, 'title': 'Create New Product'})


@staff_required
def product_update_view(request, id):
    product = get_object_or_404(Product.objects.prefetch_related('variants', 'images'), id=id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated.")
            return redirect('manage:product_list')
    else:
        form = ProductForm(instance=product)

    variant_form = VariantForm()
    return render(request, 'manage/product_form.html', {
        'form': form,
        'title': f"Edit Product: {product.name}",
        'product': product,
        'variant_form': variant_form,
    })


@staff_required
@require_POST
def product_delete_view(request, id):
    product = get_object_or_404(Product, id=id)
    name = product.name
    product.delete()
    messages.info(request, f"Product '{name}' deleted.")
    return redirect('manage:product_list')


# === VARIANT CRUD ===
@staff_required
@require_POST
def variant_create_view(request, id):
    product = get_object_or_404(Product, id=id)
    form = VariantForm(request.POST)
    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        variant.save()
        messages.success(request, f"Variant '{variant.sku}' added.")
    else:
        messages.error(request, "Failed to create variant. Check fields.")
    return redirect('manage:product_update', id=product.id)


@staff_required
def variant_update_view(request, id, vid):
    product = get_object_or_404(Product, id=id)
    variant = get_object_or_404(Variant, id=vid, product=product)
    if request.method == 'POST':
        form = VariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Variant '{variant.sku}' updated.")
            return redirect('manage:product_update', id=product.id)
    else:
        form = VariantForm(instance=variant)
    return render(request, 'manage/variant_form.html', {'form': form, 'product': product, 'variant': variant})


@staff_required
@require_POST
def variant_delete_view(request, id, vid):
    product = get_object_or_404(Product, id=id)
    variant = get_object_or_404(Variant, id=vid, product=product)
    variant.delete()
    messages.info(request, f"Variant '{variant.sku}' deleted.")
    return redirect('manage:product_update', id=product.id)


# === ORDERS MANAGEMENT ===
@staff_required
def order_list_view(request):
    """
    Requirement A9: order list filterable by status with transitions
    New -> Paid -> Shipped -> Delivered, or Cancelled.
    """
    status_filter = request.GET.get('status')
    orders = Order.objects.select_related('user', 'delivery_method').order_by('-created_at')

    if status_filter and status_filter != 'All':
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'current_status': status_filter or 'All',
        'status_choices': ['All'] + [c[0] for c in Order.Status.choices],
    }
    return render(request, 'manage/order_list.html', context)


@staff_required
def order_detail_view(request, number):
    order = get_object_or_404(
        Order.objects.select_related('user', 'delivery_method', 'discount_code').prefetch_related('items'),
        number=number
    )
    return render(request, 'manage/order_detail.html', {'order': order})


@staff_required
@require_POST
def order_status_update_view(request, number):
    """
    Changes order status enforcing allowed transitions (Requirement A9):
    New -> Paid (webhook only)
    Paid -> Shipped -> Delivered
    New or Paid -> Cancelled
    If order is cancelled, restores stock and releases reservations (Rule 5.5).
    """
    order = get_object_or_404(Order, number=number)
    target_status = request.POST.get('status')

    # Guard: Paid transition is webhook only (specification rule 5.3)
    if target_status == Order.Status.PAID:
        messages.error(request, "Transition to 'Paid' is restricted to signature-verified Stripe webhooks.")
        return redirect('manage:order_list')

    if not order.can_transition_to(target_status):
        messages.error(request, f"Transition from '{order.status}' to '{target_status}' is not allowed.")
        return redirect('manage:order_list')

    with transaction.atomic():
        old_status = order.status
        order.status = target_status
        order.save()

        # If cancelled, restore stock and release reservation (Rule 5.5)
        if target_status == Order.Status.CANCELLED:
            if old_status == Order.Status.PAID:
                # Add stock back for completed order items
                for item in order.items.all():
                    if item.variant_id:
                        Variant.objects.filter(id=item.variant_id).update(
                            stock=models.F('stock') + item.quantity
                        )
            # Release reservations
            order.reservations.filter(state='active').update(state='released')
            messages.info(request, f"Order #{order.number} cancelled. Stock and reservations restored.")
        else:
            messages.success(request, f"Order #{order.number} status updated to '{target_status}'.")

    return redirect('manage:order_list')
