from django.core.management.base import BaseCommand
from django.utils import timezone
from newsletter.models import NewsletterSubscriber, NewsletterMail
from newsletter.sendgrid_utils import send_newsletter_email


class Command(BaseCommand):
    help = 'Send a newsletter to all active subscribers'

    def add_arguments(self, parser):
        # Create a mutually exclusive group for newsletter source
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--html_file',
                           type=str,
                           help='Path to HTML content file')
        group.add_argument('--newsletter_id',
                           type=int,
                           help='ID of the NewsletterMail to send')

        # Optional arguments
        parser.add_argument(
            '--subject',
            type=str,
            help='Email subject (overrides newsletter subject if '
            '--newsletter_id is used)')
        parser.add_argument(
            '--test_email',
            type=str,
            help='Send a test email to this address instead of all subscribers'
        )

    def handle(self, *args, **options):
        html_file_path = options.get('html_file')
        newsletter_id = options.get('newsletter_id')
        test_email = options.get('test_email')

        # Get content from file or database
        if html_file_path:
            try:
                with open(html_file_path, 'r') as file:
                    html_content = file.read()
                subject = options.get('subject')
                if not subject:
                    self.stderr.write(
                        self.style.ERROR(
                            "Subject is required when using --html_file"))
                    return
                newsletter = None
            except FileNotFoundError:
                self.stderr.write(
                    self.style.ERROR(f"HTML file not found: {html_file_path}"))
                return
        else:  # Using newsletter_id
            try:
                newsletter = NewsletterMail.objects.get(id=newsletter_id)
                html_content = newsletter.html_content
                subject = options.get('subject') or newsletter.subject
            except NewsletterMail.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"Newsletter with ID {newsletter_id} not found"))
                return

        # Determine recipients
        if test_email:
            recipient_list = [test_email]
            self.stdout.write(f"Sending test newsletter to {test_email}")
        else:
            recipient_list = None  # Will use all active subscribers
            subscriber_count = NewsletterSubscriber.objects.filter(
                is_active=True).count()
            self.stdout.write(
                f"Sending newsletter to {subscriber_count} subscribers")

        # Send the newsletter
        success = send_newsletter_email(subject, html_content, recipient_list)

        # Update the newsletter record if using a database newsletter
        if success and newsletter and not test_email:
            # Get the list of subscribers who received the newsletter
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            newsletter.sent_at = timezone.now()
            newsletter.save()

            # Add subscribers to the sent_to field
            newsletter.sent_to.add(*subscribers)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Newsletter '{newsletter.subject}' sent successfully and "
                    "updated in database!"))
        elif success:
            self.stdout.write(
                self.style.SUCCESS("Newsletter sent successfully!"))
        else:
            self.stderr.write(self.style.ERROR("Failed to send newsletter"))
