import stripe
import logging
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
        return redirect(reverse("cart_detail"))

    # Create a PaymentIntent
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
        logger.info("\n=== Store Order Metadata Debug ===")
        logger.info(f"POST data: {request.POST}")

        form = OrderForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            logger.info(f"Form data: {form_data}")

            # Store form data in session
            request.session['order_form_data'] = form_data

            # Get cart from the session object and use its methods
            cart = Cart(request)
            cart_context = cart_summary(request)

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
                    metadata={
                        # Cart data using existing serialization method
                        'cart_data':
                        cart.to_json(),
                        'cart_total': cart_context['cart_total'],
                        'delivery_cost': cart_context['delivery_cost'],
                        'grand_total': cart_context['grand_total']
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
    logger.info("\n=== Starting checkout_success ===")

    payment_intent_id = request.GET.get('payment_intent')
    redirect_status = request.GET.get('redirect_status')

    logger.info(f"Payment Intent ID: {payment_intent_id}")
    logger.info(f"Redirect Status: {redirect_status}")

    if not payment_intent_id:
        messages.error(request, "No payment information found")
        return redirect(reverse('checkout'))

    try:
        # Simulate a failure in the normal checkout process
        # if TEST_WEBHOOK_ORDER_HANDLING is True
        if settings.TEST_WEBHOOK_ORDER_HANDLING:
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

                # Debug order items
                items = order.items.all()
                logger.info("\n=== Order Items ===")
                logger.info(f"Number of items: {items.count()}")
                for item in items:
                    logger.info(f"- {item.quantity}x {item.product.name} "
                                f"(€{item.item_total})")

                # Clear the order form data from the session if not cleared
                if 'order_form_data' in request.session:
                    del request.session['order_form_data']

                # Clear the cart
                cart = Cart(request)
                cart.clear()
                if 'cart' in request.session:
                    del request.session['cart']
                    request.session.modified = True
                logger.info("Cart cleared from session")

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
                logger.info("\n=== Template Rendered ===")
                logger.info(f"Response status code: {response.status_code}")
                return response

            except Exception as e:
                logger.error(f"Error in Order Creation: {str(e)}")
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
    try:
        logger.info("\n=== Starting create_order_from_payment ===")
        logger.info(f"Payment Intent ID: {payment_intent.id}")

        # Get the order form data
        form_data = request.session.get('order_form_data')
        if not form_data:
            raise ValueError("Order form data not found in session")

        # Create an order form instance
        order_form = OrderForm(form_data)

        # Validate form data
        if not order_form.is_valid():
            raise ValueError("Invalid form data")

        # Check if order already exists for this payment intent
        existing_order = Order.objects.filter(
            stripe_piid=payment_intent.id).first()
        if existing_order:
            logger.info(f"Order {existing_order.order_number} already exists "
                        f"for payment {payment_intent.id}")
            return existing_order
        # Create an order from the form data
        order = order_form.save(commit=False)

        # Set payment details
        order.stripe_piid = payment_intent.id

        # Set cart details
        cart = Cart(request)
        cart_context = cart_summary(request)
        order.original_cart = cart.to_json()
        order.delivery_cost = cart_context["delivery_cost"]
        order.order_total = cart_context["cart_total"]
        order.grand_total = cart_context["grand_total"]

        # Save the order
        order.save()

        # Create order items from cart
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
            )
        logger.info(f"Order created: {order.order_number}")
        return order

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise e
