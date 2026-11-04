from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('event/<slug:event_slug>/add-type/', views.add_ticket_type, name='add_type'),
    path('type/<int:pk>/edit/', views.edit_ticket_type, name='edit_type'),
    path('<uuid:uuid>/', views.ticket_detail, name='detail'),
]
