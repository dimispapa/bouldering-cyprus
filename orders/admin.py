from django.contrib import admin
from .models import Order, OrderItem
from rentals.models import CrashpadBooking


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price', 'item_total')
    extra = 0

    def formfield_callback(self, db_field, formfield, request):
        if formfield:
            formfield.widget.attrs['onchange'] = 'this.form.submit()'
        return formfield


class CrashpadBookingInline(admin.TabularInline):
    model = CrashpadBooking
    readonly_fields = ('rental_days', 'daily_rate', 'total_price',
                       'customer_name', 'customer_email', 'customer_phone')
    extra = 0
    fields = ('crashpad', 'check_in', 'check_out', 'daily_rate', 'rental_days',
              'total_price', 'status')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderItemInline, CrashpadBookingInline)
    readonly_fields = ('order_number', 'date_created', 'date_updated',
                       'stripe_piid', 'order_type', 'delivery_cost',
                       'handling_fee', 'order_total', 'grand_total', 'id',
                       'comments')

    list_display = ('order_number', 'id', 'date_created', 'first_name',
                    'last_name', 'order_type', 'order_total', 'delivery_cost',
                    'handling_fee', 'grand_total')

    ordering = ('-date_created', )

    search_fields = ('order_number', 'first_name', 'last_name', 'email',
                     'phone')

    list_filter = ('date_created', 'country', 'order_type')

    fieldsets = (
        ('Order Details', {
            'fields': ('order_number', 'id', 'date_created', 'date_updated',
                       'order_type')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Delivery Information', {
            'fields': ('address_line1', 'address_line2', 'town_or_city',
                       'postal_code', 'country')
        }),
        ('Financial Details', {
            'fields': ('order_total', 'delivery_cost', 'handling_fee',
                       'grand_total', 'stripe_piid')
        }),
        ('Additional Information', {
            'fields': ('comments', ),
            'classes': ('collapse', )
        }),
    )

    def save_formset(self, request, form, formset, change):
        formset.save()
        for instance in formset.forms:
            if instance.instance.order:
                instance.instance.order.update_total()

    def delete_queryset(self, request, queryset):
        """
        Override the bulk deletion method to ensure stock is released
        for each order being deleted
        """
        # Process each order individually to ensure stock release
        for order in queryset:
            order.delete()  # This will call our custom delete method


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity', 'item_total')
    readonly_fields = ('price', 'item_total')
    search_fields = ('order__order_number', 'product__name')
    list_filter = ('order__date_created', )
