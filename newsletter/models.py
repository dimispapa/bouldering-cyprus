from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                related_name='newsletter_subscription')

    def __str__(self):
        return self.email


class NewsletterMail(models.Model):
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to = models.ManyToManyField(NewsletterSubscriber, blank=True)

    def __str__(self):
        return self.subject
