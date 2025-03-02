from django.urls import reverse


def newsletter_form(request):
    """Add newsletter form data to context of all templates."""
    if request.user.is_authenticated:
        # For authenticated users, redirect to newsletter management
        form_action = reverse('newsletter:manage_subscription')
        form_method = 'get'
    else:
        # For anonymous users, redirect to signup with newsletter interest
        form_action = reverse('account_signup')
        form_method = 'get'

    return {'form_action': form_action, 'form_method': form_method}
