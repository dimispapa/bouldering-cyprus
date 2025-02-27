import stripe
import logging
import time
import json
from datetime import datetime
from decimal import Decimal
from django.urls import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from orders.forms import OrderForm
from orders.models import Order, OrderItem
from rentals.models import CrashpadBooking
from cart.cart import Cart
from cart.contexts import cart_summary
from django.db import IntegrityError, transaction
from payments.utils import validate_item_stock

# Configure logging
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(cart):
    """Helper function to create a payment intent."""
    try:
        # Calculate the total amount
        stripe_total = int(cart.cart_total() * 100)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )
        return intent
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise Exception(f"Error creating payment intent: {str(e)}")


@require_GET
def checkout(request):
    """Endpoint to handle the checkout process."""
    # Check if the cart is empty
    cart = Cart(request)
    if not len(cart):
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    # Validate stock and availability before proceeding
    for item in cart.get_items():
        validate_item_stock(item, request)

    try:
        # Proceed with checkout
        intent = create_payment_intent(cart)

        # Render the checkout page with cart and order form objects
        context = {
            "cart":
            cart,
            "order_form":
            OrderForm(
                stripe_public_key=settings.STRIPE_PUBLIC_KEY,
                stripe_client_secret=intent.client_secret,
            ),
        }
        return render(request, "payments/checkout.html", context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('cart_detail')


@require_POST
def store_order_metadata(request):
    """Endpoint to store order data in PaymentIntent metadata and session."""
    try:
        logger.info("\n=== Storing Order Metadata ===")
        logger.info(f"POST data: {request.POST}")

        form = OrderForm(request.POST)
        if form.is_valid():
            # Get the cleaned form data
            form_data = form.cleaned_data
            logger.info(f"Form data: {form_data}")

            # Store form data in session
            request.session['order_form_data'] = form_data

            # Get cart from the session object and use its methods
            cart = Cart(request)
            cart_context = cart_summary(request)
            order_total = cart_context['cart_total']
            delivery_cost = cart_context['delivery_cost']
            grand_total = cart_context['grand_total']

            # Get client secret
            client_secret = request.POST.get('stripe-client-secret')
            if not client_secret:
                logger.error("No client secret found in request POST data")
                return JsonResponse(
                    {
                        'status': 'error',
                        'error': 'No client secret provided'
                    },
                    status=400)

            try:
                payment_intent_id = client_secret.split('_secret_')[0]

                # Update PaymentIntent with metadata
                stripe.PaymentIntent.modify(
                    payment_intent_id,
                    # Update payment intent amount to include delivery cost
                    amount=int(grand_total * 100),
                    metadata={
                        'cart_data': cart.to_json(),
                        'cart_total': str(order_total),
                        'delivery_cost': str(delivery_cost),
                        'grand_total': str(grand_total),
                        'order_form_data': json.dumps(form_data),
                        'session_id': request.session.session_key
                    },
                    # Shipping details
                    shipping={
                        'name':
                        " ".join([
                            form_data.get('first_name'),
                            form_data.get('last_name')
                        ]),
                        'phone':
                        form_data.get('phone'),
                        'address': {
                            'line1': form_data.get('address_line1'),
                            'line2': form_data.get('address_line2', ''),
                            'city': form_data.get('town_or_city'),
                            'postal_code': form_data.get('postal_code'),
                            'country': form_data.get('country'),
                        },
                    },
                    # Receipt email
                    receipt_email=form_data.get('email'))

                logger.info("Successfully stored metadata in PaymentIntent")
                return JsonResponse({'status': 'success'})

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {str(e)}")
                return JsonResponse(
                    {
                        'status': 'error',
                        'error': 'Error updating PaymentIntent'
                    },
                    status=400)

        else:
            logger.error(f"Form validation failed: {form.errors}")
            return JsonResponse(
                {
                    'status': 'error',
                    'errors': form.errors,
                    'message': 'Form validation failed'
                },
                status=400)

    except Exception as e:
        logger.exception(f"Unexpected error in store_order_metadata: {e}")
        return JsonResponse(
            {
                'status': 'error',
                'error': 'An unexpected error occurred'
            },
            status=500)


def create_order_from_payment(request, payment_intent):
    """Helper function to create an order from a payment intent
    and form data."""
    max_retries = settings.ORDER_CREATION_RETRIES
    retry_delay = settings.ORDER_CREATION_RETRY_DELAY

    try:
        logger.info("\n=== Starting Order Creation ===")
        logger.info(f"Payment Intent ID: {payment_intent.id}")

        # Get the order form data from session or payment intent metadata
        form_data = request.session.get('order_form_data')
        if not form_data:
            metadata_form_data = payment_intent.metadata.get('order_form_data')
            if metadata_form_data:
                form_data = json.loads(metadata_form_data)

        if not form_data:
            raise ValueError("Order form data not found in session or "
                             "payment intent metadata")

        # Try to get cart from session first,
        # fall back to payment intent metadata
        if settings.CART_SESSION_ID in request.session:
            cart = Cart(request=request)
            cart_context = cart_summary(request)
            cart_total = cart_context['cart_total']
            delivery_cost = cart_context['delivery_cost']
            grand_total = cart_context['grand_total']
        else:
            cart = Cart(
                cart_data=json.loads(payment_intent.metadata.get('cart_data')))
            cart_total = Decimal(payment_intent.metadata.get('cart_total'))
            delivery_cost = Decimal(
                payment_intent.metadata.get('delivery_cost'))
            grand_total = Decimal(payment_intent.metadata.get('grand_total'))

        # Verify stock and availability one last time before creating order
        for item in cart.get_items():
            validate_item_stock(item, request)

        # First, check if order already exists
        existing_order = Order.objects.filter(
            stripe_piid=payment_intent.id).first()
        if existing_order:
            logger.info("View handler found existing order immediately: "
                        f"{existing_order.order_number}")
            return existing_order

        # If no order exists, wait briefly to give webhook priority
        time.sleep(retry_delay)

        for attempt in range(max_retries):
            try:
                # Check again after delay
                existing_order = Order.objects.filter(
                    stripe_piid=payment_intent.id).first()
                if existing_order:
                    logger.info("View handler found existing order after "
                                f"delay: {existing_order.order_number}")
                    return existing_order

                # If still no order, create one with transaction
                with transaction.atomic():
                    order = Order.objects.create(
                        stripe_piid=payment_intent.id,
                        first_name=form_data.get('first_name'),
                        last_name=form_data.get('last_name'),
                        email=form_data.get('email'),
                        phone=form_data.get('phone'),
                        country=form_data.get('country'),
                        postal_code=form_data.get('postal_code'),
                        town_or_city=form_data.get('town_or_city'),
                        address_line1=form_data.get('address_line1'),
                        address_line2=form_data.get('address_line2', ''),
                        original_cart=cart.to_json(),
                        order_total=cart_total,
                        delivery_cost=delivery_cost,
                        grand_total=grand_total,
                    )

                    logger.info("View handler created new order: "
                                f"{order.order_number}")

                    # Create order items/bookings and update stock/availability
                    for item in cart:
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
                            check_in = datetime.strptime(
                                item['check_in'], '%Y-%m-%d').date()
                            check_out = datetime.strptime(
                                item['check_out'], '%Y-%m-%d').date()
                            # Create rental booking
                            CrashpadBooking.objects.create(crashpad=crashpad,
                                                           order=order,
                                                           check_in=check_in,
                                                           check_out=check_out)
                            logger.info(f"Created booking for {crashpad.name}"
                                        f": {check_in} to {check_out}")

                        # Update order totals
                        order.update_total()

                    return order

            except IntegrityError as e:
                if attempt < max_retries - 1:
                    logger.info(f"Retry attempt {attempt + 1}: Order creation "
                                "failed, waiting...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached, checking one last time "
                                 "for existing order")
                    final_check = Order.objects.filter(
                        stripe_piid=payment_intent.id).first()
                    if final_check:
                        return final_check
                    raise e

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise e


@require_GET
def checkout_success(request):
    """Endpoint to handle successful checkout and create order."""
    logger.info("\n=== Starting Checkout Success ===")

    payment_intent_id = request.GET.get('payment_intent')
    redirect_status = request.GET.get('redirect_status')

    logger.info(f"Payment Intent ID: {payment_intent_id}")
    logger.info(f"Redirect Status: {redirect_status}")

    if not payment_intent_id:
        messages.error(request, "No payment information found")
        return redirect(reverse('checkout'))

    try:
        # First try to find an existing order
        order = Order.objects.filter(stripe_piid=payment_intent_id).first()

        if order:
            # Order exists, just show the success page
            # Render the success page with order details,
            # contact details, and crashpad pickup address
            context = {
                'order': order,
                'whatsapp_number': settings.WHATSAPP_NUMBER,
                'contact_email': settings.DEFAULT_FROM_EMAIL,
                'crashpad_pickup_address': settings.CRASHPAD_PICKUP_ADDRESS
            }
            return render(request, 'payments/checkout_success.html', context)

        # Simulate a failure in the normal checkout process
        # if TEST_WEBHOOK_ORDER_HANDLER is True
        if settings.TEST_WEBHOOK_ORDER_HANDLER:
            logger.info("Simulating checkout failure for testing webhook "
                        "handling")
            raise Exception("Simulated checkout failure")

        # If no order exists, try to create it
        # Retrieve the payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        logger.info("\n=== Payment Intent ===")
        logger.info(f"Status: {payment_intent.status}")
        logger.info(f"Amount: {payment_intent.amount}")

        if payment_intent.status == 'succeeded':
            try:
                # Create order using stored form data and payment intent
                order = create_order_from_payment(request, payment_intent)
                logger.info("\n=== Order Details ===")
                logger.info(f"Order Number: {order.order_number}")
                logger.info(f"Email: {order.email}")
                logger.info(f"Total: {order.grand_total}")

                # Clear the session data
                clear_session_data(request)

                messages.success(
                    request, f'Order successfully processed! '
                    f'Your order number is {order.order_number}. '
                    f'A confirmation email will be sent to {order.email}.')

                # Render the success page with order details,
                # contact details, and crashpad pickup address
                context = {
                    'order': order,
                    'whatsapp_number': settings.WHATSAPP_NUMBER,
                    'contact_email': settings.DEFAULT_FROM_EMAIL,
                    'crashpad_pickup_address': settings.CRASHPAD_PICKUP_ADDRESS
                }
                response = render(request, 'payments/checkout_success.html',
                                  context)
                logger.info("\n=== Checkout Success Template Rendered ===")
                logger.info(f"Response status code: {response.status_code}")
                return response

            except Exception as e:
                logger.error("Error in Order Creation in view handler:"
                             f" {str(e)}")
                raise e

        else:
            messages.error(request, 'Payment was unsuccessful')
            return redirect(reverse('checkout'))

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in checkout_success: {str(e)}")
        messages.error(request, f'Payment error: {str(e)}')
        return redirect(reverse('checkout'))

    except Exception as e:
        logger.error(f"Unexpected error in checkout_success: {str(e)}")
        # Give webhook handler a chance to create the order
        time.sleep(settings.ORDER_CREATION_RETRY_DELAY)

        # Check if payment succeeded and order exists
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        order = Order.objects.filter(stripe_piid=payment_intent_id).first()

        # If payment succeeded and order exists, render the success page
        if payment_intent.status == 'succeeded' and order:
            messages.success(
                request, 'Order successfully processed! '
                f'Your order number is {order.order_number}. '
                f'A confirmation email will be sent to {order.email}.')
            # Render the success page with order details,
            # contact details, and crashpad pickup address
            context = {
                'order': order,
                'whatsapp_number': settings.WHATSAPP_NUMBER,
                'contact_email': settings.DEFAULT_FROM_EMAIL,
                'crashpad_pickup_address': settings.CRASHPAD_PICKUP_ADDRESS
            }
            return render(request, 'payments/checkout_success.html', context)
        # Otherwise, show an error message and redirect to checkout
        else:
            messages.error(
                request,
                'Sorry, an error occurred while processing your payment.')
            return redirect(reverse('checkout'))


def clear_session_data(request):
    """Clear the order form data and cart from the session."""
    # Clear the order form data from the session if not cleared
    if 'order_form_data' in request.session:
        del request.session['order_form_data']
    logger.info("Order form data cleared from session")

    # Clear the cart
    cart = Cart(request)
    cart.clear()
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    logger.info("Cart cleared from session")
