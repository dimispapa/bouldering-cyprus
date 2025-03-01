from django import forms
from .models import Order
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Row,
    Column,
    HTML,
    Field,
    Div,
    Fieldset,
    Hidden,
)
from crispy_forms.bootstrap import Accordion, AccordionGroup


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address_line1",
            "address_line2",
            "town_or_city",
            "postal_code",
            "country",
            "comments",
        ]

    def set_placeholders(self, placeholders):
        """Set placeholders for form fields."""
        for field in self.fields:
            if self.fields[field].required:
                placeholder = f"{placeholders[field]} *"
            else:
                placeholder = placeholders[field]
            self.fields[field].widget.attrs["placeholder"] = placeholder
            self.fields[field].label = False

    def __init__(self, *args, **kwargs):
        stripe_public_key = kwargs.pop("stripe_public_key", "")
        stripe_client_secret = kwargs.pop("stripe_client_secret", "")

        super().__init__(*args, **kwargs)
        placeholders = {
            "first_name":
            "First name",
            "last_name":
            "Last name",
            "email":
            "Email address",
            "phone":
            "Phone number",
            "address_line1":
            "Street address 1",
            "address_line2":
            "Street address 2",
            "town_or_city":
            "Town or city",
            "postal_code":
            "Postal code",
            "country":
            "Country",
            "comments":
            "Add any additional information, comments or requests here",
        }
        # Set autofocus on first name field
        self.fields["first_name"].widget.attrs["autofocus"] = True
        # Set placeholders for form fields
        self.set_placeholders(placeholders)
        # Set helper for form
        self.helper = FormHelper()
        self.helper.form_id = "payment-form"
        # Set layout for form
        self.helper.layout = Layout(
            # Customer Details Section
            Fieldset(
                "Customer details",
                Row(
                    Column("first_name", css_class="form-group col-md-6"),
                    Column("last_name", css_class="form-group col-md-6"),
                    css_class="form-row",
                ),
                Row(
                    Column("email", css_class="form-group col-md-6"),
                    Column("phone", css_class="form-group col-md-6"),
                    css_class="form-row",
                ),
            ),
            HTML("""<hr>"""),
            Fieldset(
                "Delivery address",
                Field("address_line1"),
                Field("address_line2"),
                Row(
                    Column("town_or_city", css_class="form-group col-md-6"),
                    Column("postal_code", css_class="form-group col-md-3"),
                    Column("country", css_class="form-group col-md-3"),
                    css_class="form-row",
                ),
            ),
            # Additional Information Section - Using Accordion
            Accordion(
                AccordionGroup(
                    "Additional information",
                    Field("comments"),
                    active=False,
                ), ),
            HTML("""<hr>"""),
            # Payment Details Section
            Fieldset(
                "Payment details",
                # Express Checkout Section
                HTML("""
                    <div class="form-group mb-4">
                        <label for="express-checkout-element">Express checkout</label>
                        <div id="express-checkout-element" class="stripe-element border border-dark rounded p-3">
                            <!-- Express Checkout Element will be inserted here -->
                        </div>
                    </div>
                """),
                # Card Element Section
                HTML("""
                    <div class="form-group mb-4">
                        <label for="payment-element">OR other payment methods</label>
                        <div id="payment-element" class="stripe-element border border-dark rounded p-3">
                            <!-- Payment Element will be inserted here -->
                        </div>
                    </div>
                """),
                HTML(
                    """<div id="payment-errors" role="alert" class="mt-2 text-danger hidden"></div>"""
                ),
                # Hidden Stripe Fields
                Hidden("stripe-public-key",
                       stripe_public_key,
                       id="stripe-public-key"),
                Hidden(
                    "stripe-client-secret",
                    stripe_client_secret,
                    id="stripe-client-secret",
                ),
            ),
            # Place Order Button
            Div(
                HTML("""
                    <button id="submit" type="submit" name="submit" class="button-payment mt-3">
                        <span id="spinner" class="spinner-border spinner-border-sm hidden" role="status" aria-hidden="true"></span>
                        <span id="button-text">
                            <i class="fa-solid fa-lock"></i> Place order
                        </span>
                    </button>
                """),
                css_class="text-end",
            ),
        )
