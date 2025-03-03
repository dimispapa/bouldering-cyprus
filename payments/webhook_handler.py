import logging
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import json
from django.http import JsonResponse
from orders.models import Order
from django.contrib.auth.models import User
from payments.utils import (validate_stock, create_order_items,
                            send_confirmation_email,
                            send_rental_confirmation_email)
from cart.cart import Cart
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeWH_Handler:
    """Handle Stripe webhooks"""

    def __init__(self, request):
        self.request = request

    def _clear_session_data(self, session_id):
        """Clear the cart and order form data from the session"""
        try:
            from django.contrib.sessions.models import Session
            from django.contrib.sessions.backends.db import SessionStore

            # Create a SessionStore instance with the session key
            session_store = SessionStore(session_key=session_id)

            # Clear cart data using proper session methods
            if settings.CART_SESSION_ID in session_store:
                del session_store[settings.CART_SESSION_ID]
                session_store.save()
                logger.info(f"Cart cleared from session {session_id}")

            # Clear order form data if not already cleared
            if 'order_form_data' in session_store:
                del session_store['order_form_data']
                session_store.save()
                logger.info(
                    f"Order form data cleared from session {session_id}")

        except Session.DoesNotExist:
            logger.warning(f"Session {session_id} not found")
        except Exception as e:
            logger.error(f"Error clearing cart from session: {e}")

    def handle_payment_intent_succeeded(self, event):
        """Handle the payment_intent.succeeded webhook."""
        try:
            intent = event.data.object
            logger.info("\n=== Webhook Payment Intent Processing ===")
            logger.info(f"Payment Intent ID: {intent.id}")

            # Reconstruct cart data from metadata and initialize cart
            cart_data = {
                'cart_items': json.loads(intent.metadata.get('cart_items')),
                'rental_items':
                json.loads(intent.metadata.get('rental_items')),
            }
            cart = Cart(cart_data=cart_data)

            # Verify stock and availability for all items
            valid_stock, error_message = validate_stock(cart)
            if not valid_stock:
                logger.error(f"Stock validation failed: {error_message}")
                return JsonResponse({'error': error_message}, status=400)

            # Prepare order data
            order_data = {
                'first_name': intent.shipping.name.split()[0],
                'last_name': intent.shipping.name.split()[-1],
                'email': intent.receipt_email,
                'phone': intent.shipping.phone,
                'country': intent.shipping.address.country,
                'postal_code': intent.shipping.address.postal_code,
                'town_or_city': intent.shipping.address.city,
                'address_line1': intent.shipping.address.line1,
                'address_line2': intent.shipping.address.line2,
                'order_total': Decimal(str(intent.metadata.get('cart_total'))),
                'delivery_cost':
                Decimal(str(intent.metadata.get('delivery_cost'))),
                'handling_fee':
                Decimal(str(intent.metadata.get('handling_fee'))),
                'grand_total':
                Decimal(str(intent.metadata.get('grand_total'))),
                'order_type': intent.metadata.get('order_type'),
                'comments': intent.metadata.get('comments'),
            }

            # Try to associate with a user if user_id is in metadata
            user_id = intent.metadata.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    order_data['user'] = user
                    logger.info(
                        f"Webhook associating order with user ID: {user_id}")
                except User.DoesNotExist:
                    logger.warning(f"User with ID {user_id} not found")

            # Create or get order
            order, created = Order.objects.get_or_create(stripe_piid=intent.id,
                                                         defaults=order_data)

            # If the order was created, we need to create the order items
            # and update the stock
            if created:
                logger.info(f"Webhook created order: {order.order_number}")
                # Create order items/bookings and update stock/availability
                logger.info("About to create order items")
                create_order_items(order, cart)
                logger.info("Order items created successfully")

                # Update order totals
                order.update_total()
                logger.info("Order totals updated")

                # Send order confirmation email in any case
                send_confirmation_email(order)
                # Send rental confirmation email if there are rentals
                if cart.has_rentals():
                    send_rental_confirmation_email(order)

            # If order was not created, it means it already exists
            else:
                logger.info(
                    f"Webhook found existing order: {order.order_number}")

            # Ensure the session data is cleared
            session_id = intent.metadata.get('session_id')
            self._clear_session_data(session_id)

            return JsonResponse({'status': 'success'})

        except Exception as e:
            logger.error("Error in order creation in webhook handler:"
                         f" {str(e)}")
            raise e

    def handle_payment_intent_failed(self, event):
        """Handle the payment_intent.failed webhook."""
        intent = event.data.object

        logger.info("\n=== Failed Payment Intent Debug ===")
        logger.info(f"Payment Intent ID: {intent.id}")
        logger.info(f"Error: {intent.last_payment_error}")
        logger.info(f"Status: {intent.status}")

        try:
            # Get cart data from metadata
            cart_data = None
            if intent.metadata and 'cart_data' in intent.metadata:
                try:
                    cart_data = json.loads(intent.metadata.cart_data)
                    logger.info(f"Cart data retrieved: {cart_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing cart data: {e}")
                    cart_data = None

            # Get email from payment intent
            customer_email = intent.receipt_email

            if customer_email:
                # Send email about failed payment
                context = {
                    'cart_data':
                    cart_data,
                    'cart_items':
                    cart_data.get('items', []) if cart_data else [],
                    'cart_total':
                    cart_data.get('total', '0.00') if cart_data else '0.00',
                    'payment_error':
                    intent.last_payment_error.get('message', 'Unknown error')
                    if intent.last_payment_error else 'Unknown error',
                    'contact_email':
                    settings.DEFAULT_FROM_EMAIL
                }

                subject = render_to_string(
                    'orders/confirmation_emails/payment_failed_subject.txt',
                    context)
                body = render_to_string(
                    'orders/confirmation_emails/payment_failed_body.txt',
                    context)

                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                          [customer_email])

                logger.info(f"Payment failed email sent to {customer_email}")
            else:
                logger.warning("No customer email found in payment intent")

            return JsonResponse({
                'status': 'success',
                'message': 'Payment failure handled'
            })

        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")
            return JsonResponse(
                {
                    'status': 'error',
                    'error': 'Error handling failed payment'
                },
                status=500)

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        logger.info(f'Unhandled webhook received: {event.type}')
        return JsonResponse({'status': 'Unhandled webhook received'})
