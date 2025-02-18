from decimal import Decimal
from django.conf import settings
from shop.models import Product
import json


class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        self.cart = self.session.get(settings.CART_SESSION_ID, {})

    def add(self, product, quantity=1, update_quantity=False):
        """
        Add a product to the bag or update its quantity.
        - product: The product instance to add.
        - quantity: Number of items to add.
        - update_quantity: If True, set the quantity instead of incrementing.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0,
                                     "price": str(product.price)}
        if update_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()
        # Return the new quantity
        return self.cart[product_id]["quantity"]

    def save(self):
        """Mark the session as modified to ensure it is saved."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the bag."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the bag and fetch the products
        from the database.
        For each item, add the product object, cast the price to Decimal,
        and compute the total price.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            # Make a copy of the session dictionary for this item
            item = self.cart[str(product.id)].copy()
            item['product'] = product
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Return the total number of items in the bag."""
        return sum(item["quantity"] for item in self.cart.values())

    def cart_total(self):
        """Compute the total cost of all items in the bag."""
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )

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
            'items': [
                {
                    'product_id': str(item['product'].id),
                    'name': item['product'].name,
                    'quantity': item['quantity'],
                    'price': str(item['price']),
                    'total_price': str(item['total_price'])
                } for item in self.get_items()
            ],
            'total': str(self.cart_total()),
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
