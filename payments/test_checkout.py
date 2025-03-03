from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from shop.models import Product
from rentals.models import Crashpad
from cart.cart import Cart
from datetime import datetime, timedelta
from model_bakery import baker
from django.conf import settings


class CheckoutViewTests(TestCase):
    """Tests for the checkout view"""

    def setUp(self):
        """Set up test data"""
        # Create a product
        self.product = baker.make(Product,
                                  name="Test Product",
                                  price=Decimal("29.99"),
                                  stock=10,
                                  is_active=True)

        # Create a crashpad for rental
        self.crashpad = baker.make(Crashpad,
                                   name="Test Crashpad",
                                   day_rate=Decimal("5.00"),
                                   seven_day_rate=Decimal("4.00"),
                                   fourteen_day_rate=Decimal("3.00"))

        # Set up dates for rental
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

        # Set up client and request factory
        self.client = Client()
        self.factory = RequestFactory()

        # Create a user
        self.user = User.objects.create_user(username='testuser',
                                             email='test@example.com',
                                             password='testpassword')

    def add_session_to_request(self, request):
        """Helper method to add session to request"""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Add message middleware
        message_middleware = MessageMiddleware(lambda req: None)
        message_middleware.process_request(request)

        return request

    def add_product_to_cart(self, request):
        """Helper method to add a product to the cart"""
        cart = Cart(request)
        cart.add(self.product, 1)
        return cart

    def add_crashpad_to_cart(self, request):
        """Helper method to add a crashpad rental to the cart"""
        cart = Cart(request)
        # Use the add method with item_type='rental' and dates
        cart.add(self.crashpad,
                 quantity=1,
                 item_type='rental',
                 dates={
                     'check_in': '2023-12-01',
                     'check_out': '2023-12-05'
                 })
        return cart

    def test_checkout_empty_cart(self):
        """Test checkout view with empty cart"""
        # Call the checkout view with an empty cart
        response = self.client.get(reverse('checkout'))

        # Check that we're redirected to cart_detail
        self.assertRedirects(response, reverse('cart_detail'))

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your cart is empty.")

    def test_checkout_with_invalid_stock(self):
        """Test checkout view with invalid stock"""
        # We need to patch the validate_stock function at the module level
        # where it's imported, not where it's defined
        with patch('payments.views.validate_stock') as mock_validate_stock:
            # Set up the mock to return a validation error
            error_msg = f"Only {self.product.stock} units " \
                f"available for {self.product.name}"
            mock_validate_stock.return_value = (False, error_msg)

            # Mock the Cart class
            with patch('payments.views.Cart') as mock_cart_class:
                # Create a mock cart instance
                mock_cart = MagicMock()
                mock_cart.__iter__.return_value = [{
                    'item':
                    self.product,
                    'quantity':
                    15,  # Exceeds stock of 10
                    'price':
                    str(self.product.price),
                    'type':
                    'product',
                    'total_price':
                    Decimal('449.85')
                }]
                mock_cart.__len__.return_value = 1

                # Make the Cart constructor return our mock cart
                mock_cart_class.return_value = mock_cart

                # Call the checkout view
                response = self.client.get(reverse('checkout'))

                # Check that we're redirected to cart_detail
                self.assertRedirects(response, reverse('cart_detail'))

                # Check for error message about stock
                messages = list(get_messages(response.wsgi_request))
                self.assertEqual(str(messages[0]), error_msg)

    @patch('stripe.PaymentIntent.create')
    def test_checkout_with_product(self, mock_stripe_create):
        """Test checkout view with product in cart - integration test"""
        # Set up the mock Stripe response
        mock_intent = MagicMock()
        mock_intent.client_secret = 'test_secret'
        mock_intent.id = 'test_intent_id'
        mock_stripe_create.return_value = mock_intent

        # Create a client and add a product to the cart
        client = Client()
        session = client.session
        session[settings.CART_SESSION_ID] = {
            f"product_{self.product.id}": {
                'quantity': 2,
                'price': str(self.product.price),
                'type': 'product'
            }
        }
        session.save()

        # Mock validate_stock to return success
        with patch('payments.utils.validate_stock') as mock_validate_stock:
            mock_validate_stock.return_value = (True, None)

            # Call the checkout view
            response = client.get(reverse('checkout'))

            # Check response status code
            self.assertEqual(response.status_code, 200)

            # Check that the template is used
            self.assertTemplateUsed(response, 'payments/checkout.html')

            # Check that the context contains the expected data
            self.assertIn('cart', response.context)
            self.assertIn('order_form', response.context)

    @patch('stripe.PaymentIntent.create')
    def test_checkout_with_rental(self, mock_stripe_create):
        """Test checkout view with crashpad rental in
        cart - integration test"""
        # Set up the mock Stripe response
        mock_intent = MagicMock()
        mock_intent.client_secret = 'test_secret'
        mock_intent.id = 'test_intent_id'
        mock_stripe_create.return_value = mock_intent

        # Set up dates for rental
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')

        # Create a client and add a rental to the cart
        client = Client()
        session = client.session
        session[settings.CART_SESSION_ID] = {
            f"rental_{self.crashpad.id}": {
                'quantity': 1,
                'price': str(self.crashpad.day_rate),
                'type': 'rental',
                'check_in': check_in,
                'check_out': check_out,
                'rental_days': 7,
                'daily_rate': str(self.crashpad.seven_day_rate),
                'total_price': str(Decimal('28.00'))
            }
        }
        session.save()

        # Mock validate_stock to return success
        with patch('payments.utils.validate_stock') as mock_validate_stock:
            mock_validate_stock.return_value = (True, None)

            # Call the checkout view
            response = client.get(reverse('checkout'))

            # Check response status code
            self.assertEqual(response.status_code, 200)

            # Check that the template is used
            self.assertTemplateUsed(response, 'payments/checkout.html')

            # Check that the context contains the expected data
            self.assertIn('cart', response.context)
            self.assertIn('order_form', response.context)

    def test_checkout_exception(self):
        """Test checkout view with an exception in validate_stock"""
        # We need to patch the validate_stock function at the module level
        with patch('payments.views.validate_stock') as mock_validate_stock:
            # Set up the mock to raise a ValueError
            mock_validate_stock.side_effect = ValueError(
                "not enough values to unpack (expected 2, got 0)")

            # Mock the Cart class
            with patch('payments.views.Cart') as mock_cart_class:
                # Create a mock cart instance
                mock_cart = MagicMock()
                mock_cart.__iter__.return_value = [{
                    'item':
                    self.product,
                    'quantity':
                    2,
                    'price':
                    str(self.product.price),
                    'type':
                    'product',
                    'total_price':
                    Decimal('59.98')
                }]
                mock_cart.__len__.return_value = 1

                # Make the Cart constructor return our mock cart
                mock_cart_class.return_value = mock_cart

                # Call the checkout view
                response = self.client.get(reverse('checkout'))

                # Check that we're redirected to cart_detail
                self.assertRedirects(response, reverse('cart_detail'))

                # Check for error message
                messages = list(get_messages(response.wsgi_request))
                self.assertEqual(
                    str(messages[0]),
                    "not enough values to unpack (expected 2, got 0)")
