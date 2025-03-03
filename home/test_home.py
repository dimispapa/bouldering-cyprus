from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os


class HomeViewTest(TestCase):
    """Test the home view basic functionality"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('home')

    def test_home_view_status_code(self):
        """Test that the home view returns a 200 status code"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """Test that the home view uses the correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_home_view_contains_expected_content(self):
        """Test that the home view contains expected content"""
        response = self.client.get(self.url)
        self.assertContains(response, 'Welcome to Bouldering in Cyprus')
        self.assertContains(response, 'What is Bouldering?')
        self.assertContains(response, 'Why Bouldering Cyprus?')
        self.assertContains(response, 'Ideal Winter Destination')
        self.assertContains(response, 'Crashpad Rentals Available')

    def test_home_view_loads_css_and_js(self):
        """Test that the home view loads the required CSS and JS files"""
        response = self.client.get(self.url)
        self.assertContains(response, 'home/css/index.css')
        self.assertContains(response, 'home/js/index.js')


class HomeViewFrontendTest(StaticLiveServerTestCase):
    """Test the frontend functionality of the home view using Selenium"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Check if we're running in a CI environment
        if 'CI' in os.environ:
            # Use ChromeDriver for CI
            cls.selenium = webdriver.Chrome(options=chrome_options)
        else:
            # Use local ChromeDriver
            cls.selenium = webdriver.Chrome(options=chrome_options)

        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_hero_images_exist(self):
        """Test that the hero images exist and are properly styled"""
        self.selenium.get(f"{self.live_server_url}/")

        # Check that all hero images exist
        hero_images = self.selenium.find_elements(By.CLASS_NAME, 'hero-image')
        self.assertEqual(len(hero_images), 5)

        # Check that the first hero image is visible
        first_hero = self.selenium.find_element(By.ID, 'hero-image1')
        self.assertIn('visible', first_hero.get_attribute('class'))

    def test_scroll_down_arrow_exists(self):
        """Test that the scroll down arrow exists and has the correct target"""
        self.selenium.get(f"{self.live_server_url}/")

        # Check that the scroll down arrow exists
        scroll_down = self.selenium.find_element(By.ID, 'scroll-down-arrow')
        self.assertTrue(scroll_down.is_displayed())

        # Check that it has the correct data-target attribute
        self.assertEqual(scroll_down.get_attribute('data-target'),
                         'text-box-1')

    def test_text_boxes_exist(self):
        """Test that all text boxes exist"""
        self.selenium.get(f"{self.live_server_url}/")

        # Check that all text boxes exist
        text_boxes = self.selenium.find_elements(By.CLASS_NAME, 'text-box')
        self.assertEqual(len(text_boxes), 5)

    def test_side_navigation_exists(self):
        """Test that the side navigation exists and
        has the correct number of items"""
        self.selenium.get(f"{self.live_server_url}/")

        # Check that the side navigation toggle exists
        side_nav_toggle = self.selenium.find_element(By.ID, 'side-nav-toggle')
        self.assertTrue(side_nav_toggle.is_displayed())

        # Check that the side navigation has the correct number of items
        side_nav_items = self.selenium.find_elements(
            By.CSS_SELECTOR, '#side-navigation .nav-item')
        self.assertEqual(len(side_nav_items), 6)  # 5 text boxes + footer

    def test_scroll_to_top_arrow_exists(self):
        """Test that the scroll to top arrow exists"""
        self.selenium.get(f"{self.live_server_url}/")

        # Check that the scroll to top arrow exists
        scroll_top = self.selenium.find_element(By.ID, 'scroll-to-top-arrow')
        self.assertTrue(scroll_top.is_displayed())

    def test_parallax_effect_on_scroll(self):
        """Test that the parallax effect works when scrolling"""
        self.selenium.get(f"{self.live_server_url}/")

        # Get the first text box
        text_box1 = self.selenium.find_element(By.ID, 'text-box-1')

        # Scroll to the first text box
        self.selenium.execute_script("arguments[0].scrollIntoView();",
                                     text_box1)

        # Wait for the animation to complete
        time.sleep(1)

        # Check that the first text box is now visible
        self.assertIn('visible', text_box1.get_attribute('class'))

        # Get the second text box
        text_box2 = self.selenium.find_element(By.ID, 'text-box-2')

        # Scroll to the second text box
        self.selenium.execute_script("arguments[0].scrollIntoView();",
                                     text_box2)

        # Wait for the animation to complete
        time.sleep(1)

        # Check that the second text box is now visible
        self.assertIn('visible', text_box2.get_attribute('class'))

        # Check that the hero image has changed
        # We need to wait for the JavaScript to update the hero image
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '#hero-image2.visible')))

        # Verify that the second hero image is now visible
        hero_image2 = self.selenium.find_element(By.ID, 'hero-image2')
        self.assertIn('visible', hero_image2.get_attribute('class'))

    def test_side_navigation_functionality(self):
        """Test that clicking on side navigation items
        scrolls to the correct section"""
        self.selenium.get(f"{self.live_server_url}/")

        # Open the side navigation
        side_nav_toggle = self.selenium.find_element(By.ID, 'side-nav-toggle')
        side_nav_toggle.click()

        # Wait for the offcanvas to open
        WebDriverWait(self.selenium, 10).until(
            EC.visibility_of_element_located((By.ID, 'offcanvasSidebar')))

        # Click on the second navigation item
        nav_items = self.selenium.find_elements(By.CSS_SELECTOR,
                                                '#side-navigation .nav-item')
        nav_items[1].click()  # "What is Bouldering?"

        # Wait for the scroll to complete
        time.sleep(1)

        # Check that we've scrolled to the second text box
        # This is difficult to test directly,
        # so we'll check if the second text box is visible
        text_box2 = self.selenium.find_element(By.ID, 'text-box-2')
        self.selenium.execute_script(
            "return arguments[0].getBoundingClientRect().top;", text_box2)

        # The exact position will vary,
        # but we can check if it's in the viewport
        position = self.selenium.execute_script(
            "return arguments[0].getBoundingClientRect().top;", text_box2)

        # The position should be within the viewport height
        viewport_height = self.selenium.execute_script(
            "return window.innerHeight;")
        self.assertLess(abs(position), viewport_height)
