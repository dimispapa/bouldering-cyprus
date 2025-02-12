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

    def save_formset(self, request, form, formset, change):
        formset.save()
        for instance in formset.forms:
            if instance.instance.order:
                instance.instance.order.update_total()
