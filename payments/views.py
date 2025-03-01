import stripe
import logging
import json
from decimal import Decimal
from django.urls import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from orders.forms import OrderForm
from orders.models import Order
from cart.cart import Cart
from cart.contexts import cart_summary
from django.db import IntegrityError
from payments.utils import (validate_stock, check_existing_order,
                            create_order_items, send_confirmation_email,
                            send_rental_confirmation_email)

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
            payment_method_types=['card', 'link'],
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
    valid_stock, error_message = validate_stock(cart)
    if not valid_stock:
        logger.error(f"Stock validation failed: {error_message}")
        raise ValueError(error_message)

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
            cart_items = cart.to_json()['cart_items']
            rental_items = cart.to_json()['rental_items']
            cart_context = cart_summary(request)
            cart_total = cart_context['cart_total']
            delivery_cost = cart_context['delivery_cost']
            handling_fee = cart_context['handling_fee']
            grand_total = cart_context['grand_total']
            order_type = cart_context['order_type']
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
                    amount=int(cart_context['grand_total'] * 100),
                    metadata={
                        'cart_items': json.dumps(cart_items),
                        'rental_items': json.dumps(rental_items),
                        'cart_total': cart_total,
                        'delivery_cost': delivery_cost,
                        'handling_fee': handling_fee,
                        'grand_total': grand_total,
                        'order_type': order_type,
                        'comments': form_data.get('comments', ''),
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


def create_or_return_order(request, payment_intent):
    """Helper function to create an order from a payment intent
    and form data."""
    try:
        logger.info("\n=== Starting Order Creation ===")
        logger.info(f"Payment Intent ID: {payment_intent.id}")

        # First, check if order was already created by the webhook handler
        existing_order = check_existing_order(payment_intent)
        if existing_order:
            logger.info("View handler found existing order: "
                        f"{existing_order.order_number}")
            return existing_order
        else:
            logger.info("View handler found no existing order. "
                        "Creating new order.")

        # Get the order form data from session
        form_data = request.session.get('order_form_data')

        # If still no form data, get it from payment intent metadata
        if not form_data:
            metadata_form_data = payment_intent.metadata.get('order_form_data')
            if metadata_form_data:
                form_data = json.loads(metadata_form_data)

        # If still no form data, raise an error
        if not form_data:
            raise ValueError("Order form data not found in session or "
                             "payment intent metadata")
        logger.info(f"Form data fetched: {form_data}")

        # Try to get cart from session first
        if settings.CART_SESSION_ID in request.session:
            cart = Cart(request=request)
            cart_context = cart_summary(request)
            cart_total = cart_context['cart_total']
            delivery_cost = cart_context['delivery_cost']
            handling_fee = cart_context['handling_fee']
            grand_total = cart_context['grand_total']
            order_type = cart_context['order_type']
        # Fall back to get the cart data from payment intent metadata
        else:
            cart_data = {
                'cart_items':
                json.loads(payment_intent.metadata.get('cart_items')),
                'rental_items':
                json.loads(payment_intent.metadata.get('rental_items')),
            }
            cart = Cart(cart_data=cart_data)
            cart_total = Decimal(payment_intent.metadata.get('cart_total'))
            delivery_cost = Decimal(
                payment_intent.metadata.get('delivery_cost'))
            handling_fee = Decimal(payment_intent.metadata.get('handling_fee'))
            grand_total = Decimal(payment_intent.metadata.get('grand_total'))
        logger.info(f"Cart processed: {cart}")
        # Verify stock and availability one last time before creating order
        valid_stock, error_message = validate_stock(cart)
        if not valid_stock:
            logger.error(f"Stock validation failed: {error_message}")
            raise ValueError(error_message)
        logger.info(f"Stock validated: {valid_stock}")

        # Log the form data we're using to create the order
        logger.info(f"Creating order with form data: {form_data}")
        logger.info(f"Cart total: {cart_total}, Delivery: {delivery_cost}, "
                    f"Handling: {handling_fee}, Grand total: {grand_total}")

        # Get or create the order object
        logger.info("Attempting to get or create order")
        order, created = Order.objects.get_or_create(
            stripe_piid=payment_intent.id,
            defaults={
                'first_name': form_data.get('first_name'),
                'last_name': form_data.get('last_name'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone'),
                'country': form_data.get('country'),
                'postal_code': form_data.get('postal_code'),
                'town_or_city': form_data.get('town_or_city'),
                'address_line1': form_data.get('address_line1'),
                'address_line2': form_data.get('address_line2', ''),
                'order_total': cart_total,
                'delivery_cost': delivery_cost,
                'handling_fee': handling_fee,
                'grand_total': grand_total,
                'comments': form_data.get('comments', ''),
                'order_type': order_type,
            })

        logger.info(f"Order {'created' if created else 'retrieved'}")
        logger.info(f"Order: {order}")
        logger.info(f"Order PK: {order.pk}")
        logger.info(f"Order number: {order.order_number}")

        # Only create order items if this is a new order
        if created:
            # Create order items/bookings and update stock/availability
            logger.info("About to create order items")
            create_order_items(order, cart)
            logger.info("Order items created successfully")

            # Update order totals
            order.update_total()
            logger.info("Order totals updated")

            # Send confirmation emails
            send_confirmation_email(order)
            if cart.has_rentals():
                send_rental_confirmation_email(order)

        # Ensure the session data is cleared
        clear_session_data(request)

        return order

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
        # Simulate a failure in the normal checkout process
        # if TEST_WEBHOOK_ORDER_HANDLER is True
        if settings.TEST_WEBHOOK_ORDER_HANDLER:
            logger.info("Simulating checkout failure for testing webhook "
                        "handling")
            raise Exception("Simulated checkout failure")

        # Retrieve the payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        logger.info("\n=== Payment Intent ===")
        logger.info(f"Status: {payment_intent.status}")
        logger.info(f"Amount: {payment_intent.amount}")

        # If payment succeeded, handle order processing
        if payment_intent.status == 'succeeded':
            try:
                # Create or return existing order
                order = create_or_return_order(request, payment_intent)
                logger.info("\n=== Order Details ===")
                logger.info(f"Order Number: {order.order_number}")
                logger.info(f"Email: {order.email}")
                logger.info(f"Total: {order.grand_total}")

                messages.success(
                    request, f'Order successfully processed! '
                    f'Your order number is {order.order_number}. '
                    f'A confirmation email will be sent to {order.email}.')

                # Render the success page with order details,
                # contact details, and crashpad pickup address
                context = {
                    'order': order,
                }
                response = render(request, 'payments/checkout_success.html',
                                  context)
                logger.info("\n=== Checkout Success Template Rendered ===")
                logger.info(f"Response status code: {response.status_code}")
                return response

            except IntegrityError:
                messages.error(
                    request, "An error occurred while processing "
                    "your order. Please contact us to "
                    "resolve this issue.")
                return redirect(reverse('checkout'))

            except Exception as e:
                logger.error("Error in Order processing in view handler:"
                             f" {str(e)}")
                raise e

        else:
            messages.error(request, 'Payment was unsuccessful. Please try '
                           'again.')
            return redirect(reverse('checkout'))

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in checkout_success: {str(e)}")
        messages.error(request, f'Payment error: {str(e)}')
        return redirect(reverse('checkout'))

    except Exception as e:
        logger.error(f"Unexpected error in checkout_success: {str(e)}")
        messages.error(
            request, 'Sorry, an error occurred while processing your payment.')
        return redirect(reverse('checkout'))


def clear_session_data(request):
    """Clear the order form data and cart from the session."""
    # Clear the order form data from the session if not cleared
    if 'order_form_data' in request.session:
        del request.session['order_form_data']
    logger.info("Order form data cleared from session")

    # Clear the cart if not already cleared
    if settings.CART_SESSION_ID in request.session:
        cart = Cart(request)
        cart.clear()
    logger.info("Cart cleared from session")
