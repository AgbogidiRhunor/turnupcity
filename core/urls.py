from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from events.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls')),
    path('organizers/', include('organizers.urls')),
    path('events/', include('events.urls')),
    path('tickets/', include('tickets.urls')),
    path('orders/', include('orders.urls')),
    path('checkin/', include('checkin.urls')),
    path('refunds/', include('refunds.urls')),
    path('messaging/', include('messaging.urls')),
    path('analytics/', include('analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
