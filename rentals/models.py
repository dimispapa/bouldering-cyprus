from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from django.utils.text import slugify
import os


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
        bookings = Booking.objects.filter(crashpad=self,
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


class Booking(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
        (PARTIALLY_REFUNDED, 'Partially Refunded'),
    ]

    crashpad = models.ForeignKey(Crashpad, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    check_in = models.DateField(blank=False, null=False)
    check_out = models.DateField(blank=False, null=False)
    booking_number = models.CharField(max_length=32,
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
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default=PENDING,
                              blank=False,
                              null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.crashpad.name} - {self.check_in} to {self.check_out}"
