from django import forms
from .models import NewsletterSubscriber


class NewsletterSubscriptionForm(forms.ModelForm):

    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email':
            forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email address',
            }),
            'first_name':
            forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Your first name (optional)',
                }),
            'last_name':
            forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Your last name (optional)',
                }),
        }
