from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('add/', views.cart_add_view, name='cart_add'),
    path('update/<int:item_id>/', views.cart_update_view, name='cart_update'),
    path('remove/<int:item_id>/', views.cart_remove_view, name='cart_remove'),
    path('discount/', views.cart_discount_view, name='cart_discount'),
]
