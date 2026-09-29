from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Staff Admin Panel (/manage/)
    path('manage/', include('apps.manage.urls', namespace='manage')),

    # Accounts
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Cart
    path('cart/', include('apps.cart.urls', namespace='cart')),

    # Orders & Checkout
    path('', include('apps.orders.urls', namespace='orders')),

    # Payments & Webhooks
    path('', include('apps.payments.urls', namespace='payments')),

    # Catalog, Search, Categories, Wishlist, Starter Guide (Root paths)
    path('', include('apps.catalog.urls', namespace='catalog')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
