from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Checkout flow (A5)
    path('checkout/address/', views.checkout_address_view, name='checkout_address'),
    path('checkout/delivery/', views.checkout_delivery_view, name='checkout_delivery'),
    path('checkout/summary/', views.checkout_summary_view, name='checkout_summary'),
    path('checkout/pay/', views.checkout_pay_view, name='checkout_pay'),
    path('checkout/success/<str:number>/', views.checkout_success_view, name='checkout_success'),
    path('checkout/cancel/<str:number>/', views.checkout_cancel_view, name='checkout_cancel'),

    # Customer Order History (A8)
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/<str:number>/', views.order_detail_view, name='order_detail'),
]
