import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .webhook_handler import StripeWH_Handler

# Configure logging
logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def stripe_webhook(request):
    """Listen for webhooks from Stripe"""
    # Setup
    stripe.api_key = settings.STRIPE_SECRET_KEY
    wh_secret = settings.STRIPE_WEBHOOK_SECRET

    # Get the webhook data and verify the signature header
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        return HttpResponse(status=400)

    # Set up a webhook handler for each event type
    wh_handler = StripeWH_Handler(request)

    # Map event types to handler methods
    event_map = {
        'payment_intent.succeeded': wh_handler.handle_payment_intent_succeeded,
        'payment_intent.payment_failed':
        wh_handler.handle_payment_intent_failed,
    }

    # Get the event type and corresponding handler
    event_type = event['type']
    logger.info(f'Event received: {event_type}')
    event_handler = event_map.get(event_type, wh_handler.handle_event)
    # Call the handler for the event
    response = event_handler(event)
    logger.info(f'Webhook processed: {response}')

    return response
