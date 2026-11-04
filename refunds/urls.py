from django.urls import path
from . import views

app_name = 'refunds'

urlpatterns = [
    path('request/<int:order_pk>/', views.request_refund, name='request'),
    path('my/', views.my_refunds, name='my_refunds'),
    path('organizer/', views.organizer_refunds, name='organizer_list'),
    path('<int:pk>/process/', views.process_refund, name='process'),
]
