from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from .models import NewsletterSubscriber, NewsletterMail
import logging

logger = logging.getLogger(__name__)


@require_GET
@login_required
def unsubscribe_view(request, user_id):
    """View for unsubscribing from the newsletter via the unsubscribe link."""
    try:
        subscriber = get_object_or_404(NewsletterSubscriber, user_id=user_id)
        # Set the subscriber to inactive
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


@login_required
def manage_subscription(request):
    """View for users to manage their newsletter subscription."""
    user = request.user

    # Try to get the subscriber
    try:
        subscriber = NewsletterSubscriber.objects.get(user=user)
        is_subscribed = subscriber.is_active
        logger.info(f"Subscriber found: {subscriber.email}")
    # If the subscriber does not exist, set the subscriber to None
    except NewsletterSubscriber.DoesNotExist:
        subscriber = None
        is_subscribed = False
        logger.info("Subscriber not found")
    # If the form is submitted, handle the action
    if request.method == 'POST':
        action = request.POST.get('action')

        # If the user wants to subscribe, handle the subscription
        if action == 'subscribe':
            logger.info(f"Subscribing user: {user.email}")
            if subscriber:
                subscriber.is_active = True
                subscriber.save()
                logger.info(f"Re-subscribed subscriber: {subscriber.email}")
                messages.success(
                    request, "You have been re-subscribed to our newsletter.")
            else:
                subscriber = NewsletterSubscriber.objects.create(
                    user=user, is_active=True)
                logger.info(f"Created new subscriber: {subscriber}")
                # Send welcome email
                try:
                    # Get the welcome email template
                    welcome_email = NewsletterMail.objects.get(id=1)
                    # Send the welcome email
                    from .sendgrid_utils import send_newsletter_email
                    logger.info(f"Sending welcome email to {subscriber.email}")
                    success = send_newsletter_email(newsletter=welcome_email,
                                                    recipient_list=[
                                                        subscriber.email])
                    if success:
                        messages.success(
                            request,
                            "Thank you for subscribing to our newsletter!")
                    else:
                        logger.error(
                            f"Error sending welcome email for "
                            f"{subscriber.email}")
                        messages.error(
                            request,
                            "An error occurred while processing your "
                            "subscribe request. Please try again later.")

                except Exception as e:
                    logger.error(f"Error sending welcome email: {e}")

        # If the user wants to unsubscribe, handle the unsubscription
        elif action == 'unsubscribe':
            logger.info(f"Unsubscribing user: {user.email}")
            if subscriber:
                subscriber.is_active = False
                subscriber.save()
                logger.info(f"Unsubscribed subscriber: {subscriber.email}")
                messages.success(
                    request, "You have been unsubscribed from our newsletter.")

        # Redirect to the manage subscription page
        return redirect('newsletter:manage_subscription')

    return render(request, 'newsletter/manage_subscription.html',
                  {'is_subscribed': is_subscribed})
