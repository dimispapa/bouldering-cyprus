from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages
from decimal import Decimal
from datetime import datetime, timedelta
import json

from shop.models import Product
from rentals.models import Crashpad
from model_bakery import baker


class CartViewsTest(TestCase):

    def setUp(self):
        """Set up test data"""
        # Create a client for making requests
        self.client = Client()
        self.factory = RequestFactory()

        # Create a product
        self.product = baker.make(Product,
                                  name="Test Product",
                                  price=Decimal("29.99"),
                                  stock=10,
                                  is_active=True,
                                  _fill_optional=False)

        # Create a product with low stock
        self.low_stock_product = baker.make(Product,
                                            name="Low Stock Product",
                                            price=Decimal("19.99"),
                                            stock=2,
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

    def test_cart_add_product(self):
        """Test adding a product to the cart"""
        print("\n--- Running test_cart_add_product ---")

        # Make a POST request to add a product to the cart
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url, data)

        # Check if the response redirects to the cart detail page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('cart_detail'))

        # Check if the product was added to the cart
        session = self.client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertIn(product_key, cart_session)
        self.assertEqual(cart_session[product_key]['quantity'], 2)

        # Check if a success message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        self.assertEqual(len(messages), 1)
        self.assertIn(f"{self.product.name} was added to your cart.",
                      str(messages[0]))

    def test_cart_add_product_insufficient_stock(self):
        """Test adding a product with insufficient stock"""
        print("\n--- Running test_cart_add_product_insufficient_stock ---")

        # Make a POST request to add a product with quantity exceeding stock
        url = reverse('cart_add', args=['product'])
        data = {
            'product_id': self.product.id,
            'quantity': 15  # Stock is only 10
        }
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url, data)

        # Check if the response redirects to the shop page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('shop'))

        # Check if the product was not added to the cart
        session = self.client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertNotIn(product_key, cart_session)

        # Check if an error message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Sorry, only {self.product.stock} units available",
                      str(messages[0]))

    def test_cart_add_product_out_of_stock(self):
        """Test adding a product that is out of stock"""
        print("\n--- Running test_cart_add_product_out_of_stock ---")

        # Set product stock to 0
        self.product.stock = 0
        self.product.save()

        # Make a POST request to add a product with no stock
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 1}
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url, data)

        # Check if the response redirects to the shop page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('shop'))

        # Check if the product was not added to the cart
        session = self.client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertNotIn(product_key, cart_session)

        # Check if an error message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Sorry, {self.product.name} is out of stock",
                      str(messages[0]))

    def test_cart_add_rental(self):
        """Test adding a rental to the cart"""
        print("\n--- Running test_cart_add_rental ---")

        # Make a POST request to add a rental to the cart
        url = reverse('cart_add', args=['rental'])
        data = {
            'crashpad_ids': [self.crashpad.id],
            'check_in': self.check_in,
            'check_out': self.check_out
        }
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url,
                                    json.dumps(data),
                                    content_type='application/json')

        # Check if the response is a JSON response with success status
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['redirect_url'], '/rentals/book/')

        # Check if the rental was added to the cart
        session = self.client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        rental_key = f"rental_{self.crashpad.id}"
        self.assertIn(rental_key, cart_session)
        self.assertEqual(cart_session[rental_key]['quantity'], 1)
        self.assertEqual(cart_session[rental_key]['check_in'], self.check_in)
        self.assertEqual(cart_session[rental_key]['check_out'], self.check_out)

        # Check if a success message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        self.assertEqual(len(messages), 1)
        self.assertIn("Crashpad(s) added to your cart.", str(messages[0]))

    def test_cart_add_rental_missing_data(self):
        """Test adding a rental with missing data"""
        print("\n--- Running test_cart_add_rental_missing_data ---")

        # Make a POST request with missing check_out date
        url = reverse('cart_add', args=['rental'])
        data = {
            'crashpad_ids': [self.crashpad.id],
            'check_in': self.check_in
            # Missing check_out
        }
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url,
                                    json.dumps(data),
                                    content_type='application/json')

        # Check if the response is a JSON response with error status
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Missing required data')

        # Check if the rental was not added to the cart
        session = self.client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        rental_key = f"rental_{self.crashpad.id}"
        self.assertNotIn(rental_key, cart_session)

    def test_cart_add_invalid_item_type(self):
        """Test adding an item with invalid type"""
        print("\n--- Running test_cart_add_invalid_item_type ---")

        # Make a POST request with invalid item type
        url = reverse('cart_add', args=['invalid_type'])
        data = {'product_id': self.product.id, 'quantity': 1}
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url, data)

        # Check if the response redirects to the shop page
        print(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 302)  # Redirect

        # Check if an error message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        self.assertEqual(len(messages), 1)
        self.assertIn("Error adding item to cart", str(messages[0]))

    def test_cart_remove(self):
        """Test removing an item from the cart"""
        print("\n--- Running test_cart_remove ---")

        # Create a fresh client for this test to avoid message accumulation
        client = Client()

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        client.post(url, data)

        # Make a GET request to remove the product
        url = reverse('cart_remove', args=['product', self.product.id])
        print(f"GET to {url}")
        response = client.get(url)

        # Check if the response redirects to the cart detail page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('cart_detail'))

        # Check if the product was removed from the cart
        session = client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertNotIn(product_key, cart_session)

        # Check if a success message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        # We should have 2 messages: one from adding and one from removing
        self.assertEqual(len(messages), 2)
        self.assertIn(f"{self.product.name} was removed from your cart.",
                      str(messages[1]))

    def test_cart_detail(self):
        """Test viewing the cart detail page"""
        print("\n--- Running test_cart_detail ---")

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        self.client.post(url, data)

        # Make a GET request to view the cart
        url = reverse('cart_detail')
        print(f"GET to {url}")
        response = self.client.get(url)

        # Check if the response is successful
        print(f"Response status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

        # Check if the correct template is used
        print(f"Template used: {response.templates[0].name}")
        self.assertTemplateUsed(response, 'cart/cart_detail.html')

        # Check if the cart is in the context
        print(f"Context: {response.context}")
        self.assertIn('cart', response.context)

        # Check if the cart contains the product
        cart_in_context = response.context['cart']
        items = list(cart_in_context)
        print(f"Cart items: {items}")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['item'].id, self.product.id)
        self.assertEqual(items[0]['quantity'], 2)

    def test_cart_update_quantities(self):
        """Test updating cart quantities"""
        print("\n--- Running test_cart_update_quantities ---")

        # Create a fresh client for this test to avoid message accumulation
        client = Client()

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        client.post(url, data)

        # Make a POST request to update quantities
        url = reverse('cart_update')
        data = {'action': 'update', f'quantity_product_{self.product.id}': 5}
        print(f"POST to {url} with data: {data}")
        response = client.post(url, data)

        # Check if the response redirects to the cart detail page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('cart_detail'))

        # Check if the quantity was updated
        session = client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertEqual(cart_session[product_key]['quantity'], 5)

        # Check if a success message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        # We should have 2 messages: one from adding and one from updating
        self.assertEqual(len(messages), 2)
        self.assertIn("Your cart has been updated.", str(messages[1]))

    def test_cart_update_remove_with_zero(self):
        """Test removing an item by setting quantity to zero"""
        print("\n--- Running test_cart_update_remove_with_zero ---")

        # Create a fresh client for this test to avoid message accumulation
        client = Client()

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        client.post(url, data)

        # Make a POST request to set quantity to 0
        url = reverse('cart_update')
        data = {'action': 'update', f'quantity_product_{self.product.id}': 0}
        print(f"POST to {url} with data: {data}")
        response = client.post(url, data)

        # Check if the response redirects to the cart detail page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('cart_detail'))

        # Check if the product was removed
        session = client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertNotIn(product_key, cart_session)

        # Check if a success message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        # We should have 2 messages: one from adding and one from updating
        self.assertEqual(len(messages), 2)
        self.assertIn("Your cart has been updated.", str(messages[1]))

    def test_cart_update_insufficient_stock(self):
        """Test updating cart with insufficient stock"""
        print("\n--- Running test_cart_update_insufficient_stock ---")

        # Create a fresh client for this test to avoid message accumulation
        client = Client()

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        client.post(url, data)

        # Make a POST request to update with quantity exceeding stock
        url = reverse('cart_update')
        data = {
            'action': 'update',
            f'quantity_product_{self.product.id}': 15  # Stock is only 10
        }
        print(f"POST to {url} with data: {data}")
        response = client.post(url, data)

        # Check if the response redirects to the cart detail page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('cart_detail'))

        # Check if the quantity was not updated
        session = client.session
        cart_session = session.get('cart', {})
        print(f"Cart contents: {cart_session}")
        product_key = f"product_{self.product.id}"
        self.assertEqual(cart_session[product_key]['quantity'],
                         2)  # Still 2, not updated

        # Check if an error message was added
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")
        # We should have 2 messages: one from adding and one from the error
        self.assertEqual(len(messages), 2)
        self.assertIn(f"Sorry, only {self.product.stock} units available",
                      str(messages[1]))

    def test_cart_update_checkout(self):
        """Test checkout action in cart update"""
        print("\n--- Running test_cart_update_checkout ---")

        # Add a product to the cart first
        url = reverse('cart_add', args=['product'])
        data = {'product_id': self.product.id, 'quantity': 2}
        self.client.post(url, data)

        # Make a POST request with checkout action
        url = reverse('cart_update')
        data = {'action': 'checkout'}
        print(f"POST to {url} with data: {data}")
        response = self.client.post(url, data)

        # Check if the response redirects to the checkout page
        print(f"Response status code: {response.status_code}")
        print(f"Response redirect chain: {response.url}")
        self.assertRedirects(response, reverse('checkout'))
