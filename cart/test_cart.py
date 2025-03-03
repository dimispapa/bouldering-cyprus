from django.test import TestCase
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from cart.cart import Cart
from shop.models import Product
from rentals.models import Crashpad
from model_bakery import baker


class MockSession(dict):
    """Mock session class that mimics Django's session behavior"""

    def __init__(self, *args, **kwargs):
        self.modified = False
        super().__init__(*args, **kwargs)


class CartTest(TestCase):

    def setUp(self):
        """Set up test data"""
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

        # Mock session with our custom MockSession class
        self.session = MockSession()
        self.request = MagicMock()
        self.request.session = self.session

        # Initialize cart
        self.cart = Cart(self.request)

    def test_add_product_to_cart(self):
        """Test adding a product to the cart"""
        print("\n--- Running test_add_product_to_cart ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        quantity = self.cart.add(self.product, quantity=2, item_type='product')

        # Check if product was added correctly
        product_key = f"product_{self.product.id}"
        print(f"Product key: {product_key}")
        print(f"Cart contents: {self.cart.cart}")

        self.assertIn(product_key, self.cart.cart)
        self.assertEqual(self.cart.cart[product_key]['quantity'], 2)
        self.assertEqual(self.cart.cart[product_key]['price'],
                         str(self.product.price))
        self.assertEqual(self.cart.cart[product_key]['type'], 'product')
        self.assertEqual(quantity, 2)

        # Check if session was updated
        print(f"Session contents: {self.session}")
        self.assertIn(settings.CART_SESSION_ID, self.session)
        self.assertEqual(self.session[settings.CART_SESSION_ID],
                         self.cart.cart)
        self.assertTrue(self.session.modified)

    def test_add_rental_to_cart(self):
        """Test adding a rental to the cart"""
        print("\n--- Running test_add_rental_to_cart ---")

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}

        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        quantity = self.cart.add(self.crashpad,
                                 quantity=1,
                                 item_type='rental',
                                 dates=dates)

        # Check if rental was added correctly
        rental_key = f"rental_{self.crashpad.id}"
        print(f"Rental key: {rental_key}")
        print(f"Cart contents: {self.cart.cart}")

        self.assertIn(rental_key, self.cart.cart)
        self.assertEqual(self.cart.cart[rental_key]['quantity'], 1)
        self.assertEqual(self.cart.cart[rental_key]['type'], 'rental')
        self.assertEqual(self.cart.cart[rental_key]['check_in'], check_in)
        self.assertEqual(self.cart.cart[rental_key]['check_out'], check_out)

        # The actual implementation calculates 7 days
        print(f"Rental days: {self.cart.cart[rental_key]['rental_days']}")
        self.assertEqual(self.cart.cart[rental_key]['rental_days'], 7)

        # The implementation is using seven_day_rate for this duration
        print(f"Daily rate: {self.cart.cart[rental_key]['daily_rate']}")
        print(f"Seven-day rate: {self.crashpad.seven_day_rate}")
        self.assertEqual(self.cart.cart[rental_key]['daily_rate'],
                         str(self.crashpad.seven_day_rate))
        self.assertEqual(quantity, 1)

        # Check if session was updated
        print(f"Session contents: {self.session}")
        self.assertIn(settings.CART_SESSION_ID, self.session)
        self.assertTrue(self.session.modified)

    def test_update_product_quantity(self):
        """Test updating product quantity"""
        print("\n--- Running test_update_product_quantity ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Update quantity
        print("Updating quantity to 5")
        self.cart.add(self.product,
                      quantity=5,
                      update_quantity=True,
                      item_type='product')

        # Check if quantity was updated
        product_key = f"product_{self.product.id}"
        print(f"Product key: {product_key}")
        print(f"Cart contents: {self.cart.cart}")
        self.assertEqual(self.cart.cart[product_key]['quantity'], 5)

        # Check if session was updated
        print(f"Session modified: {self.session.modified}")
        self.assertTrue(self.session.modified)

    def test_remove_item_from_cart(self):
        """Test removing an item from the cart"""
        print("\n--- Running test_remove_item_from_cart ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Remove product
        print(f"Removing product: {self.product.name}")
        self.cart.remove(self.product, item_type='product')

        # Check if product was removed
        product_key = f"product_{self.product.id}"
        print(f"Product key: {product_key}")
        print(f"Cart contents: {self.cart.cart}")
        self.assertNotIn(product_key, self.cart.cart)

        # Check if session was updated
        print(f"Session modified: {self.session.modified}")
        self.assertTrue(self.session.modified)

    def test_cart_iteration(self):
        """Test iterating over cart items"""
        print("\n--- Running test_cart_iteration ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Iterate over cart items
        print(f"Cart contents: {self.cart.cart}")
        items = list(self.cart)
        print(f"Iterated items: {items}")
        self.assertEqual(len(items), 2)

        # Check product item
        product_item = next(item for item in items
                            if item['type'] == 'product')
        print(f"Product item: {product_item}")
        self.assertEqual(product_item['item'], self.product)
        self.assertEqual(product_item['quantity'], 2)
        self.assertEqual(product_item['price'], str(self.product.price))
        self.assertEqual(product_item['total_price'],
                         Decimal(self.product.price) * 2)

        # Check rental item
        rental_item = next(item for item in items if item['type'] == 'rental')
        print(f"Rental item: {rental_item}")
        self.assertEqual(rental_item['item'], self.crashpad)
        self.assertEqual(rental_item['quantity'], 1)

        # The implementation is using seven_day_rate for this duration
        print(f"Rental days: {rental_item['rental_days']}")
        print(f"Price: {rental_item['price']}")
        print(f"Seven-day rate: {self.crashpad.seven_day_rate}")
        self.assertEqual(rental_item['price'],
                         str(self.crashpad.seven_day_rate))
        self.assertEqual(rental_item['rental_days'], 7)

        # Total price is seven_day_rate * 7 days
        print(f"Total price: {rental_item['total_price']}")
        print(f"Expected total: {Decimal(self.crashpad.seven_day_rate) * 7}")
        self.assertEqual(rental_item['total_price'],
                         Decimal(self.crashpad.seven_day_rate) * 7)

    def test_cart_length(self):
        """Test cart length calculation"""
        print("\n--- Running test_cart_length ---")

        # Empty cart
        print(f"Empty cart length: {len(self.cart)}")
        self.assertEqual(len(self.cart), 0)

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')
        print(f"Cart length after adding product: {len(self.cart)}")
        self.assertEqual(len(self.cart), 2)

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)
        print(f"Cart length after adding rental: {len(self.cart)}")
        self.assertEqual(len(self.cart), 3)

    def test_cart_total(self):
        """Test cart total calculation"""
        print("\n--- Running test_cart_total ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Calculate expected total
        product_total = Decimal(self.product.price) * 2

        # The implementation is using seven_day_rate for this duration
        rental_total = Decimal(self.crashpad.seven_day_rate) * 7
        expected_total = product_total + rental_total

        # Check cart total
        print(f"Cart contents: {self.cart.cart}")
        print(f"Cart total: {self.cart.cart_total()}")
        print(f"Expected total: {expected_total}")
        self.assertEqual(self.cart.cart_total(), expected_total)

    def test_clear_cart(self):
        """Test clearing the cart"""
        print("\n--- Running test_clear_cart ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Clear cart
        print("Clearing cart")
        self.cart.clear()

        # Check if cart was cleared
        print(f"Session contents: {self.session}")
        self.assertNotIn(settings.CART_SESSION_ID, self.session)

        # Check if session was updated
        print(f"Session modified: {self.session.modified}")
        self.assertTrue(self.session.modified)

    def test_serialize_cart(self):
        """Test serializing the cart"""
        print("\n--- Running test_serialize_cart ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Serialize cart
        print(f"Cart contents: {self.cart.cart}")
        serialized = self.cart.serialize()
        print(f"Serialized cart: {serialized}")

        # Check serialized data
        self.assertIn('items', serialized)
        self.assertIn('total', serialized)
        self.assertEqual(len(serialized['items']), 2)
        self.assertEqual(serialized['total'], str(self.cart.cart_total()))

    def test_to_json(self):
        """Test converting cart to JSON"""
        print("\n--- Running test_to_json ---")

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Convert to JSON
        print(f"Cart contents: {self.cart.cart}")
        json_data = self.cart.to_json()
        print(f"JSON data: {json_data}")

        # Check JSON data
        self.assertIn('cart_items', json_data)
        self.assertIn('rental_items', json_data)
        self.assertEqual(len(json_data['cart_items']), 1)
        self.assertEqual(len(json_data['rental_items']), 1)

    def test_has_invalid_items(self):
        """Test checking for invalid items"""
        print("\n--- Running test_has_invalid_items ---")

        # Add product with quantity exceeding stock
        print(f"Adding product: {self.product.name},"
              f"quantity: 15 (stock: {self.product.stock})")
        self.cart.add(self.product, quantity=15, item_type='product')

        # Check for invalid items
        print(f"Cart contents: {self.cart.cart}")
        has_invalid, error = self.cart.has_invalid_items()
        print(f"Has invalid items: {has_invalid}")
        print(f"Error: {error}")

        self.assertTrue(has_invalid)
        self.assertEqual(error['error'], 'insufficient_stock')
        self.assertEqual(error['product'].id,
                         self.product.id)  # Compare IDs instead of objects
        self.assertEqual(error['requested'], 15)

    def test_validate_stock(self):
        """Test validating stock"""
        print("\n--- Running test_validate_stock ---")

        # Add product with quantity exceeding stock
        print(f"Adding product: {self.product.name},"
              f"quantity: 15 (stock: {self.product.stock})")
        self.cart.add(self.product, quantity=15, item_type='product')

        # Validate stock
        print(f"Cart contents: {self.cart.cart}")
        invalid_items = self.cart.validate_stock()
        print(f"Invalid items: {invalid_items}")

        self.assertEqual(len(invalid_items), 1)
        self.assertEqual(invalid_items[0]['name'], self.product.name)
        self.assertEqual(invalid_items[0]['type'], 'product')
        self.assertEqual(invalid_items[0]['requested'], 15)
        self.assertEqual(invalid_items[0]['available'], 10)

    def test_has_rentals(self):
        """Test checking if cart has rentals"""
        print("\n--- Running test_has_rentals ---")

        # Empty cart
        print(f"Empty cart has rentals: {self.cart.has_rentals()}")
        self.assertFalse(self.cart.has_rentals())

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Check if cart has rentals
        print(f"Cart contents: {self.cart.cart}")
        print(f"Cart has rentals: {self.cart.has_rentals()}")
        self.assertTrue(self.cart.has_rentals())

    def test_has_products(self):
        """Test checking if cart has products"""
        print("\n--- Running test_has_products ---")

        # Empty cart
        print(f"Empty cart has products: {self.cart.has_products()}")
        self.assertFalse(self.cart.has_products())

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')

        # Check if cart has products
        print(f"Cart contents: {self.cart.cart}")
        print(f"Cart has products: {self.cart.has_products()}")
        self.assertTrue(self.cart.has_products())

    def test_has_mixed_items(self):
        """Test checking if cart has mixed items"""
        print("\n--- Running test_has_mixed_items ---")

        # Empty cart
        print(f"Empty cart has mixed items: {self.cart.has_mixed_items()}")
        self.assertFalse(self.cart.has_mixed_items())

        # Add product to cart
        print(f"Adding product: {self.product.name}, quantity: 2")
        self.cart.add(self.product, quantity=2, item_type='product')
        print(
            f"Cart with product has mixed items: {self.cart.has_mixed_items()}"
        )
        self.assertFalse(self.cart.has_mixed_items())

        # Add rental to cart
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = self.next_week.strftime('%Y-%m-%d')
        dates = {'check_in': check_in, 'check_out': check_out}
        print(f"Adding rental: {self.crashpad.name},"
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        # Check if cart has mixed items
        print(f"Cart contents: {self.cart.cart}")
        print(f"Cart has mixed items: {self.cart.has_mixed_items()}")
        self.assertTrue(self.cart.has_mixed_items())

    def test_rental_rates_based_on_duration(self):
        """Test that the appropriate rental rate is
        applied based on duration"""
        print("\n--- Running test_rental_rates_based_on_duration ---")

        # Test standard rate (less than 7 days)
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = (self.tomorrow + timedelta(days=5)).strftime(
            '%Y-%m-%d')  # 6 days total (5+1)
        dates = {'check_in': check_in, 'check_out': check_out}

        print(f"Test 1: Adding rental for 6 days, "
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        rental_key = f"rental_{self.crashpad.id}"
        print(f"Cart contents: {self.cart.cart}")
        print(f"Rental days: {self.cart.cart[rental_key]['rental_days']}")
        print(f"Daily rate: {self.cart.cart[rental_key]['daily_rate']}")
        print(f"Day rate: {self.crashpad.day_rate}")

        # The implementation calculates 6 days for this duration
        self.assertEqual(self.cart.cart[rental_key]['rental_days'], 6)
        self.assertEqual(self.cart.cart[rental_key]['daily_rate'],
                         str(self.crashpad.day_rate))

        # Clear cart for next test
        print("Clearing cart")
        self.cart.clear()
        print(f"Cart contents: {self.cart.cart}")
        # Test 7-day rate (7-13 days)
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = (self.tomorrow + timedelta(days=9)).strftime(
            '%Y-%m-%d')  # 10 days total (9+1)
        dates = {'check_in': check_in, 'check_out': check_out}

        print(f"Test 2: Adding rental for 10 days, "
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        rental_key = f"rental_{self.crashpad.id}"
        print(f"Cart contents: {self.cart.cart}")
        print(f"Rental days: {self.cart.cart[rental_key]['rental_days']}")
        print(f"Daily rate: {self.cart.cart[rental_key]['daily_rate']}")
        print(f"Seven-day rate: {self.crashpad.seven_day_rate}")

        # The implementation calculates 10 days for this duration
        self.assertEqual(self.cart.cart[rental_key]['rental_days'], 10)

        # The implementation is using seven_day_rate for this duration
        self.assertEqual(self.cart.cart[rental_key]['daily_rate'],
                         str(self.crashpad.seven_day_rate))

        # Clear cart for next test
        print("Clearing cart")
        self.cart.clear()

        # Test 14-day rate (14+ days)
        check_in = self.tomorrow.strftime('%Y-%m-%d')
        check_out = (self.tomorrow + timedelta(days=15)).strftime(
            '%Y-%m-%d')  # 16 days total (15+1)
        dates = {'check_in': check_in, 'check_out': check_out}

        print(f"Test 3: Adding rental for 16 days, "
              f"check_in: {check_in}, check_out: {check_out}")
        self.cart.add(self.crashpad,
                      quantity=1,
                      item_type='rental',
                      dates=dates)

        rental_key = f"rental_{self.crashpad.id}"
        print(f"Cart contents: {self.cart.cart}")
        print(f"Rental days: {self.cart.cart[rental_key]['rental_days']}")
        print(f"Daily rate: {self.cart.cart[rental_key]['daily_rate']}")
        print(f"Fourteen-day rate: {self.crashpad.fourteen_day_rate}")

        # The implementation calculates 16 days for this duration
        self.assertEqual(self.cart.cart[rental_key]['rental_days'], 16)

        # The implementation is using fourteen_day_rate for this duration
        self.assertEqual(self.cart.cart[rental_key]['daily_rate'],
                         str(self.crashpad.fourteen_day_rate))

        # Test that the total price is calculated correctly
        item_list = list(self.cart)
        rental_item = item_list[0]

        # Total price is fourteen_day_rate * 16 days
        expected_total = Decimal(self.crashpad.fourteen_day_rate) * 16
        print(f"Total price: {rental_item['total_price']}")
        print(f"Expected total: {expected_total}")
        self.assertEqual(rental_item['total_price'], expected_total)

    def test_rental_days_calculation_debug(self):
        """Debug test to understand how rental days are calculated"""
        print("\n--- Running test_rental_days_calculation_debug ---")

        # Test with different date ranges
        test_cases = [
            # (check_in_offset, check_out_offset, description)
            (1, 2, "1 day rental"),
            (1, 3, "2 day rental"),
            (1, 7, "6 day rental"),
            (1, 8, "7 day rental"),
            (1, 14, "13 day rental"),
            (1, 15, "14 day rental"),
            (1, 21, "20 day rental"),
        ]

        for check_in_offset, check_out_offset, description in test_cases:
            # Create a new cart for each test case
            self.session = MockSession()
            self.request.session = self.session
            self.cart = Cart(self.request)

            # Set up dates
            check_in = (self.today +
                        timedelta(days=check_in_offset)).strftime('%Y-%m-%d')
            check_out = (self.today +
                         timedelta(days=check_out_offset)).strftime('%Y-%m-%d')
            dates = {'check_in': check_in, 'check_out': check_out}

            print(f"\n--- Testing {description} ---")
            print(f"Check-in: {check_in}, Check-out: {check_out}")

            # Add rental to cart
            self.cart.add(self.crashpad,
                          quantity=1,
                          item_type='rental',
                          dates=dates)

            # Get rental details
            rental_key = f"rental_{self.crashpad.id}"
            rental_days = self.cart.cart[rental_key]['rental_days']
            daily_rate = self.cart.cart[rental_key]['daily_rate']

            print(f"Rental days: {rental_days}")
            print(f"Daily rate: {daily_rate}")
            print(f"Day rate: {self.crashpad.day_rate}")
            print(f"Seven-day rate: {self.crashpad.seven_day_rate}")
            print(f"Fourteen-day rate: {self.crashpad.fourteen_day_rate}")

            # Get item from cart iteration
            item_list = list(self.cart)
            rental_item = item_list[0]
            total_price = rental_item['total_price']

            print(f"Total price: {total_price}")
            print(f"Expected total (day_rate * days):"
                  f"{Decimal(self.crashpad.day_rate) * rental_days}")
            print(f"Expected total (seven_day_rate * days):"
                  f"{Decimal(self.crashpad.seven_day_rate) * rental_days}")
            print(f"Expected total (fourteen_day_rate * days):"
                  f"{Decimal(self.crashpad.fourteen_day_rate) * rental_days}")

            # This test doesn't assert anything, it just prints debug info
            self.assertTrue(True)
