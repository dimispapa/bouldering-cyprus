from django.core.management.base import BaseCommand
from django.utils import timezone
from newsletter.models import NewsletterSubscriber, NewsletterMail
from newsletter.sendgrid_utils import send_newsletter_email


class Command(BaseCommand):
    help = 'Send a newsletter to all active subscribers'

    def add_arguments(self, parser):
        parser.add_argument('--newsletter_id',
                            type=int,
                            required=True,
                            help='ID of the NewsletterMail to send')

        # Optional arguments
        parser.add_argument(
            '--test_email',
            type=str,
            help='Send a test email to this address instead of all subscribers'
        )

    def handle(self, *args, **options):
        newsletter_id = options.get('newsletter_id')
        test_email = options.get('test_email')

        try:
            newsletter = NewsletterMail.objects.get(id=newsletter_id)
        except NewsletterMail.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f"Newsletter with ID {newsletter_id} not found"))
            return

        # Determine recipients
        if test_email:
            recipient_list = [test_email]
            self.stdout.write(f"Sending test newsletter to {test_email}")

            # Create a sample context for testing
            context = {
                'first_name': 'Test',
                'last_name': 'User',
                'email': test_email
            }

            success = send_newsletter_email(newsletter,
                                            recipient_list,
                                            context=context)
        else:
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            subscriber_count = subscribers.count()

            if subscriber_count == 0:
                self.stderr.write(
                    self.style.ERROR("No active subscribers found"))
                return

            self.stdout.write(
                f"Sending newsletter to {subscriber_count} subscribers")

            success = send_newsletter_email(newsletter, subscribers)

        # Update the newsletter record if using a database newsletter
        if success and not test_email:
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
