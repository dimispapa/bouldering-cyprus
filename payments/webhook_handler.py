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
        try:
            # Get the payment intent
            intent = event.data.object

            # Get order details from intent
            stripe_piid = intent.id
            first_name = intent.shipping.name.split()[0]
            last_name = intent.shipping.name.split()[1]
            email = intent.receipt_email
            phone = intent.shipping.phone
            address_line1 = intent.shipping.address.line1
            address_line2 = intent.shipping.address.line2
            postal_code = intent.shipping.address.postal_code
            town_or_city = intent.shipping.address.city
            country = intent.shipping.address.country
            order_total = intent.metadata.cart_total
            delivery_cost = intent.metadata.delivery_cost
            grand_total = intent.metadata.grand_total

            logger.info("\n=== Webhook Payment Intent Debug ===")
            logger.info(f"Payment Intent ID: {stripe_piid}")
            logger.info(f"First Name: {first_name}")
            logger.info(f"Last Name: {last_name}")
            logger.info(f"Email: {email}")
            logger.info(f"Phone: {phone}")
            logger.info(f"Address Line 1: {address_line1}")
            logger.info(f"Address Line 2: {address_line2}")
            logger.info(f"Order Total: {order_total}")
            logger.info(f"Delivery Cost: {delivery_cost}")
            logger.info(f"Grand Total: {grand_total}")

            # Check if order already exists
            existing_order = Order.objects.filter(stripe_piid=stripe_piid,
                                                  first_name=first_name,
                                                  last_name=last_name,
                                                  email=email,
                                                  phone=phone,
                                                  address_line1=address_line1,
                                                  address_line2=address_line2,
                                                  order_total=order_total,
                                                  delivery_cost=delivery_cost,
                                                  grand_total=grand_total)
            if existing_order:
                # Order already exists, return success
                logger.info(
                    f"Order already exists: {existing_order.order_number}")
                return JsonResponse({
                    'status': 'Success',
                    'redirect_required': False
                })

            # Order does not exist, proceed to create new order
            logger.info("Order does not exist, creating new order")
            try:
                cart_data = json.loads(intent.metadata.get('cart_data'))
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing cart data from metadata: {e}")
                raise ValueError(
                    "Invalid cart data in payment intent metadata")

            # Get or create order
            order_tuple = Order.objects.get_or_create(
                stripe_piid=stripe_piid,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'country': country,
                    'postal_code': postal_code,
                    'town_or_city': town_or_city,
                    'address_line1': address_line1,
                    'address_line2': address_line2,
                    'original_cart': json.dumps(cart_data),
                    'stripe_piid': stripe_piid,
                    'order_total': order_total,
                    'delivery_cost': delivery_cost,
                    'grand_total': grand_total,
                })

            # get_or_create returns (object, created)
            order = order_tuple[0]
            order_created = order_tuple[1]

            # Create order items if they don't exist
            for item in cart_data['items']:
                OrderItem.objects.get_or_create(order=order,
                                                product_id=item['product_id'],
                                                defaults={
                                                    'quantity':
                                                    item['quantity'],
                                                    'item_total':
                                                    float(item['total_price'])
                                                })

            logger.info(f"Successfully processed order {order.order_number}")

            # Send confirmation email
            self._send_confirmation_email(order)

            if order_created:
                return JsonResponse({
                    'status':
                    'success',
                    'redirect_required':
                    True,
                    'redirect_url':
                    f'/payments/checkout-success?payment_intent={intent.id}'
                })

            return JsonResponse({
                'status': 'success',
                'redirect_required': False
            })

        except Exception as e:
            logger.error(f"Error in webhook handler: {e}")
            return JsonResponse(
                {
                    'status': 'error',
                    'error': "Error in webhook handler"
                },
                status=500)

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        logger.info(f'Unhandled webhook received: {event.type}')
        return JsonResponse({'status': 'Unhandled webhook received'})
