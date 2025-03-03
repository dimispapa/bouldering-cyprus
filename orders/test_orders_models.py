from decimal import Decimal
from django.test import TestCase
from django.conf import settings
from model_bakery import baker
from orders.models import Order, OrderItem
from shop.models import Product
from django.contrib.auth.models import User
from rentals.models import CrashpadBooking
import uuid


class TestOrderModel(TestCase):

    def setUp(self):
        self.user = baker.make(User)
        self.product = baker.make(Product, price=Decimal('10.00'), stock=10)

    def test_order_creation(self):
        """Test basic order creation with required fields"""
        order = baker.make(
            Order,
            user=self.user,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="1234567890",
            address_line1="123 Test St",
            town_or_city="Test City",
            postal_code="12345",
            delivery_cost=Decimal('2.50'),
            order_total=Decimal('10.00'),
            grand_total=Decimal('12.50'),
        )

        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.first_name, "Test")
        self.assertEqual(order.last_name, "User")
        self.assertEqual(order.grand_total, Decimal('12.50'))

    def test_order_number_generation(self):
        """Test that order numbers are generated correctly"""
        # Instead of using baker.make, let's create the order manually
        # to ensure the save method is called properly
        order = Order(
            user=self.user,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="1234567890",
            address_line1="123 Test St",
            town_or_city="Test City",
            postal_code="12345",
            delivery_cost=Decimal('2.50'),
            order_total=Decimal('10.00'),
            grand_total=Decimal('12.50'),
            stripe_piid=f"pi_{uuid.uuid4().hex}"  # Generate a unique stripe ID
        )
        order.save()  # This will trigger the custom save method

        # Now check that the order number follows the expected format
        self.assertIsNotNone(order.order_number)
        print(f"Order number: {order.order_number}")
        self.assertEqual(len(order.order_number.split("-")), 3)
        self.assertTrue(order.order_number.startswith("BC-"))

        # Check the date part (middle section)
        date_part = order.order_number.split("-")[1]
        self.assertEqual(len(date_part), 8)  # YYYYMMDD format

        # Check the UUID part (last section)
        uuid_part = order.order_number.split("-")[2]
        self.assertEqual(len(uuid_part), 6)  # 6 characters from UUID

    def test_update_total_below_threshold(self):
        """Test update_total method when below free delivery threshold"""
        order = baker.make(Order)
        baker.make(OrderItem,
                   order=order,
                   product=self.product,
                   quantity=2,
                   item_total=Decimal('20.00'))

        order.update_total()

        expected_delivery = Decimal('20.00') * Decimal(
            str(settings.STANDARD_DELIVERY_PERCENTAGE)) / Decimal('100')
        expected_grand_total = Decimal('20.00') + expected_delivery

        self.assertEqual(order.order_total, Decimal('20.00'))
        self.assertEqual(order.delivery_cost, expected_delivery)
        self.assertEqual(order.grand_total, expected_grand_total)

    def test_update_total_above_threshold(self):
        """Test update_total method when above free delivery threshold"""
        order = baker.make(Order)
        # Convert FREE_DELIVERY_THRESHOLD to Decimal to avoid type error
        threshold_value = Decimal(str(
            settings.FREE_DELIVERY_THRESHOLD)) + Decimal('10.00')

        baker.make(OrderItem,
                   order=order,
                   product=self.product,
                   quantity=int(threshold_value / self.product.price) + 1,
                   item_total=threshold_value)

        order.update_total()

        self.assertGreater(order.order_total, threshold_value)
        self.assertEqual(order.delivery_cost, Decimal('0'))
        self.assertGreater(order.grand_total, threshold_value)

    def test_delete_order_releases_stock(self):
        """Test that deleting an order releases product stock"""
        order = baker.make(Order)
        baker.make(OrderItem,
                   order=order,
                   product=self.product,
                   quantity=3,
                   item_total=Decimal('30.00'))

        initial_stock = self.product.stock
        order.delete()

        # Refresh product from database
        self.product.refresh_from_db()

        # Stock should be increased by the quantity in the order
        self.assertEqual(self.product.stock, initial_stock + 3)

    def test_determine_order_type(self):
        """Test the _determine_order_type method"""
        # Instead of trying to mock the related managers directly,
        # let's create actual related objects
        order = baker.make(Order)

        # Test PRODUCTS_ONLY - create an order item
        baker.make(OrderItem, order=order)

        # Test that the order type is PRODUCTS_ONLY
        self.assertEqual(order._determine_order_type(), 'PRODUCTS_ONLY')

        # For the remaining tests, we should create a new order for each case
        # and set up the appropriate related objects

        # Test RENTALS_ONLY
        order2 = baker.make(Order)
        baker.make(CrashpadBooking, order=order2)
        # Test that the order type is RENTALS_ONLY
        self.assertEqual(order2._determine_order_type(), 'RENTALS_ONLY')

        # Test MIXED
        order3 = baker.make(Order)
        baker.make(OrderItem, order=order3)
        baker.make(CrashpadBooking, order=order3)
        # Test that the order type is MIXED
        self.assertEqual(order3._determine_order_type(), 'MIXED')

        # Test None
        order4 = baker.make(Order)
        # Test that the order type is None
        self.assertEqual(order4._determine_order_type(), None)


class TestOrderItemModel(TestCase):

    def setUp(self):
        self.product = baker.make(Product, price=Decimal('15.00'), stock=5)
        self.order = baker.make(Order)

    def test_order_item_creation(self):
        """Test basic order item creation"""
        order_item = baker.make(OrderItem,
                                order=self.order,
                                product=self.product,
                                quantity=2)

        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)

    def test_item_total_calculation(self):
        """Test that item_total is calculated correctly on save"""
        order_item = baker.make(OrderItem,
                                order=self.order,
                                product=self.product,
                                quantity=3)

        expected_total = self.product.price * 3
        self.assertEqual(order_item.item_total, expected_total)

    def test_price_property(self):
        """Test the price property returns the product price"""
        order_item = baker.make(OrderItem,
                                order=self.order,
                                product=self.product)

        self.assertEqual(order_item.price, self.product.price)

    def test_string_representation(self):
        """Test the string representation of an order item"""
        order_item = baker.make(OrderItem,
                                order=self.order,
                                product=self.product)

        expected_string = f"{self.order.order_number} - {self.product.name}"
        self.assertEqual(str(order_item), expected_string)
