from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('thread/<int:pk>/', views.thread_detail, name='thread'),
    path('start/<slug:organizer_slug>/', views.start_thread, name='start'),
]
