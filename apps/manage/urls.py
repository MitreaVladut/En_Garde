from django.urls import path
from . import views

app_name = 'manage'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Category CRUD
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/new/', views.category_create_view, name='category_create'),
    path('categories/<int:id>/edit/', views.category_update_view, name='category_update'),
    path('categories/<int:id>/delete/', views.category_delete_view, name='category_delete'),

    # Product CRUD
    path('products/', views.product_list_view, name='product_list'),
    path('products/new/', views.product_create_view, name='product_create'),
    path('products/<int:id>/edit/', views.product_update_view, name='product_update'),
    path('products/<int:id>/delete/', views.product_delete_view, name='product_delete'),

    # Variant CRUD
    path('products/<int:id>/variants/', views.variant_create_view, name='variant_create'),
    path('products/<int:id>/variants/<int:vid>/edit/', views.variant_update_view, name='variant_update'),
    path('products/<int:id>/variants/<int:vid>/delete/', views.variant_delete_view, name='variant_delete'),

    # Order Management & Status Transitions
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/<str:number>/', views.order_detail_view, name='order_detail'),
    path('orders/<str:number>/status/', views.order_status_update_view, name='order_status_update'),
]
