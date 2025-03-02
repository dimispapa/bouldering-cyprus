from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template import Template, Context

User = get_user_model()


class NewsletterSubscriber(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                null=False,
                                blank=False,
                                related_name='newsletter_subscription')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - " \
            f"{'Active' if self.is_active else 'Inactive'}"

    @property
    def email(self):
        return self.user.email

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name


class NewsletterMail(models.Model):
    subject = models.CharField(max_length=255)
    html_content = models.TextField(
        help_text=(
            "You can use template variables like {{ user.first_name }}, "
            "{{ site_url }}, etc."
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to = models.ManyToManyField('NewsletterSubscriber',
                                     blank=True,
                                     related_name='received_newsletters')

    def __str__(self):
        return self.subject

    def render_content(self, context_dict=None):
        """Render the newsletter content with the given context."""
        if context_dict is None:
            context_dict = {}

        # Add default context variables
        if 'site_url' not in context_dict:
            context_dict['site_url'] = settings.SITE_URL

        template = Template(self.html_content)
        context = Context(context_dict)
        return template.render(context)
