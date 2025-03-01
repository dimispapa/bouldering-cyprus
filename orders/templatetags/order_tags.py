from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def sum_items(values_list):
    """Sum a list of values"""
    try:
        return sum(values_list)
    except (ValueError, TypeError):
        return 0


@register.filter
def sum_product_items(items):
    """Sum the item_total for all product items in an order"""
    try:
        return sum(item.item_total for item in items)
    except (AttributeError, TypeError):
        return Decimal('0.00')


@register.filter
def sum_rental_items(bookings):
    """Sum the total_price for all rental items in an order"""
    try:
        return sum(booking.total_price for booking in bookings)
    except (AttributeError, TypeError):
        return Decimal('0.00')


@register.filter
def add_decimal(value, arg):
    """Add two decimal values together"""
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return value
