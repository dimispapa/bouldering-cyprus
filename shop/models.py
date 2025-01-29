import os
from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
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


def product_gallery_upload_path(instance, filename):
    """
    Upload images to 'media/product_gallery/{product_name}/'
    with sanitized names.
    """
    # Converts name to a slug
    product_name_slug = slugify(instance.product.name)
    return os.path.join("product_gallery", product_name_slug, filename)


class GalleryImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="gallery_images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=product_gallery_upload_path)

    def __str__(self):
        return f"Gallery image for {self.product.name}"
