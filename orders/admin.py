from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    def formfield_callback(self, db_field, formfield, request):
        if formfield:
            formfield.widget.attrs['onchange'] = 'this.form.submit()'
        return formfield


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "first_name",
        "last_name",
        "email",
        "phone",
        "date_created",
        "date_updated",
        "grand_total",
    ]
    list_filter = ["date_created"]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "phone",
        "order_number",
    ]
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'date_created', 'date_updated',
                       'stripe_piid')

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
