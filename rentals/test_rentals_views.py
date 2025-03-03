from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
import json

from rentals.models import Crashpad, CrashpadGalleryImage


class RentalsViewsTest(TestCase):
    """Comprehensive tests for the rentals views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create crashpads
        self.crashpad1 = Crashpad.objects.create(
            name="Test Crashpad 1",
            brand="Test Brand",
            model="Test Model 1",
            dimensions="100x100cm",
            description="Test description 1",
            day_rate=Decimal("10.00"),
            seven_day_rate=Decimal("8.00"),
            fourteen_day_rate=Decimal("6.00"))

        self.crashpad2 = Crashpad.objects.create(
            name="Test Crashpad 2",
            brand="Test Brand",
            model="Test Model 2",
            dimensions="120x120cm",
            description="Test description 2",
            day_rate=Decimal("12.00"),
            seven_day_rate=Decimal("10.00"),
            fourteen_day_rate=Decimal("8.00"))

        # Create gallery images
        self.gallery_image1 = CrashpadGalleryImage.objects.create(
            crashpad=self.crashpad1, image="test_image1.jpg")

        self.gallery_image2 = CrashpadGalleryImage.objects.create(
            crashpad=self.crashpad2, image="test_image2.jpg")

        # Set up dates for testing
        self.tomorrow = datetime.now().date() + timedelta(days=1)
        self.next_week = self.tomorrow + timedelta(days=7)
        self.tomorrow_str = self.tomorrow.strftime('%Y-%m-%d')
        self.next_week_str = self.next_week.strftime('%Y-%m-%d')

    def test_booking_view_renders(self):
        """Test that the booking view renders correctly"""
        url = reverse('rentals:booking')
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the template is used
        self.assertTemplateUsed(response, 'rentals/booking.html')

        # Check that no dates are in the context
        self.assertNotIn('check_in', response.context)
        self.assertNotIn('check_out', response.context)

    def test_booking_view_with_valid_dates(self):
        """Test booking view with valid dates"""
        url = f"{reverse('rentals:booking')}?" \
            f"check_in={self.tomorrow_str}&check_out={self.next_week_str}"
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the template is used
        self.assertTemplateUsed(response, 'rentals/booking.html')

        # Check that dates are in the context
        self.assertEqual(response.context['check_in'], self.tomorrow_str)
        self.assertEqual(response.context['check_out'], self.next_week_str)

    def test_booking_view_with_invalid_dates(self):
        """Test booking view with invalid dates"""
        # Past date
        past_date = (datetime.now().date() -
                     timedelta(days=1)).strftime('%Y-%m-%d')

        url = f"{reverse('rentals:booking')}?" \
            f"check_in={past_date}&check_out={self.next_week_str}"
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Your implementation has a try/except block that catches
        # the ValueError and doesn't add the dates to the context
        # when validation fails
        self.assertNotIn('check_in', response.context)
        self.assertNotIn('check_out', response.context)

        # Check-out before check-in
        url = f"{reverse('rentals:booking')}?" \
            f"check_in={self.next_week_str}&check_out={self.tomorrow_str}"
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Your implementation has a try/except block that
        # catches the ValueError and doesn't add the dates to the context
        # when validation fails
        self.assertNotIn('check_in', response.context)
        self.assertNotIn('check_out', response.context)

    def test_api_crashpads_list(self):
        """Test the API endpoint for listing crashpads"""
        url = reverse('rentals:crashpad-list')
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Parse the response
        data = json.loads(response.content)

        # Check if the response is paginated
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data

        # Should contain our crashpads
        self.assertEqual(len(results), 2)

        # Check that both crashpads are in the response
        crashpad_names = [item['name'] for item in results]
        self.assertIn("Test Crashpad 1", crashpad_names)
        self.assertIn("Test Crashpad 2", crashpad_names)

        # Check that gallery images are included
        for item in results:
            self.assertIn('gallery_images', item)
            if item['name'] == 'Test Crashpad 1':
                self.assertEqual(len(item['gallery_images']), 1)

    def test_api_crashpad_detail(self):
        """Test the API endpoint for a single crashpad"""
        url = reverse('rentals:crashpad-detail', args=[self.crashpad1.id])
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Should contain our crashpad details
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Test Crashpad 1')
        self.assertEqual(Decimal(data['day_rate']), Decimal('10.00'))
        self.assertEqual(Decimal(data['seven_day_rate']), Decimal('8.00'))
        self.assertEqual(Decimal(data['fourteen_day_rate']), Decimal('6.00'))

        # Check that gallery images are included
        self.assertIn('gallery_images', data)
        self.assertEqual(len(data['gallery_images']), 1)

        # Check availability status
        self.assertEqual(data['availability_status'], 'unknown')

    def test_api_crashpad_detail_with_dates(self):
        """Test the API endpoint for a single crashpad with dates"""
        url = \
            f"{reverse('rentals:crashpad-detail',
                       args=[self.crashpad1.id])}?" \
            f"check_in={self.tomorrow_str}&check_out={self.next_week_str}"
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Should contain our crashpad details
        data = json.loads(response.content)

        # Check availability status with dates
        self.assertIn('availability_status', data)
        self.assertEqual(data['availability_status'], 'available')

    def test_api_available_crashpads_no_dates(self):
        """Test the API endpoint for available crashpads without dates"""
        url = reverse('rentals:crashpad-available')
        response = self.client.get(url)

        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Should contain error message
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'],
                         'Both check_in and check_out dates are required')

    def test_api_available_crashpads_with_dates(self):
        """Test the API endpoint for available crashpads with dates"""
        url = \
            f"{reverse('rentals:crashpad-available')}?" \
            f"check_in={self.tomorrow_str}&check_out={self.next_week_str}"
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Parse the response
        data = json.loads(response.content)

        # Check if the response is paginated
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data

        # Should contain our crashpads (all should be available)
        self.assertEqual(len(results), 2)

        # Check that both crashpads are in the response
        crashpad_names = [item['name'] for item in results]
        self.assertIn("Test Crashpad 1", crashpad_names)
        self.assertIn("Test Crashpad 2", crashpad_names)

        # Check availability status
        for item in results:
            self.assertEqual(item['availability_status'], 'available')

    def test_api_available_crashpads_with_invalid_dates(self):
        """Test the API endpoint for available crashpads with invalid dates"""
        # Past date
        past_date = (datetime.now().date() -
                     timedelta(days=1)).strftime('%Y-%m-%d')

        url = \
            f"{reverse('rentals:crashpad-available')}?" \
            f"check_in={past_date}&check_out={self.next_week_str}"
        response = self.client.get(url)

        # With your updated validate_dates function, the view should now
        # return a 400 Bad Request when validation fails
        self.assertEqual(response.status_code, 400)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Should contain error message
        data = json.loads(response.content)
        self.assertIn('error', data)

        # Check-out before check-in
        url = \
            f"{reverse('rentals:crashpad-available')}?" \
            f"check_in={self.next_week_str}&check_out={self.tomorrow_str}"
        response = self.client.get(url)

        # With your updated validate_dates function, the view should now
        # return a 400 Bad Request when validation fails
        self.assertEqual(response.status_code, 400)

        # Response should be JSON
        self.assertEqual(response['Content-Type'].split(';')[0],
                         'application/json')

        # Should contain error message
        data = json.loads(response.content)
        self.assertIn('error', data)
