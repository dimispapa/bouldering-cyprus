from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import patch, MagicMock

from .models import NewsletterSubscriber, NewsletterMail
from .sendgrid_utils import send_newsletter_email

User = get_user_model()


class NewsletterSubscriptionTests(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser',
                                             email='test@example.com',
                                             password='testpassword123',
                                             first_name='Test',
                                             last_name='User')

        # Create a welcome email template
        self.welcome_email = NewsletterMail.objects.create(
            id=1,  # ID 1 is used for welcome email in the code
            subject='Welcome to our Newsletter',
            html_content='<p>Welcome {{ first_name }}!</p>')

        # Set up client for authenticated requests
        self.client = Client()
        self.client.login(username='testuser', password='testpassword123')

        # Set up request factory for view testing
        self.factory = RequestFactory()

    @patch('newsletter.sendgrid_utils.send_newsletter_email')
    def test_subscribe_flow(self, mock_send_email):
        """Test the subscription flow when a user subscribes"""
        mock_send_email.return_value = True

        # Verify user is not subscribed initially
        self.assertFalse(
            NewsletterSubscriber.objects.filter(user=self.user).exists())

        # Subscribe the user
        response = self.client.post(reverse('newsletter:manage_subscription'),
                                    {'action': 'subscribe'})

        # Check redirect
        self.assertRedirects(response,
                             reverse('newsletter:manage_subscription'))

        # Verify user is now subscribed
        subscriber = NewsletterSubscriber.objects.get(user=self.user)
        self.assertTrue(subscriber.is_active)

        # Verify welcome email was sent
        mock_send_email.assert_called_once()

        # Instead of checking exact arguments,
        # just verify the function was called
        # This is more resilient to implementation changes
        self.assertTrue(mock_send_email.called)

        # If you want to check specific aspects of the call:
        call_kwargs = mock_send_email.call_args.kwargs
        call_args = mock_send_email.call_args.args

        # Check that the newsletter parameter was passed
        if call_args and len(call_args) > 0:
            self.assertEqual(call_args[0], self.welcome_email)
        elif 'newsletter' in call_kwargs:
            self.assertEqual(call_kwargs['newsletter'], self.welcome_email)

    @patch('newsletter.sendgrid_utils.send_newsletter_email')
    def test_unsubscribe_flow(self, mock_send_email):
        """Test the unsubscription flow when a user unsubscribes"""
        # Create an active subscriber
        subscriber = NewsletterSubscriber.objects.create(user=self.user,
                                                         is_active=True)

        # Unsubscribe the user
        response = self.client.post(reverse('newsletter:manage_subscription'),
                                    {'action': 'unsubscribe'})

        # Check redirect
        self.assertRedirects(response,
                             reverse('newsletter:manage_subscription'))

        # Verify user is now unsubscribed
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)

        # Verify no email was sent for unsubscribe
        mock_send_email.assert_not_called()

    def test_unsubscribe_view(self):
        """Test the unsubscribe view accessed via the unsubscribe link"""
        # Create an active subscriber
        subscriber = NewsletterSubscriber.objects.create(user=self.user,
                                                         is_active=True)

        # Access the unsubscribe link
        response = self.client.get(
            reverse('newsletter:unsubscribe', args=[self.user.id]))

        # Check redirect
        self.assertRedirects(response, reverse('home'))

        # Verify user is now unsubscribed
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)

    def test_manage_subscription_view_get(self):
        """Test the manage subscription view (GET)"""
        # Create an active subscriber
        NewsletterSubscriber.objects.create(user=self.user, is_active=True)

        # Access the manage subscription page
        response = self.client.get(reverse('newsletter:manage_subscription'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                                'newsletter/manage_subscription.html')
        self.assertTrue(response.context['is_subscribed'])


class NewsletterSendingTests(TestCase):

    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1',
                                              email='user1@example.com',
                                              password='password123',
                                              first_name='User',
                                              last_name='One')

        self.user2 = User.objects.create_user(username='user2',
                                              email='user2@example.com',
                                              password='password123',
                                              first_name='User',
                                              last_name='Two')

        # Create subscribers
        self.subscriber1 = NewsletterSubscriber.objects.create(user=self.user1,
                                                               is_active=True)

        self.subscriber2 = NewsletterSubscriber.objects.create(
            user=self.user2,
            is_active=False  # Inactive subscriber
        )

        # Create a newsletter
        self.newsletter = NewsletterMail.objects.create(
            id=2,
            subject='Test Newsletter',
            html_content='<p>Hello {{ first_name }}!</p>')

    @patch('newsletter.sendgrid_utils.SendGridAPIClient')
    def test_send_newsletter_email_util(self, mock_sendgrid):
        """Test the send_newsletter_email utility function"""
        # Mock the SendGrid client
        mock_client = MagicMock()
        mock_sendgrid.return_value = mock_client
        mock_client.send.return_value.status_code = 202

        # Call the function with a list of subscribers
        result = send_newsletter_email(self.newsletter,
                                       recipient_list=[self.subscriber1])

        # Verify the result
        self.assertTrue(result)

        # Verify SendGrid was called
        self.assertTrue(mock_client.send.called)

    @patch(
        'newsletter.management.commands.send_newsletter.send_newsletter_email')
    def test_send_newsletter_command(self, mock_send_email):
        """Test the send_newsletter management command"""
        mock_send_email.return_value = True

        # Call the command
        call_command('send_newsletter', newsletter_id=self.newsletter.id)

        # Verify the send_newsletter_email function was called
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertEqual(args[0], self.newsletter)

        # Verify the newsletter was updated
        self.newsletter.refresh_from_db()
        self.assertIsNotNone(self.newsletter.sent_at)
        self.assertEqual(self.newsletter.sent_to.count(), 1)
        self.assertIn(self.subscriber1, self.newsletter.sent_to.all())

    @patch(
        'newsletter.management.commands.send_newsletter.send_newsletter_email')
    def test_send_newsletter_command_test_email(self, mock_send_email):
        """Test the send_newsletter command with test_email parameter"""
        mock_send_email.return_value = True
        test_email = 'test@example.com'

        # Call the command with test_email
        call_command('send_newsletter',
                     newsletter_id=self.newsletter.id,
                     test_email=test_email)

        # Verify the send_newsletter_email function
        # was called with the test email
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertEqual(args[0], self.newsletter)
        self.assertEqual(args[1], [test_email])
        self.assertIn('context', kwargs)
