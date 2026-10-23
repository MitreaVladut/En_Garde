import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, View
from django.db.models import Min, Max, Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Category, Product, Variant, ProductAttribute, WishlistItem
from apps.cart.utils import get_or_create_cart


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 24  # Requirement A1

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants', 'images', 'attributes')
        
        # Category filter (by slug from url or get)
        category_slug = self.kwargs.get('slug') or self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        # B1 Combinable Filter: Weapon Type
        weapon = self.request.GET.get('weapon')
        if weapon:
            qs = qs.filter(attributes__name='weapon_type', attributes__value__in=[weapon, 'all']).distinct()

        # B1 Combinable Filter: Certification
        cert = self.request.GET.get('cert')
        if cert:
            qs = qs.filter(attributes__name='certification', attributes__value__icontains=cert).distinct()

        # B1 Combinable Filter: In Stock Only
        in_stock = self.request.GET.get('in_stock')
        if in_stock in ['1', 'true', 'on']:
            qs = qs.filter(variants__stock__gt=0).distinct()

        # B1 Combinable Filter: Price Range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            try:
                qs = qs.annotate(min_p=Min('variants__price')).filter(min_p__gte=Decimal(min_price))
            except Exception:
                pass
        if max_price:
            try:
                qs = qs.annotate(min_p=Min('variants__price')).filter(min_p__lte=Decimal(max_price))
            except Exception:
                pass

        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'price_asc':
            qs = qs.annotate(sort_price=Min('variants__price')).order_by('sort_price')
        elif sort == 'price_desc':
            qs = qs.annotate(sort_price=Min('variants__price')).order_by('-sort_price')
        elif sort == 'name':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('slug') or self.request.GET.get('category')
        current_cat = None
        if category_slug:
            current_cat = Category.objects.filter(slug=category_slug).first()

        context['current_category'] = current_cat
        context['all_categories'] = Category.objects.all().order_by('name')
        context['selected_weapon'] = self.request.GET.get('weapon', '')
        context['selected_cert'] = self.request.GET.get('cert', '')
        context['selected_in_stock'] = self.request.GET.get('in_stock', '')
        context['selected_min_price'] = self.request.GET.get('min_price', '')
        context['selected_max_price'] = self.request.GET.get('max_price', '')
        context['selected_sort'] = self.request.GET.get('sort', 'newest')

        # Price range bounds
        price_bounds = Variant.objects.aggregate(min_p=Min('price'), max_p=Max('price'))
        context['global_min_price'] = price_bounds['min_p'] or 0
        context['global_max_price'] = price_bounds['max_p'] or 500

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related('variants', 'images', 'attributes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        variants = list(product.variants.all())

        # Precompute available stock for each variant (variant stock minus active reservations)
        variants_data = []
        for v in variants:
            avail = v.get_available_stock()
            variants_data.append({
                'id': v.id,
                'sku': v.sku,
                'size': v.size,
                'handedness': v.handedness,
                'grip_type': v.grip_type,
                'price': str(v.price),
                'stock': avail,
                'label': v.label,
            })

        context['variants_json'] = json.dumps(variants_data)
        context['default_variant'] = variants[0] if variants else None
        context['images'] = product.images.all()

        # Attributes map
        attrs = {attr.name: attr.value for attr in product.attributes.all()}
        context['product_attrs'] = attrs

        # B2 Recommendations: "Compatible with" and "similar" items
        weapon_type = attrs.get('weapon_type')
        compatible_items = []
        similar_items = []

        if weapon_type:
            # Compatible items: different category, matching weapon_type or 'all'
            compatible_items = Product.objects.filter(
                is_active=True,
                attributes__name='weapon_type',
                attributes__value__in=[weapon_type, 'all']
            ).exclude(category=product.category).distinct()[:4]

            # Similar items: same category, matching weapon_type
            similar_items = Product.objects.filter(
                is_active=True,
                category=product.category,
                attributes__name='weapon_type',
                attributes__value__in=[weapon_type, 'all']
            ).exclude(id=product.id).distinct()[:4]

        if not similar_items:
            similar_items = Product.objects.filter(
                is_active=True,
                category=product.category
            ).exclude(id=product.id)[:4]

        context['compatible_items'] = compatible_items
        context['similar_items'] = similar_items

        # Check if already wishlisted
        context['is_wishlisted'] = False
        if self.request.user.is_authenticated and variants:
            context['is_wishlisted'] = WishlistItem.objects.filter(
                user=self.request.user,
                variant=variants[0]
            ).exists()

        return context


class ProductSearchView(ListView):
    model = Product
    template_name = 'catalog/product_search.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()
        # Case-insensitive icontains search on product name (Requirement A2)
        return Product.objects.filter(
            is_active=True,
            name__icontains=query
        ).select_related('category').prefetch_related('variants', 'images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context


class WishlistView(LoginRequiredMixin, ListView):
    model = WishlistItem
    template_name = 'catalog/wishlist.html'
    context_object_name = 'wishlist_items'

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related(
            'variant', 'variant__product', 'variant__product__category'
        ).prefetch_related('variant__product__images')


class WishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, variant_id):
        variant = get_object_or_404(Variant, id=variant_id)
        item = WishlistItem.objects.filter(user=request.user, variant=variant).first()
        if item:
            item.delete()
            messages.info(request, f'Removed {variant.product.name} from your wishlist.')
        else:
            WishlistItem.objects.create(user=request.user, variant=variant)
            messages.success(request, f'Added {variant.product.name} ({variant.label}) to your wishlist!')

        return redirect(request.META.get('HTTP_REFERER', reverse('catalog:wishlist')))


class WishlistToCartView(LoginRequiredMixin, View):
    def post(self, request, id):
        item = get_object_or_404(WishlistItem, id=id, user=request.user)
        variant = item.variant
        avail = variant.get_available_stock()

        if avail <= 0:
            messages.error(request, f'Sorry, {variant.product.name} ({variant.label}) is currently out of stock.')
            return redirect('catalog:wishlist')

        cart = get_or_create_cart(request)
        cart_item, created = cart.items.get_or_create(variant=variant, defaults={'quantity': 1})
        if not created:
            if cart_item.quantity < avail:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, f'Maximum available stock ({avail}) already in cart.')
                return redirect('cart:cart_detail')

        item.delete()
        messages.success(request, f'Moved {variant.product.name} to your cart!')
        return redirect('cart:cart_detail')


class StarterKitGuideView(TemplateView):
    template_name = 'catalog/starter_kit_guide.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch key starter items
        context['starter_jacket'] = Product.objects.filter(slug='apex-350n-fencing-jacket-mens').first()
        context['starter_mask'] = Product.objects.filter(slug='350n-fencing-mask-foil-epee').first()
        context['starter_glove'] = Product.objects.filter(slug='padded-fencing-glove-anti-slip-grip').first()
        context['starter_plastron'] = Product.objects.filter(slug='800n-fie-underarm-plastron').first()
        context['starter_foil'] = Product.objects.filter(slug='club-electric-foil').first()
        return context
