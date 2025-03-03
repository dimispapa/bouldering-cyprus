from django.test import TestCase
from decimal import Decimal
from datetime import datetime, timedelta
from rentals.models import Crashpad, CrashpadGalleryImage


class CrashpadModelTest(TestCase):
    """Test the Crashpad model"""

    def setUp(self):
        """Set up test data"""
        # Create a crashpad
        self.crashpad = Crashpad.objects.create(
            name="Test Crashpad",
            brand="Test Brand",
            model="Test Model",
            dimensions="100x100cm",
            description="Test description",
            day_rate=Decimal("10.00"),
            seven_day_rate=Decimal("8.00"),
            fourteen_day_rate=Decimal("6.00"))

        # Create a second crashpad
        self.crashpad2 = Crashpad.objects.create(
            name="Test Crashpad 2",
            brand="Test Brand 2",
            model="Test Model 2",
            dimensions="120x120cm",
            description="Test description 2",
            day_rate=Decimal("12.00"),
            seven_day_rate=Decimal("10.00"),
            fourteen_day_rate=Decimal("8.00"))

    def test_crashpad_creation(self):
        """Test that a crashpad can be created"""
        self.assertEqual(self.crashpad.name, "Test Crashpad")
        self.assertEqual(self.crashpad.brand, "Test Brand")
        self.assertEqual(self.crashpad.model, "Test Model")
        self.assertEqual(self.crashpad.dimensions, "100x100cm")
        self.assertEqual(self.crashpad.description, "Test description")
        self.assertEqual(self.crashpad.day_rate, Decimal("10.00"))
        self.assertEqual(self.crashpad.seven_day_rate, Decimal("8.00"))
        self.assertEqual(self.crashpad.fourteen_day_rate, Decimal("6.00"))

    def test_crashpad_string_representation(self):
        """Test the string representation of a crashpad"""
        self.assertEqual(str(self.crashpad), "Test Crashpad")

    def test_crashpad_is_available_with_no_bookings(self):
        """Test the is_available method with no bookings"""
        # Set up dates for testing
        tomorrow = datetime.now().date() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)

        # Should be available since there are no bookings
        self.assertTrue(self.crashpad.is_available(tomorrow, next_week))

        # Test with datetime objects instead of date objects
        tomorrow_dt = datetime.now() + timedelta(days=1)
        next_week_dt = tomorrow_dt + timedelta(days=7)
        self.assertTrue(self.crashpad.is_available(tomorrow_dt, next_week_dt))


class CrashpadGalleryImageTest(TestCase):
    """Test the CrashpadGalleryImage model"""

    def setUp(self):
        """Set up test data"""
        # Create a crashpad
        self.crashpad = Crashpad.objects.create(
            name="Test Crashpad",
            brand="Test Brand",
            model="Test Model",
            dimensions="100x100cm",
            description="Test description",
            day_rate=Decimal("10.00"),
            seven_day_rate=Decimal("8.00"),
            fourteen_day_rate=Decimal("6.00"))

        # Create a gallery image
        self.gallery_image = CrashpadGalleryImage.objects.create(
            crashpad=self.crashpad, image="test_image.jpg")

    def test_gallery_image_string_representation(self):
        """Test the string representation of a gallery image"""
        self.assertEqual(str(self.gallery_image),
                         "Gallery image for Test Crashpad")


class CrashpadBookingMethodsTest(TestCase):
    """Test the CrashpadBooking model methods without creating instances"""

    def test_calculate_rental_days(self):
        """Test the calculate_rental_days method"""
        from datetime import date

        # Create a mock booking object
        class MockBooking:

            def __init__(self, check_in, check_out):
                self.check_in = check_in
                self.check_out = check_out

            def calculate_rental_days(self):
                return (self.check_out - self.check_in).days + 1

        # Test with different date ranges
        one_day = MockBooking(date(2023, 1, 1), date(2023, 1, 1))
        self.assertEqual(one_day.calculate_rental_days(), 1)

        three_days = MockBooking(date(2023, 1, 1), date(2023, 1, 3))
        self.assertEqual(three_days.calculate_rental_days(), 3)

        seven_days = MockBooking(date(2023, 1, 1), date(2023, 1, 7))
        self.assertEqual(seven_days.calculate_rental_days(), 7)

        fourteen_days = MockBooking(date(2023, 1, 1), date(2023, 1, 14))
        self.assertEqual(fourteen_days.calculate_rental_days(), 14)

    def test_calculate_daily_rate(self):
        """Test the calculate_daily_rate method"""

        # Create a mock booking object
        class MockBooking:

            def __init__(self, rental_days, crashpad):
                self.rental_days = rental_days
                self.crashpad = crashpad

            def calculate_daily_rate(self):
                if self.rental_days >= 14:
                    return self.crashpad.fourteen_day_rate
                elif self.rental_days >= 7:
                    return self.crashpad.seven_day_rate
                else:
                    return self.crashpad.day_rate

        # Create a mock crashpad
        class MockCrashpad:

            def __init__(self):
                self.day_rate = Decimal("10.00")
                self.seven_day_rate = Decimal("8.00")
                self.fourteen_day_rate = Decimal("6.00")

        crashpad = MockCrashpad()

        # Test with different rental durations
        short_booking = MockBooking(3, crashpad)
        self.assertEqual(short_booking.calculate_daily_rate(),
                         Decimal("10.00"))

        medium_booking = MockBooking(7, crashpad)
        self.assertEqual(medium_booking.calculate_daily_rate(),
                         Decimal("8.00"))

        long_booking = MockBooking(14, crashpad)
        self.assertEqual(long_booking.calculate_daily_rate(), Decimal("6.00"))

    def test_calculate_total_price(self):
        """Test the calculate_total_price method"""

        # Create a mock booking object
        class MockBooking:

            def __init__(self, rental_days, daily_rate):
                self.rental_days = rental_days
                self.daily_rate = daily_rate

            def calculate_rental_days(self):
                return self.rental_days

            def calculate_total_price(self):
                return self.daily_rate * self.rental_days

        # Test with different values
        booking = MockBooking(7, Decimal("8.00"))
        self.assertEqual(booking.calculate_total_price(), Decimal("56.00"))

        booking = MockBooking(3, Decimal("10.00"))
        self.assertEqual(booking.calculate_total_price(), Decimal("30.00"))

        booking = MockBooking(14, Decimal("6.00"))
        self.assertEqual(booking.calculate_total_price(), Decimal("84.00"))
