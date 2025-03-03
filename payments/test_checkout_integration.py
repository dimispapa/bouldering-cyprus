from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from decimal import Decimal
import os
import tempfile
import shutil
from datetime import datetime, timedelta

from shop.models import Product
from rentals.models import Crashpad
from model_bakery import baker


class CheckoutSeleniumTests(StaticLiveServerTestCase):
    """Integration tests for the checkout process using Selenium"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a temporary directory for Chrome profile and screenshots
        cls.chrome_profile_dir = os.path.join(
            tempfile.gettempdir(), 'chrome-profile-for-checkout-tests')
        os.makedirs(cls.chrome_profile_dir, exist_ok=True)

        cls.screenshots_dir = os.path.join(tempfile.gettempdir(),
                                           'checkout-test-screenshots')
        os.makedirs(cls.screenshots_dir, exist_ok=True)

        print(f"Using Chrome profile directory: {cls.chrome_profile_dir}")
        print(f"Screenshots will be saved to: {cls.screenshots_dir}")

        # Setup Chrome options with the custom profile
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-data-dir={cls.chrome_profile_dir}')
        options.add_argument('--window-size=1920,3000')

        # Disable permissions prompts and notifications
        options.add_experimental_option(
            'prefs', {
                'profile.default_content_setting_values.notifications':
                2,
                'profile.default_content_settings.popups':
                0,
                'download.prompt_for_download':
                False,
                'download.default_directory':
                tempfile.gettempdir(),
                'profile.content_settings.exceptions.automatic_downloads.'
                '*.setting':
                1,
                'profile.default_content_setting_values.geolocation':
                2,
                'profile.default_content_setting_values.media_stream_mic':
                2,
                'profile.default_content_setting_values.media_stream_camera':
                2,
            })

        # Initialize the Chrome WebDriver
        cls.browser = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()),
                                       options=options)

        # Set a very tall window to avoid scrolling issues
        cls.browser.set_window_size(1920, 3000)
        cls.browser.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        # Clean up the Chrome profile directory
        try:
            shutil.rmtree(cls.chrome_profile_dir)
            print(
                "Cleaned up Chrome profile directory: "
                f"{cls.chrome_profile_dir}"
            )
        except Exception as e:
            print(f"Error cleaning up Chrome profile directory: {e}")
        super().tearDownClass()

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

        # Format dates as strings for URLs
        self.tomorrow_str = self.tomorrow.strftime("%Y-%m-%d")
        self.next_week_str = self.next_week.strftime("%Y-%m-%d")

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present and return it"""
        try:
            element = WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            # Take a screenshot when element is not found
            screenshot_path = os.path.join(self.screenshots_dir,
                                           f"timeout_{value}.png")
            self.browser.save_screenshot(screenshot_path)
            print(
                f"Timeout waiting for element {value}. "
                f"Screenshot saved to {screenshot_path}"
            )
            raise

    def safe_click(self, element, screenshot_prefix=None):
        """Safely click an element with JavaScript and take a screenshot"""
        if screenshot_prefix:
            screenshot_path = os.path.join(
                self.screenshots_dir, f"{screenshot_prefix}_before_click.png")
            self.browser.save_screenshot(screenshot_path)

        # Scroll element into view and click with JavaScript
        self.browser.execute_script("arguments[0].scrollIntoView(true);",
                                    element)
        self.browser.execute_script("arguments[0].click();", element)

        if screenshot_prefix:
            screenshot_path = os.path.join(
                self.screenshots_dir, f"{screenshot_prefix}_after_click.png")
            self.browser.save_screenshot(screenshot_path)

    def test_checkout_page_ui(self):
        """Test the checkout page UI after adding items via API"""
        try:
            # First, use the API to add a product to the cart
            from django.test import Client
            client = Client()

            # Add a product to the cart
            url = reverse('cart_add', args=['product'])
            response = client.post(url, {
                'product_id': self.product.id,
                'quantity': 2
            })

            # Check that the response is successful (should redirect)
            self.assertEqual(response.status_code, 302)

            # Get the session ID from the client
            session_id = client.session.session_key

            # Set the session cookie in the browser
            self.browser.get(f"{self.live_server_url}/")
            self.browser.add_cookie({
                'name': 'sessionid',
                'value': session_id,
                'path': '/'
            })

            # Navigate to the checkout page
            checkout_url = f"{self.live_server_url}{reverse('checkout')}"
            print(f"Navigating to: {checkout_url}")
            self.browser.get(checkout_url)

            # Take a screenshot of the checkout page
            screenshot_path = os.path.join(self.screenshots_dir,
                                           "checkout_page.png")
            self.browser.save_screenshot(screenshot_path)

            # Check that we're on the checkout page
            self.assertIn("Order Summary", self.browser.page_source)

            # Check that our product is in the cart
            self.assertIn("Test Product", self.browser.page_source)

            # Check for key UI elements
            # 1. Payment form
            payment_form = self.browser.find_element(By.ID, "payment-form")
            self.assertIsNotNone(payment_form)

            # 2. Order summary section
            order_summary = self.browser.find_element(
                By.XPATH, "//h4[contains(text(), 'Order Summary')]")
            self.assertIsNotNone(order_summary)

            # 3. Progress bar
            progress_bar = self.browser.find_element(By.ID,
                                                     "progressbar-container")
            self.assertIsNotNone(progress_bar)

            # 4. Edit cart link
            edit_cart_link = self.browser.find_element(
                By.XPATH, "//a[contains(@class, 'button-update')]")
            self.assertIsNotNone(edit_cart_link)

            print("Checkout page UI test passed")
        except Exception as e:
            screenshot_path = os.path.join(self.screenshots_dir,
                                           "checkout_ui_error.png")
            self.browser.save_screenshot(screenshot_path)
            print(f"Error during checkout UI test: {e}")
            print(f"Screenshot saved to: {screenshot_path}")
            raise

    def test_api_cart_directly(self):
        """Test the cart API directly without relying on JavaScript"""
        from django.test import Client

        # Use Django's test client to add a product to the cart
        client = Client()

        # Add a product to the cart
        url = reverse('cart_add', args=['product'])
        response = client.post(url, {
            'product_id': self.product.id,
            'quantity': 2
        })

        # Print response info for debugging
        print(f"Cart add response status: {response.status_code}")

        # Check that the response is successful (should redirect)
        self.assertEqual(response.status_code, 302)

        # Get the cart contents
        cart_url = reverse('cart_detail')
        response = client.get(cart_url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that the product is in the cart
        self.assertIn(b"Test Product", response.content)

        # Go to checkout
        checkout_url = reverse('checkout')
        response = client.get(checkout_url)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that the product is on the checkout page
        self.assertIn(b"Test Product", response.content)

        print("API cart test passed")
