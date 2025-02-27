from django.db import models
from django.utils.text import slugify
import os
from orders.models import Order


class Crashpad(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    brand = models.CharField(max_length=100, blank=False, null=False)
    model = models.CharField(max_length=100, blank=False, null=False)
    dimensions = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    day_rate = models.DecimalField(max_digits=10,
                                   decimal_places=2,
                                   default=0,
                                   blank=False,
                                   null=False)
    seven_day_rate = models.DecimalField(max_digits=10,
                                         decimal_places=2,
                                         default=0,
                                         blank=False,
                                         null=False)
    fourteen_day_rate = models.DecimalField(max_digits=10,
                                            decimal_places=2,
                                            default=0,
                                            blank=False,
                                            null=False)
    image = models.ImageField(upload_to='crashpads/', null=True, blank=True)

    def __str__(self):
        return self.name

    def is_available(self, check_in, check_out):
        """Check if the crashpad is available for the given dates"""
        bookings = CrashpadBooking.objects.filter(crashpad=self,
                                                  status='confirmed',
                                                  check_in__lte=check_out,
                                                  check_out__gte=check_in)
        return not bookings.exists()


def crashpad_gallery_upload_path(instance, filename):
    """
    Upload images to 'media/crashpad_gallery/{crashpad_name}/'
    with sanitized names.
    """
    # Converts name to a slug
    crashpad_name_slug = slugify(instance.crashpad.name)
    return os.path.join("crashpad_gallery", crashpad_name_slug, filename)


class CrashpadGalleryImage(models.Model):
    crashpad = models.ForeignKey(Crashpad,
                                 related_name="gallery_images",
                                 on_delete=models.CASCADE)
    image = models.ImageField(upload_to=crashpad_gallery_upload_path)

    def __str__(self):
        return f"Gallery image for {self.crashpad.name}"


class CrashpadBooking(models.Model):
    crashpad = models.ForeignKey(Crashpad, on_delete=models.CASCADE)
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name='crashpads')
    check_in = models.DateField()
    check_out = models.DateField()
    rental_days = models.IntegerField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10,
                              choices=[
                                  ('confirmed', 'Confirmed'),
                                  ('cancelled', 'Cancelled'),
                              ],
                              default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Methods for calculated fields
    def calculate_rental_days(self):
        return (self.check_out - self.check_in).days

    def calculate_daily_rate(self):
        # Calculate daily rate
        if self.rental_days >= 14:
            daily_rate = self.crashpad.fourteen_day_rate
        elif self.rental_days >= 7:
            daily_rate = self.crashpad.seven_day_rate
        else:
            daily_rate = self.crashpad.day_rate
        return daily_rate

    def calculate_total_price(self):
        return self.daily_rate * self.calculate_rental_days()

    def get_customer_name(self):
        return f"{self.order.first_name} {self.order.last_name}"

    def get_customer_email(self):
        return self.order.email

    def get_customer_phone(self):
        return self.order.phone

    # Database fields that use the methods
    rental_days = models.IntegerField(editable=False)
    customer_name = models.CharField(max_length=255, editable=False)
    customer_email = models.EmailField(editable=False)
    customer_phone = models.CharField(max_length=20, editable=False)

    def save(self, *args, **kwargs):
        """Populate calculated fields before saving"""
        self.rental_days = self.calculate_rental_days()
        self.daily_rate = self.calculate_daily_rate()
        self.total_price = self.calculate_total_price()
        self.customer_name = self.get_customer_name()
        self.customer_email = self.get_customer_email()
        self.customer_phone = self.get_customer_phone()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - {self.crashpad.name} " \
               f"({self.check_in} to {self.check_out})"

    class Meta:
        ordering = ['-created_at']
