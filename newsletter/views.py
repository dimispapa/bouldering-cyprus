from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import NewsletterSubscriber
from .forms import NewsletterSubscriptionForm
import logging

logger = logging.getLogger(__name__)


def subscribe_view(request):
    """View for newsletter subscription page."""
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Check if already subscribed
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': form.cleaned_data.get('first_name', ''),
                    'last_name': form.cleaned_data.get('last_name', ''),
                    'is_active': True,
                    'user':
                    request.user if request.user.is_authenticated else None
                })

            if not created and not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()
                messages.success(
                    request, "You have been resubscribed to our newsletter.")
            elif not created:
                messages.info(request,
                              "You are already subscribed to our newsletter.")
            else:
                messages.success(
                    request, "Thank you for subscribing to our newsletter!")

            return redirect('home')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
        form = NewsletterSubscriptionForm(initial=initial_data)

    return render(request, 'newsletter/subscribe.html', {'form': form})


def unsubscribe_view(request, email):
    """View for unsubscribing from the newsletter."""
    try:
        subscriber = get_object_or_404(NewsletterSubscriber, email=email)
        subscriber.is_active = False
        subscriber.save()
        messages.success(
            request,
            "You have been successfully unsubscribed from our newsletter.")
    except Exception as e:
        logger.error(f"Error unsubscribing from newsletter: {e}")
        messages.error(
            request,
            "An error occurred while processing your unsubscribe request.")

    return redirect('home')


@require_POST
def ajax_subscribe(request):
    """AJAX endpoint for newsletter subscription from footer or popup."""
    form = NewsletterSubscriptionForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']

        # Check if already subscribed
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
                'is_active': True,
                'user': request.user if request.user.is_authenticated else None
            })

        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save()
            messages.success(request,
                             "You have been resubscribed to our newsletter.")
            return redirect('home')
        elif not created:
            messages.info(request,
                          "You are already subscribed to our newsletter.")
            return redirect('home')
        else:
            messages.success(request,
                             "Thank you for subscribing to our newsletter!")
            return redirect('home')
    else:
        errors = {field: error[0] for field, error in form.errors.items()}
        logger.error(f"Error subscribing to newsletter: {errors}")
        messages.error(
            request, f'An error occurred while subscribing to the newsletter.'
            f' {errors["email"]}')
        return redirect('home')


@login_required
def manage_subscription(request):
    """View for users to manage their newsletter subscription."""
    user = request.user
    try:
        subscriber = NewsletterSubscriber.objects.get(user=user)
        is_subscribed = subscriber.is_active
    except NewsletterSubscriber.DoesNotExist:
        subscriber = None
        is_subscribed = False

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'subscribe':
            if subscriber:
                subscriber.is_active = True
                subscriber.save()
            else:
                NewsletterSubscriber.objects.create(email=user.email,
                                                    first_name=user.first_name,
                                                    last_name=user.last_name,
                                                    is_active=True,
                                                    user=user)
            messages.success(request,
                             "You have been subscribed to our newsletter.")
            return redirect('newsletter:manage_subscription')

        elif action == 'unsubscribe':
            if subscriber:
                subscriber.is_active = False
                subscriber.save()
                messages.success(
                    request, "You have been unsubscribed from our newsletter.")
            return redirect('newsletter:manage_subscription')

    return render(request, 'newsletter/manage_subscription.html',
                  {'is_subscribed': is_subscribed})
