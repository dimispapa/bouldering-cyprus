import logging
from django.contrib.sites.models import Site
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, CustomArg
from django.conf import settings
from .models import NewsletterSubscriber, NewsletterMail
from django.contrib import messages


logger = logging.getLogger(__name__)


def send_newsletter_email(newsletter,
                          recipient_list=None,
                          from_email=None,
                          context=None):
    """
    Send a newsletter email using SendGrid.

    Args:
        newsletter: NewsletterMail object
        recipient_list (list, optional): List of recipient emails or
            subscriber objects. If None, will be sent to all active
            subscribers.
        from_email (str, optional): Sender email. Defaults to
            settings.DEFAULT_FROM_EMAIL.
        context (dict, optional): Additional context for template rendering.

    Returns:
        bool: True if successful, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Get the site URL from settings or construct it
    if hasattr(settings, 'SITE_URL'):
        site_url = settings.SITE_URL
    else:
        # Get the current site
        current_site = Site.objects.get_current()
        site_url = current_site.domain

    # Get the static URL from settings
    static_url = settings.EMAIL_STATIC_URL
    if static_url.endswith('/'):
        static_url = static_url[:-1]  # Remove trailing slash

    # Initialize context if None
    if context is None:
        context = {}

    # Add base context
    context['site_url'] = site_url
    context['static_url'] = static_url
    logger.info(f"Base context: {context}")

    try:
        sg = SendGridAPIClient(api_key=settings.EMAIL_HOST_PASSWORD)

        # If no recipient list is provided, get all active subscribers
        if recipient_list is None:
            subscribers = list(
                NewsletterSubscriber.objects.filter(is_active=True))
            logger.info(f"Fetched {len(subscribers)} activesubscribers")

        # Otherwise use the provided recipient list
        else:
            subscribers = recipient_list

        # For each recipient, create a personalized email
        for subscriber in subscribers:
            # Prepare recipient-specific context
            recipient_context = context.copy()

            if hasattr(subscriber, 'user'):
                # It's a subscriber object
                recipient_email = subscriber.user.email
                recipient_context['user'] = subscriber.user
                recipient_context['first_name'] = subscriber.user.first_name
                recipient_context['last_name'] = subscriber.user.last_name
                recipient_context['email'] = recipient_email
                recipient_context['unsubscribe_url'] = \
                    f"{site_url}/newsletter/unsubscribe/{subscriber.user.id}/"
            else:
                # It's just an email string e.g. from a test email
                recipient_email = subscriber
                recipient_context['email'] = recipient_email
                recipient_context['unsubscribe_url'] = \
                    f"{site_url}/newsletter/manage/"

            logger.info(f"Processing subscriber: {recipient_email}")
            logger.info(f"Recipient context: {recipient_context}")

            # Render the content with the recipient-specific context
            html_content = newsletter.render_content(recipient_context)

            # Create the message
            message = Mail(from_email=from_email,
                           to_emails=recipient_email,
                           subject=newsletter.subject,
                           html_content=html_content)

            # Add unsubscribe link
            unsubscribe_url = \
                f"{site_url}/newsletter/unsubscribe/{recipient_email}/"
            message.add_custom_arg(
                CustomArg('unsubscribe_url', unsubscribe_url))

            # Send the newsletter
            response = sg.send(message)

            if response.status_code not in [200, 201, 202]:
                logger.error(f"Failed to send newsletter to {recipient_email}:"
                             f" {response.body}")
            else:
                logger.info(f"Newsletter sent to {recipient_email}")

        return True

    except Exception as e:
        logger.error(f"Error sending newsletter: {str(e)}")
        return False


def send_welcome_email(request, subscriber):
    """
    Send a welcome email to a new subscriber.
    """
    # Get the welcome email template
    welcome_email = NewsletterMail.objects.get(id=1)
    # Send the welcome email
    logger.info(f"Sending welcome email to {subscriber.email}")
    success = send_newsletter_email(newsletter=welcome_email,
                                    recipient_list=[subscriber])
    if success:
        logger.info(f"Welcome email sent to {subscriber.email}")
        messages.success(request,
                         "Thank you for subscribing to our newsletter!")
    else:
        logger.error(f"Error sending welcome email for "
                     f"{subscriber.email}")
        messages.error(
            request, "An error occurred while processing your "
            "subscribtion to our newsletter. Please try again "
            "later or contact us at info@bouldering-cyprus.com.")
