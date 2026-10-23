from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('categories/<slug:slug>/', views.ProductListView.as_view(), name='category_detail'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.ProductSearchView.as_view(), name='search'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/toggle/<int:variant_id>/', views.WishlistToggleView.as_view(), name='wishlist_toggle'),
    path('wishlist/<int:id>/to-cart/', views.WishlistToCartView.as_view(), name='wishlist_to_cart'),
    path('guide/starter-kit/', views.StarterKitGuideView.as_view(), name='starter_kit_guide'),
]
