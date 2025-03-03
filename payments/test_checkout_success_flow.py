from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
import json
import stripe
from unittest.mock import patch, MagicMock

from orders.models import Order, OrderItem
from shop.models import Product
from rentals.models import Crashpad, CrashpadBooking
from model_bakery import baker
from payments.views import create_or_return_order


class CheckoutSuccessFlowTest(TestCase):
    """Test the complete checkout success flow"""

    def setUp(self):
        """Set up test data"""
        # Create a user
        self.user = User.objects.create_user(username='testuser',
                                             email='test@example.com',
                                             password='testpassword')

        # Create a product
        self.product = baker.make(Product,
                                  name="Test Product",
                                  price=Decimal("29.99"),
                                  stock=10,
                                  is_active=True)

        # Create a crashpad - using correct field names from your model
        self.crashpad = baker.make(Crashpad,
                                   name="Test Crashpad",
                                   brand="Test Brand",
                                   model="Test Model",
                                   dimensions="100x100x10",
                                   description="Test Description",
                                   day_rate=Decimal("10.00"),
                                   seven_day_rate=Decimal("8.00"),
                                   fourteen_day_rate=Decimal("7.00"))

        # Set up the client and request factory
        self.client = Client()
        self.factory = RequestFactory()

        # Create a mock payment intent with correct cart item structure
        self.payment_intent = MagicMock()
        self.payment_intent.id = "pi_test_123456789"
        self.payment_intent.status = "succeeded"
        self.payment_intent.amount = 3499  # $34.99
        self.payment_intent.metadata = {
            'cart_items':
            json.dumps([{
                'id': self.product.id,
                'type': 'product',
                'name': self.product.name,
                'price': float(self.product.price),
                'quantity': 1
            }]),
            'rental_items':
            json.dumps([{
                'id': self.crashpad.id,
                'type': 'rental',
                'name': self.crashpad.name,
                'day_rate': float(self.crashpad.day_rate
                                  ),  # Match the field name in your Cart class
                'check_in': '2023-01-01',
                'check_out': '2023-01-05',
                'rental_days': 5
            }]),
            'cart_total':
            "79.99",
            'delivery_cost':
            "5.00",
            'handling_fee':
            "2.50",
            'grand_total':
            "87.49",
            'order_type':
            "MIXED",
            'order_form_data':
            json.dumps({
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'phone': '1234567890',
                'address_line1': 'Test Address',
                'address_line2': '',
                'town_or_city': 'Test City',
                'postal_code': '12345',
                'country': 'CY',
                'comments': ''
            })
        }

        # Set up session
        session = self.client.session
        session['order_form_data'] = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address_line1': 'Test Address',
            'address_line2': '',
            'town_or_city': 'Test City',
            'postal_code': '12345',
            'country': 'CY',
            'comments': ''
        }
        session.save()

    @patch('stripe.PaymentIntent.retrieve')
    @patch('payments.views.create_or_return_order')
    def test_checkout_success_view(self, mock_create_order, mock_retrieve):
        """Test the checkout success view with a valid payment intent"""
        # Set up the mocks
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_123456789"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 3499  # $34.99
        mock_retrieve.return_value = mock_payment_intent

        # Create a mock order
        mock_order = baker.make(Order,
                                order_number="BC-20230101-ABCDEF",
                                stripe_piid=mock_payment_intent.id,
                                order_total=Decimal("29.99"),
                                delivery_cost=Decimal("5.00"),
                                grand_total=Decimal("34.99"))
        mock_create_order.return_value = mock_order

        # Get the URL for the checkout success view with the payment intent ID
        url = reverse(
            'checkout_success') + f"?payment_intent={mock_payment_intent.id}"

        # Make a GET request to the view
        response = self.client.get(url, follow=True)

        # Check that the response is successful
        # Since your view redirects to another URL after processing,
        # we should check for 200 after following redirects
        self.assertEqual(response.status_code, 200)

        # Check that the create_or_return_order function was called
        mock_create_order.assert_called_once()

    @patch('stripe.PaymentIntent.retrieve')
    def test_checkout_success_view_with_failed_payment(self, mock_retrieve):
        """Test the checkout success view with a failed payment"""
        # Set up the mock
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_123456789"
        # Failed payment
        mock_payment_intent.status = "requires_payment_method"
        mock_retrieve.return_value = mock_payment_intent

        # Get the URL for the checkout success view with the payment intent ID
        url = reverse(
            'checkout_success') + f"?payment_intent={mock_payment_intent.id}"

        # Make a GET request to the view
        response = self.client.get(url)

        # Check that the response is a redirect to the checkout page
        self.assertRedirects(response,
                             reverse('checkout'),
                             fetch_redirect_response=False)

    def test_checkout_success_view_with_no_payment_intent(self):
        """Test the checkout success view with no payment intent"""
        # Get the URL for the checkout success view without a payment intent
        url = reverse('checkout_success')

        # Make a GET request to the view
        response = self.client.get(url)

        # Check that the response is a redirect to the checkout page
        self.assertRedirects(response,
                             reverse('checkout'),
                             fetch_redirect_response=False)

    @patch('stripe.PaymentIntent.retrieve')
    def test_checkout_success_view_with_stripe_error(self, mock_retrieve):
        """Test the checkout success view with a Stripe error"""
        # Set up the mock to raise a Stripe error
        mock_retrieve.side_effect = stripe.error.StripeError(
            "Test Stripe error")

        # Get the URL for the checkout success view with the payment intent ID
        url = reverse('checkout_success') + "?payment_intent=pi_test_123456789"

        # Make a GET request to the view
        response = self.client.get(url)

        # Check that the response is a redirect to the checkout page
        self.assertRedirects(response,
                             reverse('checkout'),
                             fetch_redirect_response=False)

    @patch('payments.views.check_existing_order')
    @patch('payments.utils.validate_stock')
    @patch('payments.views.Cart')
    def test_create_or_return_order_existing_order(self, mock_cart,
                                                   mock_validate_stock,
                                                   mock_check_existing):
        """Test retrieving an existing order"""
        # Set up the mocks
        existing_order = baker.make(Order,
                                    order_number="BC-20230101-ABCDEF",
                                    stripe_piid=self.payment_intent.id)
        mock_check_existing.return_value = existing_order

        # Mock the Cart class to return valid stock
        mock_cart_instance = MagicMock()
        mock_cart_instance.has_invalid_items.return_value = (False, {})
        mock_cart.return_value = mock_cart_instance

        # Create a request
        request = self.factory.get(reverse('checkout_success'))
        request.session = self.client.session

        # Call the function
        order = create_or_return_order(request, self.payment_intent)

        # Check that the existing order was returned
        self.assertEqual(order, existing_order)

    @patch('payments.views.check_existing_order')
    @patch('payments.utils.validate_stock')
    @patch('payments.views.Cart')
    def test_create_or_return_order_with_invalid_stock(self, mock_cart,
                                                       mock_validate_stock,
                                                       mock_check_existing):
        """Test creating an order with invalid stock"""
        # Set up the mocks
        mock_check_existing.return_value = None

        # Mock the Cart class to return invalid stock
        mock_cart_instance = MagicMock()
        mock_cart_instance.has_invalid_items.return_value = (True, {
            'error':
            'Product out of stock'
        })
        mock_cart.return_value = mock_cart_instance

        mock_validate_stock.side_effect = ValueError("Product out of stock")

        # Create a request
        request = self.factory.get(reverse('checkout_success'))
        request.session = self.client.session

        # Call the function and check that it raises a ValueError
        with self.assertRaises(ValueError):
            create_or_return_order(request, self.payment_intent)

    @patch('stripe.PaymentIntent.retrieve')
    @patch('payments.views.create_or_return_order')
    def test_checkout_success_template_with_products_and_rentals(
            self, mock_create_order, mock_retrieve):
        """Test the checkout success template with both products and rentals"""
        # Create an order with baker.make
        order = baker.make(Order,
                           first_name="Test",
                           last_name="User",
                           email="test@example.com",
                           phone="1234567890",
                           country="CY",
                           postal_code="12345",
                           town_or_city="Test City",
                           address_line1="Test Address",
                           order_total=Decimal("79.99"),
                           delivery_cost=Decimal("5.00"),
                           handling_fee=Decimal("2.50"),
                           grand_total=Decimal("87.49"),
                           stripe_piid="pi_test_123456789",
                           order_type="MIXED")

        # Create an OrderItem with baker.make
        baker.make(OrderItem,
                   order=order,
                   product=self.product,
                   quantity=1,
                   item_total=Decimal("29.99"))

        # Use datetime objects for dates
        from datetime import datetime
        check_in = datetime.strptime("2023-01-01", "%Y-%m-%d").date()
        check_out = datetime.strptime("2023-01-05", "%Y-%m-%d").date()

        # Create a CrashpadBooking with baker.make
        baker.make(CrashpadBooking,
                   crashpad=self.crashpad,
                   order=order,
                   check_in=check_in,
                   check_out=check_out,
                   rental_days=5,
                   daily_rate=Decimal("10.00"),
                   total_price=Decimal("50.00"),
                   status="confirmed")

        # Set up the mock to return the payment intent
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = order.stripe_piid
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 8749  # $87.49
        mock_retrieve.return_value = mock_payment_intent

        # Mock create_or_return_order to return our pre-created order
        mock_create_order.return_value = order

        # Get the URL for the checkout success page with the payment intent
        url = reverse(
            'checkout_success') + f"?payment_intent={order.stripe_piid}"

        # Make a GET request to the view
        response = self.client.get(url, follow=True)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that the template contains the order details
        self.assertContains(response, order.order_number)
        self.assertContains(response, order.email)
        self.assertContains(response, "Test Product")

        # Check that the template contains the delivery details
        self.assertContains(response, order.first_name)
        self.assertContains(response, order.last_name)
        self.assertContains(response, order.address_line1)
        self.assertContains(response, order.town_or_city)
        self.assertContains(response, order.postal_code)

        # Check that the template contains the order summary
        self.assertContains(response, f"€{order.order_total}")
        self.assertContains(response, f"€{order.delivery_cost}")
        self.assertContains(response, f"€{order.handling_fee}")
        self.assertContains(response, f"€{order.grand_total}")

        # Check that the template contains the success message and icons
        self.assertContains(response, "Thank you for your order!")
        self.assertContains(response, "fa-circle-check")

        # Check that the template contains the progress bar
        self.assertContains(response, "progressbar--step-3")
