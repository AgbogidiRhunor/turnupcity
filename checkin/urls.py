from django.urls import path
from . import views

app_name = 'checkin'

urlpatterns = [
    path('', views.scanner_dashboard, name='select_event'),
    path('event/<slug:event_slug>/', views.scanner_dashboard, name='scanner'),
    path('scan/', views.scan_ticket, name='scan'),
    path('lookup/', views.manual_lookup, name='lookup'),
]
