from django.db import models
from shop.models import Product
from django.conf import settings
from django_countries.fields import CountryField
import uuid
import logging

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
                                null=False,
                                blank=False,
                                on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=False, blank=False, default=0)
    item_total = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     null=False,
                                     blank=False,
                                     default=0)

    def save(self, *args, **kwargs):
        """Calculate the item total and save the order item"""
        self.item_total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
