from decimal import Decimal
from django.conf import settings
from shop.models import Product
import json
import logging

logger = logging.getLogger(__name__)


class Cart:

    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID, {})
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """
        Add a product to the bag or update its quantity.
        - product: The product instance to add.
        - quantity: Number of items to add.
        - update_quantity: If True, set the quantity instead of incrementing.
        """
        try:
            product_id = str(product.id)
            if product_id not in self.cart:
                self.cart[product_id] = {
                    "quantity": 0,
                    "price": str(product.price)
                }
            # If updating quantity, set it directly
            if update_quantity:
                self.cart[product_id]["quantity"] = quantity
            else:
                # If adding quantity, increment it
                self.cart[product_id]["quantity"] += quantity

            # Save the cart after any modification
            self.save()
            # Return the new quantity
            return self.cart[product_id]["quantity"]

        except Exception as e:
            logger.error(f"Error adding product to cart: {e}")

    def save(self):
        """Mark the session as modified to ensure it is saved."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        try:
            product_id = str(product.id)
            if product_id in self.cart:
                del self.cart[product_id]
                self.save()
        except Exception as e:
            logger.error(f"Error removing product from cart: {e}")

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)

        # Create a copy of the cart to avoid modifying the session directly
        cart = self.cart.copy()

        for product in products:
            # Create a new dictionary for each item
            item = cart[str(product.id)].copy()  # Make a copy of the cart item
            item['product'] = product
            item['price'] = str(item['price'])
            item['quantity'] = int(item['quantity'])
            item['total_price'] = str(
                Decimal(item['price']) * item['quantity'])
            yield item

    def __len__(self):
        """Return the total number of items in the bag."""
        return sum(int(item["quantity"]) for item in self.cart.values())

    def cart_total(self):
        """Compute the total cost of all items in the bag."""
        total = sum(
            Decimal(item["price"]) * int(item["quantity"])
            for item in self.cart.values())
        return str(total)  # Return as string to ensure JSON serialization

    def clear(self):
        """Remove the bag from the session."""
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def get_items(self):
        """Return a list of dictionaries representing the cart items."""
        return list(self)

    def serialize(self):
        """Return a JSON-serializable representation of the cart."""
        return {
            'items': [{
                'product_id': str(item['product'].id),
                'name': item['product'].name,
                'quantity': int(item['quantity']),
                'price': str(item['price']),
                'total_price': str(item['total_price'])
            } for item in self.get_items()],
            'total':
            self.cart_total(),
        }

    def to_json(self):
        """Return a JSON string representation of the cart."""
        return json.dumps(self.serialize())

    def has_invalid_items(self):
        """Check if any items in cart have invalid quantities"""
        for item in self:
            product = item['product']
            if not product.has_stock(item['quantity']):
                return True
        return False

    def validate_stock(self):
        """Return list of items with stock issues"""
        invalid_items = []
        for item in self:
            product = item['product']
            if not product.has_stock(item['quantity']):
                invalid_items.append({
                    'name': product.name,
                    'requested': item['quantity'],
                    'available': product.stock
                })
        return invalid_items
