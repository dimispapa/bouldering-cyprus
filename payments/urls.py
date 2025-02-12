from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path(
        "create-payment-intent/",
        views.create_payment_intent,
        name="create_payment_intent",
    ),
    path("checkout-success/", views.checkout_success, name="checkout_success"),
    path("store-order-metadata/", views.store_order_metadata, name="store_order_metadata"),
]
