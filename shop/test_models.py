from django.test import TestCase
from django.conf import settings
from model_bakery import baker
from decimal import Decimal
import os

from shop.models import Product, GalleryImage, product_gallery_upload_path


class ProductModelTest(TestCase):

    def setUp(self):
        """Set up test data"""
        self.product = baker.make(
            Product,
            name="Test Product",
            description="Test Description",
            price=Decimal("99.99"),
            stock=settings.LOW_STOCK_THRESHOLD +
            5,  # Ensure it's above threshold
            is_active=True)

        self.out_of_stock_product = baker.make(Product,
                                               name="Out of Stock Product",
                                               price=Decimal("49.99"),
                                               stock=0,
                                               is_active=True)

        self.low_stock_product = baker.make(
            Product,
            name="Low Stock Product",
            price=Decimal("29.99"),
            stock=settings.LOW_STOCK_THRESHOLD - 1,  # Just below threshold
            is_active=True)

    def test_product_str_method(self):
        """Test the string representation of a Product"""
        self.assertEqual(str(self.product), "Test Product")

    def test_is_in_stock_method(self):
        """Test the is_in_stock method"""
        self.assertTrue(self.product.is_in_stock())
        self.assertFalse(self.out_of_stock_product.is_in_stock())

    def test_is_low_stock_method(self):
        """Test the is_low_stock method"""
        self.assertFalse(self.product.is_low_stock())
        self.assertFalse(self.out_of_stock_product.is_low_stock()
                         )  # Out of stock is not low stock
        self.assertTrue(self.low_stock_product.is_low_stock())

        # Test with custom threshold
        custom_threshold = 15
        self.assertTrue(self.product.is_low_stock(threshold=custom_threshold))

    def test_has_stock_method(self):
        """Test the has_stock method"""
        self.assertTrue(self.product.has_stock())
        self.assertTrue(self.product.has_stock(quantity=5))

        # The product has settings.LOW_STOCK_THRESHOLD + 5 items in stock
        # So we need to request more than that to get False
        self.assertFalse(
            self.product.has_stock(quantity=settings.LOW_STOCK_THRESHOLD + 6))

        self.assertFalse(self.out_of_stock_product.has_stock())

    def test_get_stock_status_method(self):
        """Test the get_stock_status method"""
        # Test in-stock product
        status = self.product.get_stock_status()
        self.assertEqual(status['message'], 'In Stock')
        self.assertEqual(status['css_class'], 'text-success')

        # Test out-of-stock product
        status = self.out_of_stock_product.get_stock_status()
        self.assertEqual(status['message'], 'Out of Stock')
        self.assertEqual(status['css_class'], 'text-danger')

        # Test low-stock product
        status = self.low_stock_product.get_stock_status()
        self.assertEqual(status['message'],
                         f'Only {self.low_stock_product.stock} left!')
        self.assertEqual(status['css_class'], 'text-warning')


class GalleryImageModelTest(TestCase):

    def setUp(self):
        """Set up test data"""
        self.product = baker.make(Product, name="Test Product with Gallery")
        self.gallery_image = baker.make(GalleryImage, product=self.product)

    def test_gallery_image_str_method(self):
        """Test the string representation of a GalleryImage"""
        expected_str = f"Gallery image for {self.product.name}"
        self.assertEqual(str(self.gallery_image), expected_str)


class ProductGalleryUploadPathTest(TestCase):

    def test_product_gallery_upload_path(self):
        """Test the product_gallery_upload_path function"""
        product = baker.make(Product, name="Test Product Name")
        gallery_image = baker.make(GalleryImage, product=product)

        # Test with a simple filename
        filename = "test_image.jpg"
        path = product_gallery_upload_path(gallery_image, filename)

        # Expected path should use slugified product name
        expected_path = os.path.join("product_gallery", "test-product-name",
                                     filename)
        self.assertEqual(path, expected_path)

        # Test with a filename containing spaces and special characters
        filename = "test image (1).jpg"
        path = product_gallery_upload_path(gallery_image, filename)
        expected_path = os.path.join("product_gallery", "test-product-name",
                                     filename)
        self.assertEqual(path, expected_path)
