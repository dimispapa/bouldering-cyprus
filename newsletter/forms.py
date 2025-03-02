from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, HTML
from django.urls import reverse


class FooterNewsletterForm(forms.Form):
    """Form for newsletter interest in the footer
    - redirects to signup or manage."""
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(
                                 attrs={
                                     'placeholder': 'Your email',
                                     'class': 'form-control',
                                     'id': 'footer-email-input'
                                 }))

    def __init__(self, *args, **kwargs):
        # Extract form_action if provided, otherwise default to signup
        form_action = kwargs.pop('form_action', reverse('account_signup'))
        form_method = kwargs.pop('form_method', 'get')

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'footer-newsletter-form'
        self.helper.form_method = form_method
        self.helper.form_action = form_action
        self.helper.form_class = 'footer-newsletter-form'
        self.helper.form_show_labels = False

        # Only include the hidden newsletter interest field if going to signup
        if form_action == reverse('account_signup'):
            extra_html = """<input type="hidden" name="newsletter_interest"
                            value="true">"""
        else:
            extra_html = ''

        self.helper.layout = Layout(
            # Email field with button in input group
            Div(Field('email', wrapper_class=''),
                Div(HTML("""<button type="submit" class="button-very-small">
                            <i class="fa-solid fa-envelope-circle-check"></i>
                        </button>"""),
                    css_class='input-group-append'),
                css_class='input-group mb-2'),
            # Conditional hidden field
            HTML(extra_html),
            # Message container
            Div(id='newsletter-message', css_class='mt-1 small'))
