from django.contrib import admin
from .models import RefundRequest, RefundAuditLog


class RefundAuditLogInline(admin.TabularInline):
    model = RefundAuditLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'notes', 'created_at')


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'requested_by', 'status', 'refund_amount', 'created_at')
    list_filter = ('status',)
    inlines = [RefundAuditLogInline]
