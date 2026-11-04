from django.contrib import admin
from django.utils import timezone
from .models import OrganizerProfile, StaffRequest, StaffMembership


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('organization_name', 'user__email')
    actions = ['verify_organizers']

    def verify_organizers(self, request, queryset):
        queryset.update(status=OrganizerProfile.STATUS_VERIFIED, verified_at=timezone.now())
        self.message_user(request, 'Selected organizers verified.')
    verify_organizers.short_description = 'Verify selected organizers'


@admin.register(StaffRequest)
class StaffRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'organizer', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(StaffMembership)
class StaffMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organizer', 'is_active', 'joined_at')
    list_filter = ('is_active',)
