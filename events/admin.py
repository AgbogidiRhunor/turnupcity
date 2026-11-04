from django.contrib import admin
from .models import Event, Category, Coupon


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'status', 'start_date', 'city', 'created_at')
    list_filter = ('status', 'is_private', 'city')
    search_fields = ('title', 'organizer__organization_name')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'event', 'discount_type', 'discount_value', 'is_active', 'used_count')
    list_filter = ('is_active', 'discount_type')
