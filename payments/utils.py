import time
import logging
from orders.models import Order, OrderItem
from rentals.models import CrashpadBooking
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Configure logging
logger = logging.getLogger(__name__)


def get_error_message(error):
    """
    Map the error message for the given error.
    """
    error_messages = {
        'insufficient_stock':
        f"Sorry, only {error.product.stock} units available for "
        f"{error.product.name}",
        'dates_unavailable':
        f"Sorry, {error.crashpad.name} is no longer available for "
        f"the selected dates",
        'dates_in_past':
        f"The selected dates for {error.crashpad.name} are in the past",
    }
    return error_messages[error]


def validate_stock(cart):
    """
    Validate items in the cart.
    Returns a tuple with a boolean and an error message.
    """
    # Validate items using the cart method
    has_errors, error_dict = cart.has_invalid_items()

    if has_errors:
        if error_dict['error'] == 'insufficient_stock':
            error_message = (f"Sorry, {error_dict['product'].name} only has "
                             f"{error_dict['product'].stock} items in stock. "
                             f"Please adjust your quantity.")
        elif error_dict['error'] == 'dates_unavailable':
            error_message = (
                f"Sorry, {error_dict['crashpad'].name} is no longer "
                f"available for the dates {error_dict['dates']}.")
        elif error_dict['error'] == 'dates_in_past':
            error_message = (
                f"Sorry, the selected dates {error_dict['dates']} "
                f"for {error_dict['crashpad'].name} are in the past.")
        else:
            error_message = "An error occurred validating your cart."
        return (False, error_message)

    return (True, None)


def check_existing_order(payment_intent):
    """
    Check if an order already exists for the given payment intent.
    """
    max_retries = settings.ORDER_CREATION_RETRIES
    retry_delay = settings.ORDER_CREATION_RETRY_DELAY

    # Wait briefly to give webhook priority
    time.sleep(retry_delay)

    # Start checking for existing order a few times after delay
    for attempt in range(max_retries):
        # Check for existing order
        existing_order = Order.objects.filter(
            stripe_piid=payment_intent.id).first()
        if existing_order:
            logger.info("View handler found existing order after "
                        f"delay: {existing_order.order_number}")
            # Return the order if found
            return existing_order
        # If no order is found, wait and try again
        if attempt < max_retries - 1:
            logger.info(f"Retry attempt {attempt + 1}: Fetching order "
                        "failed, waiting...")
            time.sleep(retry_delay)
        # If max retries reached, check for existing order one last time
        else:
            logger.info("Max retries reached, checking one last time "
                        "for existing order")
            existing_order = Order.objects.filter(
                stripe_piid=payment_intent.id).first()
            if existing_order:
                # Return the order if found
                return existing_order
    # If no order is found after all retries, return None
    logger.info(
        f"No existing order found for payment intent {payment_intent.id} "
        f"after {max_retries} attempts")
    return None


def create_order_items(order, cart):
    """
    Create order items/bookings for the given order and cart.
    Updates stock and availability.
    """
    logger.info(f"Creating order items for order {order.order_number}")
    logger.info(f"Order PK: {order.pk}")
    logger.info(f"Cart items: {len(cart)}")

    # Make sure the order has a primary key
    if not order.pk:
        logger.error("Order does not have a primary key!")
        raise ValueError("Order must be saved before creating order items")

    for i, item in enumerate(cart):
        logger.info(f"Processing item {i+1}: {item}")

        # Create order items for products
        if item['type'] == 'product':
            product = item['item']
            quantity = item['quantity']
            total_price = item['total_price']

            # Create order item
            OrderItem.objects.create(order=order,
                                     product=product,
                                     quantity=quantity,
                                     item_total=total_price)

            # Update product stock
            product.stock -= quantity
            product.save()
            logger.info(f"Updated stock for {product.name}: "
                        f"new stock level = {product.stock}")

        # Create bookings for crashpad rentals
        elif item['type'] == 'rental':
            crashpad = item['item']
            check_in = datetime.strptime(item['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(item['check_out'], '%Y-%m-%d').date()
            daily_rate = item['daily_rate']
            rental_days = item['rental_days']
            total_price = item['total_price']

            # Create rental booking
            CrashpadBooking.objects.create(crashpad=crashpad,
                                           order=order,
                                           check_in=check_in,
                                           check_out=check_out,
                                           daily_rate=daily_rate,
                                           rental_days=rental_days,
                                           total_price=total_price)

            logger.info(f"Created booking for {crashpad.name}"
                        f": {check_in} to {check_out}")


def send_confirmation_email(order):
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
                'contact_email': settings.DEFAULT_FROM_EMAIL,
                'whatsapp_number': settings.WHATSAPP_NUMBER,
            })
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email])

        logger.info(f"Confirmation email sent for order {order.order_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending confirmation email: {e}")
        return False


def send_rental_confirmation_email(order):
    """
    Send the user a confirmation email for the rental
    """
    try:
        subject = render_to_string(
            'orders/confirmation_emails/'
            'confirmation_email_rentals_subject.txt', {'order': order})
        body = render_to_string(
            'orders/confirmation_emails/'
            'confirmation_email_rentals_body.txt', {
                'order': order,
                'crashpad_pickup_address': settings.CRASHPAD_PICKUP_ADDRESS,
                'contact_email': settings.DEFAULT_FROM_EMAIL,
                'whatsapp_number': settings.WHATSAPP_NUMBER,
            })
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email])
        logger.info("Rental confirmation email sent "
                    f"for order {order.order_number}")
        return True
    except Exception as e:
        logger.error(f"Error sending rental confirmation email: {e}")
        return False
