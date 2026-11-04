from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.organizer_analytics, name='dashboard'),
    path('event/<slug:event_slug>/', views.event_analytics, name='event_detail'),
    path('event/<slug:event_slug>/export/', views.export_csv, name='export_csv'),
    path('event/<slug:event_slug>/broadcast/', views.broadcast_email, name='broadcast'),
]
