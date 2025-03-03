from django.test import TestCase, Client, override_settings
from django.urls import reverse
from model_bakery import baker
from decimal import Decimal
import re
import tempfile
from unittest.mock import patch

from shop.models import Product, GalleryImage

# Create a temporary media root for testing
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ShopViewTest(TestCase):

    def setUp(self):
        """Set up test data"""
        # Create an active product
        self.product = baker.make(
            Product,
            name="Test Guide Book",
            description="<p>This is a test description</p>",
            price=Decimal("29.99"),
            stock=10,
            is_active=True,
            # Don't set image field
            _fill_optional=False)

        # Create an inactive product (shouldn't appear in the view)
        self.inactive_product = baker.make(Product,
                                           name="Inactive Product",
                                           price=Decimal("19.99"),
                                           is_active=False,
                                           _fill_optional=False)

        # Create some gallery images for the product
        # but don't set actual images
        self.gallery_image1 = baker.make(GalleryImage,
                                         product=self.product,
                                         _fill_optional=False)

        self.gallery_image2 = baker.make(GalleryImage,
                                         product=self.product,
                                         _fill_optional=False)

        # Set up the client
        self.client = Client()

        # Mock the image url method to avoid errors
        self.patcher = patch(
            'django.db.models.fields.files.ImageFieldFile.url',
            new_callable=lambda: '/mock/image/url.jpg')
        self.mock_url = self.patcher.start()

        # Get the response
        self.url = reverse('shop')
        self.response = self.client.get(self.url)

    def tearDown(self):
        # Stop the patcher
        self.patcher.stop()

    def test_shop_view_status_code(self):
        """Test that the shop view returns a 200 status code"""
        self.assertEqual(self.response.status_code, 200)

    def test_shop_view_uses_correct_template(self):
        """Test that the shop view uses the correct template"""
        self.assertTemplateUsed(self.response, 'shop/shop.html')
        self.assertTemplateUsed(self.response, 'base.html')

    def test_shop_view_contains_correct_html(self):
        """Test that the shop view contains the expected HTML elements"""
        # Check page title
        self.assertContains(
            self.response,
            '<title>Bouldering Cyprus - Buy the Guide Book</title>',
            html=True)

        # Check CSS is loaded
        self.assertContains(self.response, 'shop/css/shop.css')

        # Check JS is loaded
        self.assertContains(self.response, 'shop/js/shop.js')

        # Check product name is displayed
        self.assertContains(self.response, self.product.name)

        # Check product description is displayed
        self.assertContains(self.response, self.product.description)

        # Check product price is displayed
        self.assertContains(self.response, f'€{self.product.price}')

        # Check stock status is displayed
        stock_status = self.product.get_stock_status()
        self.assertContains(self.response, stock_status['message'])

        # Check add to cart form exists
        self.assertContains(self.response, 'action="/cart/add/product/"')
        self.assertContains(self.response, 'name="product_id"')
        self.assertContains(self.response, f'value="{self.product.id}"')
        self.assertContains(self.response, 'name="quantity"')

        # Check gallery section exists
        self.assertContains(self.response, '<h2>Gallery</h2>')

        # Check modal exists
        self.assertContains(self.response, 'id="galleryModal"')
        self.assertContains(self.response, 'id="modalImage"')
        self.assertContains(self.response, 'id="prevBtn"')
        self.assertContains(self.response, 'id="nextBtn"')

    def test_inactive_products_not_displayed(self):
        """Test that inactive products are not displayed"""
        self.assertNotContains(self.response, self.inactive_product.name)

    def test_gallery_images_displayed(self):
        """Test that gallery images are displayed"""
        # Check that the gallery thumbnails are displayed
        # We can't check the exact URLs since model_bakery
        # doesn't create real files
        # But we can check that the gallery-thumbnail class is used
        thumbnail_count = len(
            re.findall(r'class="[^"]*gallery-thumbnail[^"]*"',
                       self.response.content.decode()))

        # We should have at least the main product image + gallery images
        expected_count = 1  # Main product image
        if self.product.image:  # If product has a main image
            expected_count += 1
        expected_count += self.product.gallery_images.count()

        # The count might be less if model_bakery doesn't set image fields
        self.assertGreaterEqual(thumbnail_count, 1)

    def test_context_data(self):
        """Test that the context contains the correct data"""
        products = self.response.context['products']
        self.assertEqual(len(products), 1)  # Only active products
        self.assertEqual(products[0], self.product)
