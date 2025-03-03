import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase, RequestFactory
from django.contrib.sessions.models import Session
from django.conf import settings
from model_bakery import baker

from payments.webhook_handler import StripeWH_Handler
from orders.models import Order
from shop.models import Product
from rentals.models import Crashpad


class MockEvent:
    """Mock Stripe event for testing webhook handlers"""

    def __init__(self, event_type, data_object):
        self.type = event_type
        self.data = MagicMock()
        self.data.object = data_object


class TestStripeWebhookHandler(TestCase):

    def setUp(self):
        # Set up request factory
        self.factory = RequestFactory()

        # Create test models using model_bakery
        self.product = baker.make(Product,
                                  name='Test Product',
                                  description='Test Description',
                                  price=Decimal('10.00'),
                                  stock=5)

        # Create a test crashpad for rental items
        self.crashpad = baker.make(Crashpad,
                                   name='Test Crashpad',
                                   description='Test Description',
                                   day_rate=Decimal('10.00'))

        # Create a mock payment intent for successful payment
        self.mock_intent = MagicMock()
        self.mock_intent.id = 'pi_test123456'
        self.mock_intent.receipt_email = 'test@example.com'
        self.mock_intent.shipping = MagicMock()
        self.mock_intent.shipping.name = 'Test User'
        self.mock_intent.shipping.phone = '1234567890'
        self.mock_intent.shipping.address = MagicMock()
        self.mock_intent.shipping.address.country = 'US'
        self.mock_intent.shipping.address.postal_code = '12345'
        self.mock_intent.shipping.address.city = 'Test City'
        self.mock_intent.shipping.address.line1 = 'Test Address 1'
        self.mock_intent.shipping.address.line2 = 'Test Address 2'

        # Create metadata for the mock intent
        self.mock_intent.metadata = {
            'cart_items':
            json.dumps([{
                'id': self.product.id,
                'type': 'product',
                'name': self.product.name,
                'price': float(self.product.price),
                'quantity': 2
            }]),
            'rental_items':
            json.dumps([{
                'id': self.crashpad.id,
                'type': 'rental',
                'name': self.crashpad.name,
                'day_rate': float(self.crashpad.day_rate),
                'check_in': '2023-01-01',
                'check_out': '2023-01-05',
                'rental_days': 5
            }]),
            'cart_total':
            '20.00',
            'delivery_cost':
            '5.00',
            'handling_fee':
            '1.00',
            'grand_total':
            '26.00',
            'order_type':
            'MIXED',
            'order_form_data':
            json.dumps({
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'phone': '1234567890',
                'address_line1': 'Test Address 1',
                'address_line2': 'Test Address 2',
                'town_or_city': 'Test City',
                'postal_code': '12345',
                'country': 'US',
                'comments': ''
            })
        }

        # Create a mock session with proper expire_date
        expire_date = datetime.now() + timedelta(days=1)
        self.session = Session.objects.create(session_key='test_session_id',
                                              session_data='test_data',
                                              expire_date=expire_date)

        # Create a mock failed payment intent
        self.mock_failed_intent = MagicMock()
        self.mock_failed_intent.id = 'pi_failed123'
        self.mock_failed_intent.last_payment_error = {
            'message': 'Card declined'
        }
        self.mock_failed_intent.status = 'requires_payment_method'

    def test_handle_event(self):
        """Test handling a generic webhook event"""
        # Create request
        request = self.factory.post('/webhook/')

        # Create handler and event
        handler = StripeWH_Handler(request)
        event = MockEvent('generic.event', {})

        # Process the event
        response = handler.handle_event(event)

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'Unhandled webhook received')

    @patch('payments.webhook_handler.validate_stock')
    @patch('payments.webhook_handler.Cart')
    def test_handle_payment_intent_succeeded(self, mock_cart,
                                             mock_validate_stock):
        """Test handling a successful payment intent webhook"""
        # Configure mocks
        mock_validate_stock.return_value = (True, None)

        # Create a mock cart instance
        mock_cart_instance = MagicMock()
        mock_cart_instance.has_invalid_items.return_value = (False, {})
        mock_cart.return_value = mock_cart_instance

        # Create request
        request = self.factory.post('/webhook/')

        # Create handler and event
        handler = StripeWH_Handler(request)
        event = MockEvent('payment_intent.succeeded', self.mock_intent)

        # Process the event
        with patch('payments.webhook_handler.send_confirmation_email'):
            with patch(
                    'payments.webhook_handler.send_rental_confirmation_email'):
                response = handler.handle_payment_intent_succeeded(event)

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # Check that an order was created
        order = Order.objects.filter(stripe_piid='pi_test123456').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.first_name, 'Test')
        self.assertEqual(order.last_name, 'User')
        self.assertEqual(order.email, 'test@example.com')
        self.assertEqual(order.order_type, 'MIXED')

    @patch('payments.webhook_handler.validate_stock')
    @patch('payments.webhook_handler.Cart')
    def test_handle_payment_intent_succeeded_invalid_stock(
            self, mock_cart, mock_validate_stock):
        """Test handling a payment intent with invalid stock"""
        # Configure mocks
        mock_validate_stock.side_effect = ValueError("Product out of stock")

        # Create a mock cart instance
        mock_cart_instance = MagicMock()
        mock_cart_instance.has_invalid_items.return_value = (True, {
            "error":
            "Product out of stock"
        })
        mock_cart.return_value = mock_cart_instance

        # Create request
        request = self.factory.post('/webhook/')

        # Create handler and event
        handler = StripeWH_Handler(request)
        event = MockEvent('payment_intent.succeeded', self.mock_intent)

        # Process the event - we need to catch the ValueError
        try:
            handler.handle_payment_intent_succeeded(event)
            self.fail("Expected ValueError was not raised")
        except ValueError as e:
            self.assertEqual(str(e), "Product out of stock")

    @patch('stripe.PaymentIntent.retrieve')
    def test_handle_payment_intent_failed(self, mock_retrieve):
        """Test handling a failed payment intent webhook"""
        # Configure mock
        mock_retrieve.return_value = self.mock_failed_intent

        # Create request
        request = self.factory.post('/webhook/')

        # Create handler and event
        handler = StripeWH_Handler(request)
        # Use a MagicMock object instead of a dict for the event data
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = 'pi_failed123'
        event = MockEvent('payment_intent.payment_failed', mock_payment_intent)

        # Process the event
        response = handler.handle_payment_intent_failed(event)

        # Check response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['message'], 'Payment failure handled')

    @patch('django.contrib.sessions.backends.db.SessionStore')
    def test_clear_session_data(self, mock_session_store):
        """Test the _clear_session_data method"""
        # Configure mock
        mock_session = MagicMock()
        mock_session_store.return_value = mock_session
        mock_session.__contains__.side_effect = lambda key: key in {
            settings.CART_SESSION_ID, 'order_form_data'
        }

        # Create request
        request = self.factory.post('/webhook/')

        # Create handler
        handler = StripeWH_Handler(request)

        # Call the method
        handler._clear_session_data('test_session_id')

        # Verify session was cleared
        self.assertEqual(mock_session.__delitem__.call_count, 2)
        mock_session.save.assert_called()

    def test_webhook_integration_with_existing_order(self):
        """Test webhook handling when an order already exists"""
        # Create an existing order with the same payment intent ID
        baker.make(Order,
                   stripe_piid='pi_test123456',
                   first_name='Existing',
                   last_name='User',
                   email='existing@example.com',
                   order_total=Decimal('20.00'),
                   delivery_cost=Decimal('5.00'),
                   handling_fee=Decimal('1.00'),
                   grand_total=Decimal('26.00'))

        # Create request
        request = self.factory.post('/webhook/')

        # Create handler and event
        handler = StripeWH_Handler(request)
        event = MockEvent('payment_intent.succeeded', self.mock_intent)

        # Configure mock for validate_stock and Cart
        with patch('payments.webhook_handler.validate_stock',
                   return_value=(True, None)):
            with patch('payments.webhook_handler.Cart') as mock_cart:
                # Create a mock cart instance
                mock_cart_instance = MagicMock()
                mock_cart_instance.has_invalid_items.return_value = (False, {})
                mock_cart.return_value = mock_cart_instance

                # Process the event
                with patch('payments.webhook_handler.send_confirmation_email'):
                    with patch(
                            'payments.webhook_handler.'
                            'send_rental_confirmation_email'
                    ):
                        response = handler.handle_payment_intent_succeeded(
                            event)

        # Check response
        self.assertEqual(response.status_code, 200)

        # Verify the existing order wasn't modified
        # (first name should still be 'Existing')
        order = Order.objects.get(stripe_piid='pi_test123456')
        self.assertEqual(order.first_name, 'Existing')
        self.assertEqual(order.email, 'existing@example.com')
