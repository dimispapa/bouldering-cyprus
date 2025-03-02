from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin
from .models import NewsletterSubscriber, NewsletterMail
from .sendgrid_utils import send_newsletter_email


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active',
                    'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

    # These methods help the admin use the properties
    def email(self, obj):
        return obj.email

    def first_name(self, obj):
        return obj.first_name

    def last_name(self, obj):
        return obj.last_name

    # Set column names in admin
    email.short_description = 'Email'
    first_name.short_description = 'First Name'
    last_name.short_description = 'Last Name'

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
    readonly_fields = ('sent_at', 'template_variables_help')
    actions = ['send_newsletter', 'send_test_newsletter']

    def template_variables_help(self, obj):
        """Display help text for template variables."""
        return format_html("""
        <div class="help-block">
            <h4>Available Template Variables:</h4>
            <ul>
                <li><code>{{ site_url }}</code> - The base URL of the site</li>
                <li><code>{{ user.first_name }}</code> - Recipient's first name</li>
                <li><code>{{ user.last_name }}</code> - Recipient's last name</li>
                <li><code>{{ email }}</code> - Recipient's email address</li>
            </ul>
            <p>Example: <code>Hello {{ user.first_name }},</code></p>
            <p>Links: <code>&lt;a href="{{ site_url }}/newsletter/unsubscribe/"&gt;Unsubscribe&lt;/a&gt;</code></p>
        </div>
        """)

    template_variables_help.short_description = "Template Variables"

    def get_fieldsets(self, request, obj=None):
        """Add the template variables help to the fieldsets."""
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets)
        fieldsets.append(('Template Help', {
            'fields': ('template_variables_help', )
        }))
        return fieldsets

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

        success = send_newsletter_email(newsletter, subscribers)

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

        # Create a context with sample data for testing
        context = {
            'user': request.user,
            'first_name': request.user.first_name or 'Test',
            'last_name': request.user.last_name or 'User',
            'email': admin_email
        }

        success = send_newsletter_email(newsletter, [admin_email],
                                        context=context)

        if success:
            self.message_user(
                request,
                f"Test newsletter '{newsletter.subject}' was successfully "
                f"sent to {admin_email}.")
        else:
            self.message_user(
                request,
                "Failed to send test newsletter. Please check the logs.",
                level=messages.ERROR)

    send_test_newsletter.short_description = "Send test newsletter to yourself"
