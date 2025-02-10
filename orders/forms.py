from django import forms
from .models import Order
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Row,
    Column,
    Submit,
    HTML,
    Field,
    Div,
    Fieldset,
    Template,
    Hidden,
)


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
            "city",
            "postal_code",
            "country",
        ]

    def __init__(self, *args, **kwargs):
        stripe_public_key = kwargs.pop("stripe_public_key", "")
        stripe_client_secret = kwargs.pop("stripe_client_secret", "")

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_id = "payment-form"
        self.helper.form_action = "#"  # or your specific action URL

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
                Field("address_line1"),
                Field("address_line2"),
                Row(
                    Column("city", css_class="form-group col-md-6"),
                    Column("postal_code", css_class="form-group col-md-3"),
                    Column("country", css_class="form-group col-md-3"),
                    css_class="form-row",
                ),
            ),
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
                        <div id="express-checkout-errors" role="alert" class="mt-2 text-danger"></div>
                    </div>
                """),
                # Card Element Section
                HTML("""
                    <div class="form-group mb-4">
                        <label for="payment-element">Other payment methods</label>
                        <div id="payment-element" class="stripe-element border border-dark rounded p-3">
                            <!-- Payment Element will be inserted here -->
                        </div>
                        <div id="payment-errors" role="alert" class="mt-2 text-danger"></div>
                    </div>
                """),
                # Hidden Stripe Fields
                Hidden("stripe-public-key", stripe_public_key, id="stripe-public-key"),
                Hidden(
                    "stripe-client-secret",
                    stripe_client_secret,
                    id="stripe-client-secret",
                ),
            ),
            Div(
                HTML("""
                    <button type="submit" name="submit" class="button-payment mt-3">
                        <i class="fa-solid fa-lock"></i> Place Order
                    </button>
                """),
                css_class='text-end'
            )
        )
