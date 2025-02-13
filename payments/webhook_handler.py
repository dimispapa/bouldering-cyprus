import logging
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from orders.models import Order, OrderItem
import json
from django.http import JsonResponse

# Configure logging
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


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
        """Handle the payment_intent.succeeded webhook."""
        intent = event.data.object
        logger.info(f"Intent: {intent}")
        # Get shipping details, with fallback to metadata
        shipping_details = intent.shipping
        if not shipping_details or not shipping_details.address:
            metadata = intent.metadata
            if metadata:
                shipping_details = {
                    'name': metadata.get('shipping_name'),
                    'phone': metadata.get('shipping_phone'),
                    'address': {
                        'line1': metadata.get('shipping_address1'),
                        'line2': metadata.get('shipping_address2'),
                        'city': metadata.get('shipping_city'),
                        'postal_code': metadata.get('shipping_postal_code'),
                        'country': metadata.get('shipping_country'),
                    }
                }

        if not shipping_details:
            raise ValueError("No shipping details found in payment intent")

        # Get cart data and totals from metadata
        metadata = intent.metadata
        try:
            cart_data = json.loads(metadata.get('cart_data', '{}'))
            cart_total = float(metadata.get('cart_total', 0))
            delivery_cost = float(metadata.get('delivery_cost', 0))
            grand_total = float(metadata.get('grand_total', 0))
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing cart data from metadata: {e}")
            raise ValueError("Invalid cart data in payment intent metadata")

        # Get the Charge object
        charge = stripe.Charge.retrieve(intent.latest_charge)
        billing_details = charge.billing_details
        stripe_piid = intent.id

        try:
            # Get or create order
            order = Order.objects.get_or_create(
                stripe_piid=stripe_piid,
                defaults={
                    'first_name':
                    billing_details.name.split()[0] if billing_details.name
                    else shipping_details['name'].split()[0],
                    'last_name':
                    billing_details.name.split()[-1] if billing_details.name
                    else shipping_details['name'].split()[-1],
                    'email':
                    billing_details.email if billing_details.email else None,
                    'phone':
                    billing_details.phone
                    if billing_details.phone else shipping_details['phone'],
                    'country':
                    shipping_details['address']['country'],
                    'postal_code':
                    shipping_details['address']['postal_code'],
                    'town_or_city':
                    shipping_details['address']['city'],
                    'address_line1':
                    shipping_details['address']['line1'],
                    'address_line2':
                    shipping_details['address']['line2'],
                    'original_cart':
                    json.dumps(cart_data),
                    'stripe_piid':
                    stripe_piid,
                    'order_total':
                    cart_total,
                    'delivery_cost':
                    delivery_cost,
                    'grand_total':
                    grand_total,
                })

            # Create order items from cart data
            if isinstance(order, tuple):
                order = order[0]  # get_or_create returns (object, created)

            # Create order items if they don't exist
            if cart_data and 'items' in cart_data:
                for item in cart_data['items']:
                    OrderItem.objects.get_or_create(
                        order=order,
                        product_id=item['product_id'],
                        defaults={
                            'quantity': item['quantity'],
                            'price': float(item['price'])
                        })

            logger.info(f"Successfully processed order {order.order_number}")
            success = self._send_confirmation_email(order)
            return JsonResponse({'status': 'Successfully processed order'
                                 if success else 'Error processing order'})

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return JsonResponse({'status': 'Error creating order'}, status=500)

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        logger.info(f'Unhandled webhook received: {event.type}')
        return JsonResponse({'status': 'Unhandled webhook received'})
