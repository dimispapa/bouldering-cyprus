from django.db import models
from shop.models import Product
from rentals.models import Crashpad
from django.conf import settings
from django_countries.fields import CountryField
import uuid
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Order(models.Model):
    """Order model holding successful order details"""
    order_number = models.CharField(max_length=32,
                                    null=False,
                                    editable=False,
                                    unique=True)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(max_length=250, null=False, blank=False)
    phone = models.CharField(max_length=20, null=False, blank=False)
    address_line1 = models.CharField(max_length=250, null=False, blank=False)
    address_line2 = models.CharField(max_length=250, null=True, blank=True)
    town_or_city = models.CharField(max_length=100, null=False, blank=False)
    postal_code = models.CharField(max_length=20, null=False, blank=False)
    country = CountryField(blank_label="Country *", null=False, blank=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    stripe_piid = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        # enforce uniqueness, avoid duplicate orders
        unique=True,
        # for better query performance
        db_index=True)

    original_cart = models.TextField(null=False, blank=False)
    delivery_cost = models.DecimalField(max_digits=6,
                                        decimal_places=2,
                                        null=False)
    order_total = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      null=False)
    grand_total = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      null=False)

    class Meta:
        ordering = ("-date_created", )

    def _generate_order_number(self):
        """
        Generate a random, unique order number using UUID
        """
        return uuid.uuid4().hex.upper()

    def save(self, *args, **kwargs):
        """
        Override the save method to set the order number
        if it hasn't been set yet
        """
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def update_total(self):
        """Update the order total, delivery cost and grand total"""
        self.order_total = self.items.aggregate(
            models.Sum("item_total"))["item_total__sum"] or 0
        if self.order_total < settings.FREE_DELIVERY_THRESHOLD:
            self.delivery_cost = (settings.STANDARD_DELIVERY_PERCENTAGE *
                                  self.order_total / 100)
        else:
            self.delivery_cost = 0
        self.grand_total = self.order_total + self.delivery_cost
        self.save()

    def delete(self, *args, **kwargs):
        """
        Override the delete method to release product stock
        before deleting the order
        """
        try:
            logger.info(
                f"Starting delete process for order {self.order_number}")
            # Release stock for each order item
            items_count = self.items.count()
            logger.info(f"Found {items_count} items to process")

            for order_item in self.items.all():
                product = order_item.product
                old_stock = product.stock
                product.stock += order_item.quantity
                product.save()
                logger.info(
                    f"Released {order_item.quantity} units back to stock "
                    f"for product {product.name} "
                    f"(ID: {product.id}) from deleted order "
                    f"{self.order_number}. "
                    f"Stock changed from {old_stock} to {product.stock}")
        except Exception as e:
            logger.error(f"Error releasing stock for "
                         f"order {self.order_number}: {e}")
            # Re-raise the exception to prevent deletion if stock release fails
            raise

        # Finally call the delete method
        logger.info(f"Proceeding with deletion of order {self.order_number}")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    """Order item model linking order to product"""
    order = models.ForeignKey(Order,
                              null=False,
                              blank=False,
                              on_delete=models.CASCADE,
                              related_name="items")
    product = models.ForeignKey(Product,
                                null=True,
                                blank=True,
                                on_delete=models.SET_NULL,
                                related_name="order_items")
    crashpad = models.ForeignKey(Crashpad,
                                 null=True,
                                 blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name="order_items")
    type = models.CharField(max_length=10,
                            choices=[('product', 'Product'),
                                     ('rental', 'Rental')])
    quantity = models.IntegerField(default=1)
    item_total = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     null=False,
                                     blank=False)
    # Rental specific fields
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    rental_days = models.IntegerField(null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     null=True,
                                     blank=True)

    def clean(self):
        """
        Validate the OrderItem based on its type
        """
        super().clean()
        errors = {}

        # Validate item type and corresponding fields
        if self.type == 'product':
            # Product-specific validation
            if not self.product:
                errors['product'] = 'Product is required for product-type ' \
                                    'items'
            if self.crashpad:
                errors['crashpad'] = 'Crashpad should not be set for ' \
                                     'product-type items'
            if (self.check_in or self.check_out or self.rental_days
                    or self.daily_rate):
                errors['rental_fields'] = 'Rental fields should not be set ' \
                                          'for product-type items'
            if self.quantity < 1:
                errors['quantity'] = 'Quantity must be at least 1 for products'

        elif self.type == 'rental':
            # Rental-specific validation
            if not self.crashpad:
                errors['crashpad'] = 'Crashpad is required for rental-type ' \
                                     'items'
            if self.product:
                errors['product'] = 'Product should not be set for ' \
                                    'rental-type items'
            if not self.check_in:
                errors['check_in'] = 'Check-in date is required for rentals'
            if not self.check_out:
                errors['check_out'] = 'Check-out date is required for rentals'
            if not self.rental_days:
                errors['rental_days'] = 'Rental days is required for rentals'
            if not self.daily_rate:
                errors['daily_rate'] = 'Daily rate is required for rentals'
            if self.quantity != 1:
                errors['quantity'] = 'Quantity must be exactly 1 for rentals'

            # Validate dates if both are present
            if self.check_in and self.check_out:
                if self.check_in >= self.check_out:
                    errors['dates'] = 'Check-out date must be after ' \
                                      'check-in date'
                if self.rental_days != (self.check_out - self.check_in).days:
                    errors['rental_days'] = 'Rental days does not match the ' \
                                            'date range'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Override save to ensure full_clean is called for validation.
        Calculate the item total and save the order item.
        """
        self.full_clean()
        if self.type == 'product':
            self.item_total = self.product.price * self.quantity
        elif self.type == 'rental':
            self.item_total = self.daily_rate * self.rental_days
        super().save(*args, **kwargs)

    def __str__(self):
        item_name = self.product.name if self.product else self.crashpad.name
        return f"{self.order.order_number} - {item_name}"
