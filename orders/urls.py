from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<slug:event_slug>/', views.checkout, name='checkout'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'),
    path('paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('<int:pk>/confirmation/', views.order_confirmation, name='confirmation'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('my/', views.my_orders, name='my_orders'),
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('organizer/', views.organizer_orders, name='organizer_orders'),
]
