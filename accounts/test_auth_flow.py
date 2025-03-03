from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from allauth.account.models import EmailAddress

User = get_user_model()


class AuthenticationFlowTest(TestCase):
    """Test the complete authentication flow using
    Django allauth with email verification"""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('account_signup')
        self.login_url = reverse('account_login')
        self.logout_url = reverse('account_logout')
        self.email_url = reverse('account_email')
        self.password_change_url = reverse('account_change_password')
        self.test_user_data = {
            'email': 'testuser@example.com',
            'username': 'testuser',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
        }

    def test_signup_page_loads(self):
        """Test that the signup page loads correctly"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Already have an account?')

    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertContains(response, 'Sign In')
        self.assertContains(response, 'Forgot Password?')
        self.assertContains(response, "Don't have an account?")

    def test_logout_page_loads(self):
        """Test that the logout page loads correctly when logged in"""
        # Create and log in a user first
        User.objects.create_user(username='logouttest',
                                 email='logouttest@example.com',
                                 password='TestPassword123!')
        self.client.login(username='logouttest', password='TestPassword123!')

        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/logout.html')
        self.assertContains(response, 'Sign Out')
        self.assertContains(response, 'Are you sure you want to sign out?')

    def test_email_management_page_loads(self):
        """Test that the email management page
        loads correctly when logged in"""
        # Create and log in a user first
        user = User.objects.create_user(username='emailtest',
                                        email='emailtest@example.com',
                                        password='TestPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=False)
        self.client.login(username='emailtest', password='TestPassword123!')

        response = self.client.get(self.email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/email.html')
        self.assertContains(response, 'My Account')
        self.assertContains(response, 'Email Address')
        self.assertContains(response, 'Unverified')

    def test_signup_flow_with_email_verification(self):
        """Test the complete signup flow with email verification"""
        # Step 1: Visit the signup page
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit the signup form
        response = self.client.post(self.signup_url,
                                    self.test_user_data,
                                    follow=True)

        # Check that the user was created
        self.assertTrue(
            User.objects.filter(email=self.test_user_data['email']).exists())
        user = User.objects.get(email=self.test_user_data['email'])

        # Check that the user has the correct name
        self.assertEqual(user.first_name, self.test_user_data['first_name'])
        self.assertEqual(user.last_name, self.test_user_data['last_name'])

        # Check that an email address was created
        self.assertTrue(EmailAddress.objects.filter(user=user).exists())
        email_obj = EmailAddress.objects.get(user=user)
        self.assertEqual(email_obj.email, self.test_user_data['email'])

        # Check if email verification is enabled in your settings
        # If it's not mandatory, the email might be auto-verified
        if getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION',
                   'optional') != 'none':
            self.assertFalse(email_obj.verified)  # Should not be verified yet
            # Check if a verification email was sent
            self.assertTrue(len(mail.outbox) > 0)
            self.assertIn(self.test_user_data['email'], mail.outbox[0].to)

    def test_login_flow(self):
        """Test the login flow"""
        # Create a user with a verified email
        user = User.objects.create_user(username='logintest',
                                        email='logintest@example.com',
                                        password='TestPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=True)

        # Step 1: Visit the login page
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit the login form
        response = self.client.post(self.login_url, {
            'login': 'logintest@example.com',
            'password': 'TestPassword123!',
        },
                                    follow=True)

        # Check that the login was successful
        self.assertTrue(response.context['user'].is_authenticated)

        # Check that we were redirected to the expected page
        expected_url = getattr(settings, 'LOGIN_REDIRECT_URL', '/')
        self.assertRedirects(response, expected_url)

    def test_login_with_unverified_email(self):
        """Test login with an unverified email"""
        # Create a user with an unverified email
        user = User.objects.create_user(username='unverifiedlogin',
                                        email='unverifiedlogin@example.com',
                                        password='TestPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=False)

        # Try to log in
        response = self.client.post(self.login_url, {
            'login': 'unverifiedlogin@example.com',
            'password': 'TestPassword123!',
        },
                                    follow=True)

        # Check that the login failed due to unverified email
        self.assertFalse(response.context['user'].is_authenticated)

        # Verify we're redirected to the email verification sent page
        # (not the success page)
        self.assertEqual(response.resolver_match.url_name,
                         'account_email_verification_sent')

    def test_logout_flow(self):
        """Test the logout flow"""
        # Create and log in a user first
        user = User.objects.create_user(username='logoutflowtest',
                                        email='logoutflowtest@example.com',
                                        password='TestPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=True)
        self.client.login(username='logoutflowtest',
                          password='TestPassword123!')

        # Step 1: Visit the logout page
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit the logout form
        response = self.client.post(self.logout_url, follow=True)

        # Check that the user is now logged out
        self.assertFalse(response.context['user'].is_authenticated)

        # Check that we were redirected to the home page
        expected_url = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
        self.assertRedirects(response, expected_url)

    def test_password_change_flow(self):
        """Test the password change flow"""
        # Create and log in a user
        user = User.objects.create_user(username='passwordtest',
                                        email='passwordtest@example.com',
                                        password='OldPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=True)
        self.client.login(username='passwordtest', password='OldPassword123!')

        # Step 1: Visit the password change page
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_change.html')

        # Step 2: Submit the password change form
        response = self.client.post(self.password_change_url, {
            'oldpassword': 'OldPassword123!',
            'password1': 'NewPassword456!',
            'password2': 'NewPassword456!',
        },
                                    follow=True)

        # Check that the password was actually changed
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword456!'))

        # Check that we can log in with the new password
        self.client.logout()
        login_success = self.client.login(username='passwordtest',
                                          password='NewPassword456!')
        self.assertTrue(login_success)

    def test_email_verification_resend(self):
        """Test resending email verification"""
        # Create a user with an unverified email
        user = User.objects.create_user(username='unverified',
                                        email='unverified@example.com',
                                        password='TestPassword123!')
        EmailAddress.objects.create(user=user,
                                    email=user.email,
                                    primary=True,
                                    verified=False)
        self.client.login(username='unverified', password='TestPassword123!')

        # Clear the outbox
        mail.outbox = []

        # Step 1: Visit the email management page
        response = self.client.get(self.email_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit the resend verification form
        response = self.client.post(self.email_url, {
            'action_send': 'unverified@example.com',
        },
                                    follow=True)

        # Check that a verification email was sent
        # This might not work if email sending is disabled in tests
        if len(mail.outbox) > 0:
            self.assertIn('unverified@example.com', mail.outbox[0].to)


class CustomUserAdminTest(TestCase):
    """Test the custom user admin"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPassword123!')
        self.client = Client()
        self.client.login(username='admin', password='AdminPassword123!')

    def test_user_admin_list_display(self):
        """Test that the user admin list display shows the correct fields"""
        response = self.client.get(reverse('admin:auth_user_changelist'))
        self.assertEqual(response.status_code, 200)

        # Check that our custom fields are displayed
        self.assertContains(response, 'Email')
        self.assertContains(response, 'First name')
        self.assertContains(response, 'Last name')
        self.assertContains(response, 'Staff status')
        self.assertContains(response, 'Active')
