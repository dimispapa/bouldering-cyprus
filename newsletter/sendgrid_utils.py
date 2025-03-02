import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_newsletter_email(subject,
                          html_content,
                          recipient_list=None,
                          from_email=None):
    """
    Send a newsletter email using SendGrid.

    Args:
        subject (str): Email subject
        html_content (str): HTML content of the email
        recipient_list (list, optional): List of recipient emails.
            If None, will be sent to all active subscribers.
        from_email (str, optional): Sender email.
            Defaults to settings.DEFAULT_FROM_EMAIL.

    Returns:
        bool: True if successful, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        sg = SendGridAPIClient(api_key=settings.EMAIL_HOST_PASSWORD)

        # If no recipient list is provided, get all active subscribers
        if recipient_list is None:
            from .models import NewsletterSubscriber
            recipient_list = NewsletterSubscriber.objects.filter(
                is_active=True).values_list('email', flat=True)

        # For each recipient, create a personalized email
        for recipient in recipient_list:
            message = Mail(from_email=from_email,
                           to_emails=recipient,
                           subject=subject,
                           html_content=html_content)

            # Add unsubscribe link
            message.add_custom_arg({
                'unsubscribe_url':
                f"{settings.SITE_URL}/newsletter/unsubscribe/{recipient}/"
            })

            response = sg.send(message)

            if response.status_code not in [200, 201, 202]:
                logger.error(f"Failed to send newsletter to {recipient}:"
                             f" {response.body}")

        return True

    except Exception as e:
        logger.error(f"Error sending newsletter: {str(e)}")
        return False
