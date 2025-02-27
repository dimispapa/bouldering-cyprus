from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Crashpad, CrashpadBooking, CrashpadGalleryImage


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


@admin.register(CrashpadBooking)
class CrashpadBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'crashpad', 'customer_name', 'customer_email',
                    'check_in', 'check_out', 'rental_days', 'daily_rate',
                    'total_price', 'status')

    list_filter = ('crashpad', 'status', 'check_in', 'check_out', 'created_at',
                   'customer_name', 'customer_email', 'customer_phone')

    search_fields = ('crashpad__name', 'customer_email', 'customer_name',
                     'customer_phone')

    readonly_fields = ('created_at', 'updated_at', 'rental_days', 'daily_rate',
                       'total_price', 'customer_name', 'customer_email',
                       'customer_phone')
