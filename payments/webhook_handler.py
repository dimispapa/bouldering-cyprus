import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from orders.models import Order

# Configure logging
logger = logging.getLogger(__name__)


class StripeWH_Handler:
    """Handle Stripe webhooks"""

    def __init__(self, request):
        self.request = request

    def _send_confirmation_email(self, order):
        """
        Send the user a confirmation email
        """
        try:
            subject = render_to_string(
                'orders/confirmation_emails/confirmation_email_subject.txt',
                {'order': order})
            body = render_to_string(
                'orders/confirmation_emails/confirmation_email_body.txt', {
                    'order': order,
                    'contact_email': settings.DEFAULT_FROM_EMAIL
                })
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                      [order.email])

            logger.info(
                f"Confirmation email sent for order {order.order_number}")
            return True
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return False

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook from Stripe
        """
        payment_intent = event.data.object

        try:
            order = Order.objects.get(stripe_piid=payment_intent.id)
            return self._send_confirmation_email(order)

        except Order.DoesNotExist:
            logger.error(
                f"Order not found for payment intent {payment_intent.id}")
            return False

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        logger.info(f'Unhandled webhook received: {event.type}')
        return True
