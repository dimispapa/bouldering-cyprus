import os
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0

    def is_low_stock(self, threshold=settings.LOW_STOCK_THRESHOLD):
        """Check if product is running low on stock"""
        return 0 < self.stock <= threshold

    def has_stock(self, quantity=1):
        """Check if requested quantity is available"""
        return self.stock >= quantity

    def get_stock_status(self):
        """Returns stock status message and CSS class"""
        if self.stock == 0:
            return {'message': 'Out of Stock', 'css_class': 'text-danger'}
        elif self.is_low_stock():
            return {
                'message': f'Only {self.stock} left!',
                'css_class': 'text-warning'
            }
        return {'message': 'In Stock', 'css_class': 'text-success'}


def product_gallery_upload_path(instance, filename):
    """
    Upload images to 'media/product_gallery/{product_name}/'
    with sanitized names.
    """
    # Converts name to a slug
    product_name_slug = slugify(instance.product.name)
    return os.path.join("product_gallery", product_name_slug, filename)


class GalleryImage(models.Model):
    product = models.ForeignKey(Product,
                                related_name="gallery_images",
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_gallery_upload_path)

    def __str__(self):
        return f"Gallery image for {self.product.name}"
