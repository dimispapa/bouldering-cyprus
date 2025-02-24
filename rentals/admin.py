from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Crashpad, Booking, CrashpadGalleryImage


class CrashpadGalleryImageInline(admin.TabularInline):
    model = CrashpadGalleryImage
    extra = 1
    fields = ("image", )
    readonly_fields = ()
    min_num = 0
    max_num = 10


@admin.register(Crashpad)
class CrashpadAdmin(SummernoteModelAdmin):
    list_display = ('name', 'brand', 'model', 'day_rate', 'seven_day_rate',
                    'fourteen_day_rate')
    summernote_fields = ('description', )
    list_filter = ('brand', )
    search_fields = ('name', 'brand', 'model', 'description')
    ordering = ('name', 'brand', 'model', 'day_rate')
    list_per_page = 20

    inlines = [CrashpadGalleryImageInline
               ]  # Add the inline for multiple image uploads


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'crashpad', 'user', 'check_in',
                    'check_out', 'status', 'created_at')
    list_filter = ('status', 'check_in', 'check_out', 'created_at')
    search_fields = ('booking_number', 'user__email', 'first_name',
                     'last_name', 'email')
    readonly_fields = ('booking_number', 'created_at', 'updated_at')
    ordering = ('-created_at', )
    list_per_page = 20

    fieldsets = (('Booking Information', {
        'fields': ('booking_number', 'crashpad', 'user', 'status', 'check_in',
                   'check_out')
    }), ('Customer Information', {
        'fields': ('first_name', 'last_name', 'email', 'phone')
    }), ('Address Information', {
        'fields': ('address_line1', 'address_line2', 'town_or_city',
                   'postal_code', 'country')
    }), ('Timestamps', {
        'fields': ('created_at', 'updated_at'),
        'classes': ('collapse', )
    }))
