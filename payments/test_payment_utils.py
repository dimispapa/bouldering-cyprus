from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.conf import settings

from payments.utils import (validate_stock, check_existing_order,
                            create_order_items, send_confirmation_email,
                            send_rental_confirmation_email)


class TestGetErrorMessage(TestCase):
    """Tests for the get_error_message function"""

    def test_insufficient_stock_error(self):
        """Test error message for insufficient stock"""
        # Create a mock error object with product attribute
        error_dict = MagicMock()
        error_dict.product = MagicMock()
        error_dict.product.name = "Test Product"
        error_dict.product.stock = 2

        # Call the function with the error key
        with patch('payments.utils.get_error_message') as mock_get_error:
            mock_get_error.return_value = \
                f"Sorry, only {error_dict.product.stock} units " \
                f"available for {error_dict.product.name}"
            result = mock_get_error('insufficient_stock')

            # Check the result
            self.assertIn(f"only {error_dict.product.stock} units", result)
            self.assertIn(error_dict.product.name, result)

    def test_dates_unavailable_error(self):
        """Test error message for unavailable dates"""
        # Create a mock error with crashpad attribute
        with patch('payments.utils.get_error_message') as mock_get_error:
            mock_get_error.return_value = \
                "Sorry, Test Crashpad is no longer available for " \
                "the selected dates"
            result = mock_get_error('dates_unavailable')

            # Check the result
            self.assertIn("no longer available", result)
            self.assertIn("Test Crashpad", result)

    def test_dates_in_past_error(self):
        """Test error message for dates in the past"""
        # Create a mock error with crashpad attribute
        with patch('payments.utils.get_error_message') as mock_get_error:
            mock_get_error.return_value = \
                "The selected dates for Test Crashpad are in the past"
            result = mock_get_error('dates_in_past')

            # Check the result
            self.assertIn("in the past", result)
            self.assertIn("Test Crashpad", result)


class TestValidateStock(TestCase):
    """Tests for the validate_stock function"""

    def test_valid_cart(self):
        """Test validation with a valid cart"""
        # Create a mock cart with no errors
        cart = MagicMock()
        cart.has_invalid_items.return_value = (False, None)

        # Call the function
        result, error = validate_stock(cart)

        # Check the result
        self.assertTrue(result)
        self.assertIsNone(error)
        cart.has_invalid_items.assert_called_once()

    def test_insufficient_stock_error(self):
        """Test validation with insufficient stock error"""
        # Create a mock cart with insufficient stock error
        cart = MagicMock()
        product = MagicMock()
        product.name = "Test Product"
        product.stock = 2

        error_dict = {'error': 'insufficient_stock', 'product': product}
        cart.has_invalid_items.return_value = (True, error_dict)

        # Call the function
        result, error = validate_stock(cart)

        # Check the result
        self.assertFalse(result)
        self.assertIn("Test Product only has 2 items in stock", error)
        cart.has_invalid_items.assert_called_once()

    def test_dates_unavailable_error(self):
        """Test validation with dates unavailable error"""
        # Create a mock cart with dates unavailable error
        cart = MagicMock()
        crashpad = MagicMock()
        crashpad.name = "Test Crashpad"

        error_dict = {
            'error': 'dates_unavailable',
            'crashpad': crashpad,
            'dates': '2023-01-01 to 2023-01-05'
        }
        cart.has_invalid_items.return_value = (True, error_dict)

        # Call the function
        result, error = validate_stock(cart)

        # Check the result
        self.assertFalse(result)
        self.assertIn("Test Crashpad is no longer available", error)
        self.assertIn("2023-01-01 to 2023-01-05", error)
        cart.has_invalid_items.assert_called_once()

    def test_dates_in_past_error(self):
        """Test validation with dates in past error"""
        # Create a mock cart with dates in past error
        cart = MagicMock()
        crashpad = MagicMock()
        crashpad.name = "Test Crashpad"

        error_dict = {
            'error': 'dates_in_past',
            'crashpad': crashpad,
            'dates': '2023-01-01 to 2023-01-05'
        }
        cart.has_invalid_items.return_value = (True, error_dict)

        # Call the function
        result, error = validate_stock(cart)

        # Check the result
        self.assertFalse(result)
        self.assertIn("dates 2023-01-01 to 2023-01-05", error)
        self.assertIn("are in the past", error)
        cart.has_invalid_items.assert_called_once()

    def test_unknown_error(self):
        """Test validation with unknown error"""
        # Create a mock cart with unknown error
        cart = MagicMock()
        error_dict = {'error': 'unknown_error'}
        cart.has_invalid_items.return_value = (True, error_dict)

        # Call the function
        result, error = validate_stock(cart)

        # Check the result
        self.assertFalse(result)
        self.assertEqual("An error occurred validating your cart.", error)
        cart.has_invalid_items.assert_called_once()


class TestCheckExistingOrder(TestCase):
    """Tests for the check_existing_order function"""

    @patch('payments.utils.time.sleep')
    @patch('payments.utils.Order.objects.filter')
    def test_order_found_immediately(self, mock_filter, mock_sleep):
        """Test when order is found immediately after initial delay"""
        # Setup mocks
        payment_intent = MagicMock()
        payment_intent.id = 'pi_test123'

        mock_order = MagicMock()
        mock_order.order_number = 'TEST123'

        # Configure filter to return the order on first call
        mock_filter.return_value.first.return_value = mock_order

        # Set retry settings for test
        settings.ORDER_CREATION_RETRIES = 3
        settings.ORDER_CREATION_RETRY_DELAY = 0.1

        # Call the function
        result = check_existing_order(payment_intent)

        # Check the result
        self.assertEqual(result, mock_order)
        mock_filter.assert_called_with(stripe_piid='pi_test123')
        mock_sleep.assert_called_once_with(0.1)  # Initial delay only

    @patch('payments.utils.time.sleep')
    @patch('payments.utils.Order.objects.filter')
    def test_order_found_after_retries(self, mock_filter, mock_sleep):
        """Test when order is found after a few retries"""
        # Setup mocks
        payment_intent = MagicMock()
        payment_intent.id = 'pi_test123'

        mock_order = MagicMock()
        mock_order.order_number = 'TEST123'

        # Configure filter to return None for first call, then the order
        mock_filter.return_value.first.side_effect = [None, None, mock_order]

        # Set retry settings for test
        settings.ORDER_CREATION_RETRIES = 3
        settings.ORDER_CREATION_RETRY_DELAY = 0.1

        # Call the function
        result = check_existing_order(payment_intent)

        # Check the result
        self.assertEqual(result, mock_order)
        self.assertEqual(mock_filter.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)  # Initial + 2 retries

    @patch('payments.utils.time.sleep')
    @patch('payments.utils.Order.objects.filter')
    def test_order_not_found(self, mock_filter, mock_sleep):
        """Test when order is not found after all retries"""
        # Setup mocks
        payment_intent = MagicMock()
        payment_intent.id = 'pi_test123'

        # Configure filter to always return None
        mock_filter.return_value.first.return_value = None

        # Set retry settings for test
        settings.ORDER_CREATION_RETRIES = 3
        settings.ORDER_CREATION_RETRY_DELAY = 0.1

        # Call the function
        result = check_existing_order(payment_intent)

        # Check the result
        self.assertIsNone(result)
        self.assertEqual(mock_filter.call_count, 4)  # Initial + 3 retries
        self.assertEqual(mock_sleep.call_count, 3)  # Initial + 2 retries


class TestCreateOrderItems(TestCase):
    """Tests for the create_order_items function"""

    @patch('orders.models.Order')
    @patch('shop.models.Product')
    @patch('rentals.models.Crashpad')
    @patch('orders.models.OrderItem.objects.create')
    @patch('rentals.models.CrashpadBooking.objects.create')
    def test_create_product_order_items(self, mock_booking_create,
                                        mock_order_item_create, mock_crashpad,
                                        mock_product, mock_order):
        """Test creating order items for products"""
        # Create mock order and product
        order = mock_order()
        order.pk = 1
        order.order_number = "TEST123"

        product = mock_product()
        product.name = "Test Product"
        product.stock = 10

        # Create a cart with a product item
        cart = [{
            'type': 'product',
            'item': product,
            'quantity': 2,
            'total_price': Decimal("39.98")
        }]

        # Call the function
        create_order_items(order, cart)

        # Check order items were created
        mock_order_item_create.assert_called_once_with(
            order=order,
            product=product,
            quantity=2,
            item_total=Decimal("39.98"))

        # Check stock was updated
        self.assertEqual(product.stock, 8)
        product.save.assert_called_once()

        # Check booking was not created
        mock_booking_create.assert_not_called()

    @patch('orders.models.Order')
    @patch('shop.models.Product')
    @patch('rentals.models.Crashpad')
    @patch('orders.models.OrderItem.objects.create')
    @patch('rentals.models.CrashpadBooking.objects.create')
    def test_create_rental_order_items(self, mock_booking_create,
                                       mock_order_item_create, mock_crashpad,
                                       mock_product, mock_order):
        """Test creating order items for rentals"""
        # Create mock order and crashpad
        order = mock_order()
        order.pk = 1
        order.order_number = "TEST123"

        crashpad = mock_crashpad()
        crashpad.name = "Test Crashpad"

        # Create a cart with a rental item
        today = date.today()
        check_in = today + timedelta(days=1)
        check_out = today + timedelta(days=4)

        cart = [{
            'type': 'rental',
            'item': crashpad,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'daily_rate': Decimal("10.00"),
            'rental_days': 3,
            'total_price': Decimal("30.00")
        }]

        # Call the function
        create_order_items(order, cart)

        # Check booking was created
        mock_booking_create.assert_called_once_with(
            crashpad=crashpad,
            order=order,
            check_in=check_in,
            check_out=check_out,
            daily_rate=Decimal("10.00"),
            rental_days=3,
            total_price=Decimal("30.00"))

        # Check order item was not created
        mock_order_item_create.assert_not_called()

    @patch('orders.models.Order')
    @patch('shop.models.Product')
    @patch('rentals.models.Crashpad')
    @patch('orders.models.OrderItem.objects.create')
    @patch('rentals.models.CrashpadBooking.objects.create')
    def test_create_mixed_order_items(self, mock_booking_create,
                                      mock_order_item_create, mock_crashpad,
                                      mock_product, mock_order):
        """Test creating order items for both products and rentals"""
        # Create mock order, product and crashpad
        order = mock_order()
        order.pk = 1
        order.order_number = "TEST123"

        product = mock_product()
        product.name = "Test Product"
        product.stock = 10

        crashpad = mock_crashpad()
        crashpad.name = "Test Crashpad"

        # Create a cart with both product and rental items
        today = date.today()
        check_in = today + timedelta(days=1)
        check_out = today + timedelta(days=4)

        cart = [{
            'type': 'product',
            'item': product,
            'quantity': 1,
            'total_price': Decimal("19.99")
        }, {
            'type': 'rental',
            'item': crashpad,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'daily_rate': Decimal("10.00"),
            'rental_days': 3,
            'total_price': Decimal("30.00")
        }]

        # Call the function
        create_order_items(order, cart)

        # Check order item was created
        mock_order_item_create.assert_called_once_with(
            order=order,
            product=product,
            quantity=1,
            item_total=Decimal("19.99"))

        # Check booking was created
        mock_booking_create.assert_called_once_with(
            crashpad=crashpad,
            order=order,
            check_in=check_in,
            check_out=check_out,
            daily_rate=Decimal("10.00"),
            rental_days=3,
            total_price=Decimal("30.00"))

        # Check stock was updated
        self.assertEqual(product.stock, 9)
        product.save.assert_called_once()

    def test_order_without_pk(self):
        """Test creating order items for an order without a primary key"""
        # Create an order without a primary key
        order = MagicMock()
        order.pk = None

        # Create a cart
        cart = [{
            'type': 'product',
            'item': MagicMock(),
            'quantity': 1,
            'total_price': Decimal("19.99")
        }]

        # Call the function and expect an error
        with self.assertRaises(ValueError):
            create_order_items(order, cart)


class TestSendConfirmationEmail(TestCase):
    """Tests for the send_confirmation_email function"""

    @patch('payments.utils.send_mail')
    def test_send_confirmation_email_success(self, mock_send_mail):
        """Test sending confirmation email successfully"""
        # Create mock order
        order = MagicMock()
        order.order_number = "TEST123"
        order.email = "test@example.com"

        # Configure mock
        mock_send_mail.return_value = 1

        # Call the function
        result = send_confirmation_email(order)

        # Check the result
        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check the arguments
        args = mock_send_mail.call_args[0]
        self.assertIn(order.email, args[3])  # recipient email

    @patch('payments.utils.send_mail')
    def test_send_confirmation_email_failure(self, mock_send_mail):
        """Test sending confirmation email with failure"""
        # Create mock order
        order = MagicMock()
        order.order_number = "TEST123"
        order.email = "test@example.com"

        # Configure mock to raise an exception
        mock_send_mail.side_effect = Exception("Email error")

        # Call the function
        result = send_confirmation_email(order)

        # Check the result
        self.assertFalse(result)
        mock_send_mail.assert_called_once()


class TestSendRentalConfirmationEmail(TestCase):
    """Tests for the send_rental_confirmation_email function"""

    @patch('payments.utils.send_mail')
    def test_send_rental_confirmation_email_success(self, mock_send_mail):
        """Test sending rental confirmation email successfully"""
        # Create mock order
        order = MagicMock()
        order.order_number = "TEST123"
        order.email = "test@example.com"

        # Configure mock
        mock_send_mail.return_value = 1

        # Call the function
        result = send_rental_confirmation_email(order)

        # Check the result
        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check the arguments
        args = mock_send_mail.call_args[0]
        self.assertIn(order.email, args[3])  # recipient email

    @patch('payments.utils.send_mail')
    def test_send_rental_confirmation_email_failure(self, mock_send_mail):
        """Test sending rental confirmation email with failure"""
        # Create mock order
        order = MagicMock()
        order.order_number = "TEST123"
        order.email = "test@example.com"

        # Configure mock to raise an exception
        mock_send_mail.side_effect = Exception("Email error")

        # Call the function
        result = send_rental_confirmation_email(order)

        # Check the result
        self.assertFalse(result)
        mock_send_mail.assert_called_once()
