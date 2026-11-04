from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'body', 'created_at')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('organizer', 'participant', 'subject', 'updated_at')
    inlines = [MessageInline]
