from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm
from newsletter.models import NewsletterSubscriber
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div

User = get_user_model()


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
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    newsletter_opt_in = forms.BooleanField(
        required=False,
        label=("Subscribe to our newsletter to receive updates about new "
               "bouldering spots, events and special offers."),
        initial=False  # Default to unchecked
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if there's newsletter interest from the footer form
        if self.initial.get('newsletter_interest'):
            self.fields['newsletter_opt_in'].initial = True

        # Set up crispy form
        self.helper = FormHelper()
        self.helper.form_id = 'signup_form'
        self.helper.form_class = 'signup'
        self.helper.form_method = 'post'
        self.helper.form_action = 'account_signup'

        self.helper.layout = Layout(
            Field('email', css_class='form-control'),
            Field('first_name', css_class='form-control'),
            Field('last_name', css_class='form-control'),
            Field('password1', css_class='form-control'),
            Field('password2', css_class='form-control'),
            Div(Field('newsletter_opt_in'), css_class='form-group form-check'),
            Submit('submit', 'Sign Up', css_class='button-large w-100'))

    def save(self, request):
        user = super().save(request)

        # Save first and last name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Handle newsletter subscription
        if self.cleaned_data.get('newsletter_opt_in'):
            NewsletterSubscriber.objects.get_or_create(
                user=user, defaults={'is_active': True})

        return user
