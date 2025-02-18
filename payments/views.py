import stripe
import logging
import time
import json
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
from orders.models import OrderItem
from django.db import IntegrityError
from shop.models import Product

# Configure logging
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(cart):
    """Helper function to create a payment intent."""
    try:
        # Calculate the total amount
        stripe_total = round(cart.cart_total() * 100)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )
        return intent
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        return JsonResponse(
            {
                "error":
                "An error occurred while creating the payment intent. "
                "Please get in touch if the problem persists."
            },
            status=403)


@require_GET
def checkout(request):
    """Endpoint to handle the checkout process."""
    # Check if the cart is empty
    cart = Cart(request)
    if not len(cart):
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    # Validate stock before proceeding
    invalid_items = cart.validate_stock()
    if invalid_items:
        for item in invalid_items:
            messages.error(
                request,
                f"Only {item['available']} units available for {item['name']}"
            )
        return redirect('cart_detail')

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
                        # Cart data using existing serialization method
                        'cart_data':
                        cart.to_json(),
                        'cart_total': order_total,
                        'delivery_cost': delivery_cost,
                        'grand_total': grand_total,
                        'order_form_data': form_data
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
                    receipt_email=form_data.get('email')
                )

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

                context = {
                    'order': order,
                    'payment_intent': payment_intent,
                }

                logger.info(
                    f"Items in order: {[f'{item.product.name} '
                                        f'(qty: {item.quantity})'
                                        for item in order.items.all()]}"
                )
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
        messages.error(
            request,
            'Sorry, an error occurred while processing your payment.')
        return redirect(reverse('checkout'))


def create_order_from_payment(request, payment_intent):
    """Helper function to create an order from a payment intent
    and form data."""
    max_retries = settings.ORDER_CREATION_RETRIES
    retry_delay = settings.ORDER_CREATION_RETRY_DELAY

    try:
        logger.info("\n=== Starting Order Creation ===")
        logger.info(f"Payment Intent ID: {payment_intent.id}")

        # Get the order form data
        form_data = (request.session.get('order_form_data')
                     if request.session.get('order_form_data')
                     else payment_intent.metadata.get('order_form_data'))
        if not form_data:
            raise ValueError("Order form data not found in session or "
                             "payment intent metadata")

        # Get cart data
        cart = Cart(request)
        cart_context = cart_summary(request)

        # Verify stock one last time before creating order
        cart_data = json.loads(payment_intent.metadata.get('cart_data', '{}'))
        for item in cart_data.get('items', []):
            product = Product.objects.get(id=item['product_id'])
            if not product.has_stock(item['quantity']):
                logger.error(f"Insufficient stock for product {product.id}")
                messages.error(
                    request,
                    f"Sorry, only {product.stock} units available for "
                    f"{product.name}"
                )
                return redirect("cart_detail")

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

                # If still no order, create one
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
                    order_total=cart_context['cart_total'],
                    delivery_cost=cart_context['delivery_cost'],
                    grand_total=cart_context['grand_total'],
                )

                logger.info("View handler created new order: "
                            f"{order.order_number}")

                # Create order items and update stock
                for item in cart:
                    product = item['product']
                    quantity = item['quantity']

                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        item_total=item['total_price']
                    )

                    # Update product stock
                    product.stock -= quantity
                    product.save()
                    logger.info(f"Updated stock for {product.name}: "
                                f"new stock level = {product.stock}")

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
