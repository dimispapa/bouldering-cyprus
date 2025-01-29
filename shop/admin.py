from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Product, GalleryImage


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1
    fields = ("image",)
    readonly_fields = ()
    min_num = 0
    max_num = 10


@admin.register(Product)
class ProductAdmin(SummernoteModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active', 'created_at')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')
    summernote_fields = ('description',)

    inlines = [GalleryImageInline]  # Add the inline for multiple image uploads
