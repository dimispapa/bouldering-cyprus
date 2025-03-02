from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django_summernote.admin import SummernoteModelAdmin
from .models import NewsletterSubscriber, NewsletterMail
from .sendgrid_utils import send_newsletter_email


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active',
                    'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    actions = ['deactivate_subscribers', 'activate_subscribers']

    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} subscribers were successfully deactivated.")

    deactivate_subscribers.short_description = \
        "Deactivate selected subscribers"

    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} subscribers were successfully activated.")

    activate_subscribers.short_description = "Activate selected subscribers"


@admin.register(NewsletterMail)
class NewsletterMailAdmin(SummernoteModelAdmin):
    list_display = ('subject', 'created_at', 'sent_at')
    list_filter = ('created_at', 'sent_at')
    summernote_fields = ('html_content', )
    search_fields = ('subject', )
    readonly_fields = ('sent_at', )
    actions = ['send_newsletter', 'send_test_newsletter']

    def send_newsletter(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request,
                              "Please select only one newsletter to send.",
                              level=messages.ERROR)
            return

        newsletter = queryset.first()
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)

        if not subscribers.exists():
            self.message_user(request,
                              "There are no active subscribers to send to.",
                              level=messages.WARNING)
            return

        success = send_newsletter_email(newsletter.subject,
                                        newsletter.html_content)

        if success:
            newsletter.sent_at = timezone.now()
            newsletter.save()
            newsletter.sent_to.add(*subscribers)
            self.message_user(
                request,
                f"Newsletter '{newsletter.subject}' was successfully sent to "
                f"{subscribers.count()} subscribers.")
        else:
            self.message_user(
                request,
                "Failed to send newsletter. Please check the logs.",
                level=messages.ERROR)

    send_newsletter.short_description = \
        "Send newsletter to all active subscribers"

    def send_test_newsletter(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request,
                              "Please select only one newsletter to test.",
                              level=messages.ERROR)
            return

        # Send to the admin user
        admin_email = request.user.email
        if not admin_email:
            self.message_user(
                request,
                "You don't have an email address to send the test to.",
                level=messages.ERROR)
            return

        newsletter = queryset.first()
        success = send_newsletter_email(newsletter.subject,
                                        newsletter.html_content, [admin_email])

        if success:
            self.message_user(
                request,
                f"Test newsletter '{newsletter.subject}' was successfully "
                f"sent to {admin_email}."
            )
        else:
            self.message_user(
                request,
                "Failed to send test newsletter. Please check the logs.",
                level=messages.ERROR)

    send_test_newsletter.short_description = "Send test newsletter to yourself"
