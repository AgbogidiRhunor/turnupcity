from django.contrib import admin
from .models import TicketType, Ticket, ScanLog


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'event__title')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'ticket_type', 'order', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('uuid', 'qr_code')


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'scanned_by', 'scanned_at', 'gate', 'success')
    list_filter = ('success',)
    readonly_fields = ('scanned_at',)
