from django.test import TestCase, RequestFactory
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta

from shop.models import Product
from rentals.models import Crashpad
from cart.cart import Cart
from cart.contexts import cart_summary
from model_bakery import baker


class MockSession(dict):
    """Mock session class that mimics Django's session behavior"""

    def __init__(self, *args, **kwargs):
        self.modified = False
        super().__init__(*args, **kwargs)


class CartContextsTest(TestCase):

    def setUp(self):
        """Set up test data"""
        # Create a request factory
        self.factory = RequestFactory()

        # Create a product
        self.product = baker.make(Product,
                                  name="Test Product",
                                  price=Decimal("29.99"),
                                  stock=10,
                                  is_active=True,
                                  _fill_optional=False)

        # Create a crashpad for rental
        self.crashpad = baker.make(Crashpad,
                                   name="Test Crashpad",
                                   day_rate=Decimal("5.00"),
                                   seven_day_rate=Decimal("4.00"),
                                   fourteen_day_rate=Decimal("3.00"),
                                   _fill_optional=False)

        # Set up dates for rental
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

        # Format dates for use in tests
        self.check_in = self.tomorrow.strftime('%Y-%m-%d')
        self.check_out = self.next_week.strftime('%Y-%m-%d')

    def test_empty_cart_context(self):
        """Test context with empty cart"""
        print("\n--- Running test_empty_cart_context ---")

        # Create a request with a fresh session
        request = self.factory.get('/')
        request.session = MockSession()

        # Get context
        context = cart_summary(request)
        print(f"Context: {context}")

        # Check context values
        self.assertEqual(context['cart_items'], [])
        self.assertEqual(context['cart_item_count'], 0)
        self.assertEqual(context['cart_total'], Decimal('0'))
        self.assertEqual(context['delivery_cost'], Decimal('0'))
        self.assertEqual(context['handling_fee'], Decimal('0'))
        self.assertEqual(context['grand_total'], Decimal('0'))
        self.assertEqual(context['order_type'], None)
        self.assertFalse(context['has_products'])
        self.assertFalse(context['has_rentals'])

    def test_products_only_context(self):
        """Test context with only products in cart"""
        print("\n--- Running test_products_only_context ---")

        # Create a request with a fresh session
        request = self.factory.get('/')
        request.session = MockSession()

        # Add product to cart
        cart = Cart(request)
        cart.add(self.product, quantity=2, item_type='product')

        # Get context
        context = cart_summary(request)
        print(f"Context: {context}")

        # Calculate expected values
        expected_cart_total = Decimal('29.99') * 2
        expected_delivery_cost = Decimal('0')
        if expected_cart_total < settings.FREE_DELIVERY_THRESHOLD:
            expected_delivery_cost = (
                Decimal(settings.STANDARD_DELIVERY_PERCENTAGE) *
                expected_cart_total / Decimal('100'))

        # Check context values
        self.assertEqual(len(context['cart_items']), 1)
        self.assertEqual(context['cart_item_count'], len(cart))
        self.assertEqual(context['cart_total'], expected_cart_total)
        self.assertEqual(context['delivery_cost'], expected_delivery_cost)
        self.assertEqual(context['handling_fee'], Decimal('0'))
        self.assertEqual(context['grand_total'],
                         expected_cart_total + expected_delivery_cost)
        self.assertEqual(context['order_type'], 'PRODUCTS_ONLY')
        self.assertTrue(context['has_products'])
        self.assertFalse(context['has_rentals'])
        self.assertEqual(context['product_items_sum'], expected_cart_total)
        self.assertEqual(context['product_items_subtotal'],
                         expected_cart_total + expected_delivery_cost)
        self.assertEqual(context['rental_items_sum'], Decimal('0'))
        self.assertEqual(context['rental_items_subtotal'], Decimal('0'))

    def test_rentals_only_context(self):
        """Test context with only rentals in cart"""
        print("\n--- Running test_rentals_only_context ---")

        # Create a request with a fresh session
        request = self.factory.get('/')
        request.session = MockSession()

        # Add rental to cart
        cart = Cart(request)
        dates = {'check_in': self.check_in, 'check_out': self.check_out}
        cart.add(self.crashpad, quantity=1, item_type='rental', dates=dates)

        # Get context
        context = cart_summary(request)
        print(f"Context: {context}")

        # Calculate expected values
        rental_days = 7  # Based on the dates we set
        daily_rate = Decimal('4.00')  # seven_day_rate for this duration
        expected_rental_total = daily_rate * rental_days
        expected_handling_fee = Decimal(str(settings.RENTAL_HANDLING_FEE))

        # Check context values
        self.assertEqual(len(context['cart_items']), 1)
        self.assertEqual(context['cart_item_count'], 1)
        self.assertEqual(context['cart_total'], expected_rental_total)
        self.assertEqual(context['delivery_cost'], Decimal('0'))
        self.assertEqual(context['handling_fee'], expected_handling_fee)
        self.assertEqual(context['grand_total'],
                         expected_rental_total + expected_handling_fee)
        self.assertEqual(context['order_type'], 'RENTALS_ONLY')
        self.assertFalse(context['has_products'])
        self.assertTrue(context['has_rentals'])
        self.assertEqual(context['product_items_sum'], Decimal('0'))
        self.assertEqual(context['product_items_subtotal'], Decimal('0'))
        self.assertEqual(context['rental_items_sum'], expected_rental_total)
        self.assertEqual(context['rental_items_subtotal'],
                         expected_rental_total + expected_handling_fee)

    def test_mixed_cart_context(self):
        """Test context with both products and rentals in cart"""
        print("\n--- Running test_mixed_cart_context ---")

        # Create a request with a fresh session
        request = self.factory.get('/')
        request.session = MockSession()

        # Add product and rental to cart
        cart = Cart(request)
        cart.add(self.product, quantity=2, item_type='product')

        dates = {'check_in': self.check_in, 'check_out': self.check_out}
        cart.add(self.crashpad, quantity=1, item_type='rental', dates=dates)

        # Get context
        context = cart_summary(request)
        print(f"Context: {context}")

        # Calculate expected values
        expected_product_total = Decimal('29.99') * 2
        rental_days = 7  # Based on the dates we set
        daily_rate = Decimal('4.00')  # seven_day_rate for this duration
        expected_rental_total = daily_rate * rental_days
        expected_cart_total = expected_product_total + expected_rental_total

        # Print the actual values from settings for debugging
        print(f"FREE_DELIVERY_THRESHOLD: {settings.FREE_DELIVERY_THRESHOLD}")
        print("STANDARD_DELIVERY_PERCENTAGE: "
              f"{settings.STANDARD_DELIVERY_PERCENTAGE}")
        print(f"Cart total: {expected_cart_total}")

        # Calculate delivery cost based on the entire cart total
        expected_delivery_cost = Decimal('0')
        if expected_cart_total < settings.FREE_DELIVERY_THRESHOLD:
            expected_delivery_cost = (
                Decimal(settings.STANDARD_DELIVERY_PERCENTAGE) *
                expected_product_total / Decimal('100'))

        # Print the calculated delivery cost for debugging
        print(f"Calculated delivery cost: {expected_delivery_cost}")
        print(f"Context delivery cost: {context['delivery_cost']}")

        expected_handling_fee = Decimal(str(settings.RENTAL_HANDLING_FEE))

        # Check context values
        self.assertEqual(len(context['cart_items']), 2)
        self.assertEqual(context['cart_item_count'], len(cart))
        self.assertEqual(context['cart_total'], expected_cart_total)

        # Use assertAlmostEqual for decimal comparison
        # to handle potential rounding issues
        self.assertAlmostEqual(context['delivery_cost'],
                               expected_delivery_cost,
                               places=2)

        self.assertEqual(context['handling_fee'], expected_handling_fee)

        # Use assertAlmostEqual for the grand total as well
        expected_grand_total = (expected_cart_total + expected_delivery_cost +
                                expected_handling_fee)
        self.assertAlmostEqual(context['grand_total'],
                               expected_grand_total,
                               places=2)

        self.assertEqual(context['order_type'], 'MIXED')
        self.assertTrue(context['has_products'])
        self.assertTrue(context['has_rentals'])
        self.assertEqual(context['product_items_sum'], expected_product_total)

        # Use assertAlmostEqual for the product subtotal
        expected_product_subtotal = (expected_product_total +
                                     expected_delivery_cost)
        self.assertAlmostEqual(context['product_items_subtotal'],
                               expected_product_subtotal,
                               places=2)

        self.assertEqual(context['rental_items_sum'], expected_rental_total)
        self.assertEqual(context['rental_items_subtotal'],
                         expected_rental_total + expected_handling_fee)
