from django.urls import path
from . import views

app_name = 'organizers'

urlpatterns = [
    path('setup/', views.organizer_setup, name='setup'),
    path('dashboard/', views.organizer_dashboard, name='dashboard'),
    path('edit/', views.organizer_edit, name='edit'),
    path('staff-requests/', views.staff_requests_list, name='staff_requests'),
    path('staff-requests/<int:pk>/action/', views.approve_staff_request, name='approve_staff'),
    path('<slug:slug>/', views.organizer_public_profile, name='public_profile'),
    path('<slug:slug>/work/', views.request_to_work, name='request_to_work'),
    path('withdrawals/', views.withdrawal_dashboard, name='withdrawal_dashboard'),
    path('withdrawals/bank/', views.setup_bank_account, name='setup_bank_account'),
    path('withdrawals/request/', views.request_withdrawal, name='request_withdrawal'),
]
