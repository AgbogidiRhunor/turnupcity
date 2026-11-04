from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.HomeView.as_view(), name='list'),
    path('create/', views.create_event, name='create'),
    path('<slug:slug>/', views.EventDetailView.as_view(), name='detail'),
    path('<slug:slug>/manage/', views.manage_event, name='manage'),
    path('<slug:slug>/edit/', views.edit_event, name='edit'),
    path('<slug:slug>/publish/', views.publish_event, name='publish'),
    path('<slug:slug>/cancel/', views.cancel_event, name='cancel'),
    path('<slug:slug>/coupon/add/', views.add_coupon, name='add_coupon'),
]
