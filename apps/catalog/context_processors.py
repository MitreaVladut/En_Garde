from apps.catalog.models import Category, WishlistItem


def catalog_context(request):
    categories = Category.objects.all().order_by('id')
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return {
        'nav_categories': categories,
        'wishlist_count': wishlist_count,
    }
