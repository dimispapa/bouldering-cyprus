from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm
from newsletter.models import NewsletterSubscriber


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not authenticate(username=self.user.username, password=password):
            raise forms.ValidationError(
                _("Your password was entered incorrectly. "
                  "Please enter it again."))
        return password


class CustomSignupForm(SignupForm):
    """Custom signup form that allows users to subscribe to the newsletter."""
    newsletter_opt_in = forms.BooleanField(
        required=False,
        initial=True,
        label="Subscribe to our newsletter to receive updates about new "
              "bouldering spots and special offers."
    )

    def save(self, request):
        # First save the user using the parent's save method
        user = super(CustomSignupForm, self).save(request)

        # Handle newsletter subscription
        if self.cleaned_data.get('newsletter_opt_in'):
            NewsletterSubscriber.objects.get_or_create(email=user.email,
                                                       defaults={
                                                           'first_name':
                                                           user.first_name,
                                                           'last_name':
                                                           user.last_name,
                                                           'is_active': True,
                                                           'user': user
                                                       })

        return user
