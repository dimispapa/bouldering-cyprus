from decimal import Decimal
from django.conf import settings
from shop.models import Product
from rentals.models import Crashpad
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Cart:

    def __init__(self, request=None, cart_data=None):
        """Initialize the cart."""
        # The cart is initialized from the session
        if request:
            self.session = request.session
            cart = self.session.get(settings.CART_SESSION_ID, {})
            self.cart = cart
        # The cart is initialized from the payment intent
        elif cart_data:
            # Initialize empty cart
            self.cart = {}
            print(f"Cart data: {cart_data}")

            # Process product items
            if 'cart_items' in cart_data:
                for item in cart_data['cart_items']:
                    id = item['id']
                    key = f"product_{id}"
                    self.cart[key] = {
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'type': 'product',
                    }

            # Process rental items
            if 'rental_items' in cart_data:
                for item in cart_data['rental_items']:
                    id = item['id']
                    key = f"rental_{id}"
                    self.cart[key] = {
                        'quantity': 1,  # Rentals always have quantity of 1
                        'price': item['price'],
                        'type': 'rental',
                        'check_in': item['check_in'],
                        'check_out': item['check_out'],
                        'daily_rate': item['daily_rate'],
                        'rental_days': item['rental_days'],
                        'total_price': item['total_price'],
                    }

        logger.debug(f"Cart initialized with contents: {self.cart}")

    def add(self,
            item,
            quantity=1,
            update_quantity=False,
            item_type='product',
            dates=None):
        """
        Add an item to the cart or update its quantity.
        - item: The product or crashpad instance to add
        - quantity: Number of items to add
        - update_quantity: If True, set the quantity instead of incrementing
        - item_type: 'product' or 'rental'
        - dates: Dictionary containing check_in and check_out dates for rentals
        """
        try:
            item_id = str(item.id)
            key = f"{item_type}_{item_id}"

            # Add validation for rental quantity
            if item_type == 'rental' and quantity != 1:
                logger.warning(
                    "Attempted to add rental item with quantity != 1")
                quantity = 1  # Force quantity to 1 for rentals

            logger.debug(
                f"Adding to cart - Type: {item_type}, Item: {item.name}, "
                f"Quantity: {quantity}")
            logger.debug(f"Current cart contents: {self.cart}")

            if key not in self.cart:
                logger.debug(f"New item being added to cart with key: {key}")
                self.cart[key] = {
                    "quantity": 0,
                    "type": item_type,
                }

                # Handle different pricing for products vs rentals
                if item_type == 'rental':
                    if not dates:
                        logger.error("Rental dates missing")
                        raise ValueError("Dates are required for rental items")

                    check_in = datetime.strptime(dates['check_in'], '%Y-%m-%d')
                    check_out = datetime.strptime(dates['check_out'],
                                                  '%Y-%m-%d')
                    rental_days = (check_out - check_in).days

                    logger.debug(
                        f"Rental details - Days: {rental_days}, "
                        f"Check-in: {check_in}, Check-out: {check_out}")

                    # Calculate daily rate
                    if rental_days >= 14:
                        daily_rate = item.fourteen_day_rate
                        rate_type = "14+ day rate"
                    elif rental_days >= 7:
                        daily_rate = item.seven_day_rate
                        rate_type = "7+ day rate"
                    else:
                        daily_rate = item.day_rate
                        rate_type = "daily rate"

                    logger.debug(f"Using {rate_type}: €{daily_rate}/day")

                    self.cart[key].update({
                        "price": str(daily_rate),
                        "check_in": dates['check_in'],
                        "check_out": dates['check_out'],
                        "rental_days": rental_days,
                        "daily_rate": str(daily_rate)
                    })
                else:
                    # Regular product pricing
                    self.cart[key]["price"] = str(item.price)
                    logger.debug(f"Product price: €{item.price}")

            if update_quantity:
                self.cart[key]["quantity"] = quantity
            else:
                self.cart[key]["quantity"] += quantity

            logger.debug(f"Updated cart contents: {self.cart}")
            self.save()
            return self.cart[key]["quantity"]

        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}", exc_info=True)
            raise

    def save(self):
        """Mark the session as modified to ensure it is saved."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, item, item_type='product'):
        """Remove an item from the cart."""
        try:
            key = f"{item_type}_{item.id}"
            if key in self.cart:
                del self.cart[key]
                self.save()
        except Exception as e:
            logger.error(f"Error removing item from cart: {e}")

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products/rentals.
        """
        product_ids = []
        crashpad_ids = []

        for key in self.cart.keys():
            item_type, item_id = key.split('_')
            if item_type == 'product':
                product_ids.append(item_id)
            elif item_type == 'rental':
                crashpad_ids.append(item_id)

        products = Product.objects.filter(id__in=product_ids)
        crashpads = Crashpad.objects.filter(id__in=crashpad_ids)

        # Create a copy of the cart to avoid modifying the session directly
        cart = self.cart.copy()

        # Handle products
        for product in products:
            key = f"product_{product.id}"
            item = cart[key].copy()
            item['item'] = product
            item['total_price'] = Decimal(item['price']) * item['quantity']
            yield item

        # Handle rentals
        for crashpad in crashpads:
            key = f"rental_{crashpad.id}"
            item = cart[key].copy()
            item['item'] = crashpad
            # Force quantity to 1 for rentals as a safety measure
            item['quantity'] = 1
            # For rentals, total price is just the daily rate * number of days
            rental_days = item.get('rental_days', 1)
            item['total_price'] = Decimal(item['price']) * rental_days
            yield item

    def __len__(self):
        """Return the total number of items in the bag."""
        return sum(int(item["quantity"]) for item in self.cart.values())

    def cart_total(self):
        """
        Compute the total cost of all items in the cart.
        For rentals, consider the rental duration.
        """
        total = Decimal('0.0')
        for item in self.cart.values():
            if item['type'] == 'rental':
                rental_days = item.get('rental_days', 1)
                total += (Decimal(item['price']) * int(item['quantity']) *
                          rental_days)
            else:
                total += Decimal(item['price']) * int(item['quantity'])
        return total

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
                'item_id': str(item['item'].id),
                'name': item['item'].name,
                'quantity': int(item['quantity']),
                'price': str(item['price']),
                'total_price': str(item['total_price']),
                'type': item['type'],
                'check_in': item.get('check_in'),
                'check_out': item.get('check_out'),
                'rental_days': item.get('rental_days'),
                'daily_rate': item.get('daily_rate')
            } for item in self.get_items()],
            'total':
            str(self.cart_total()),
        }

    def to_json(self):
        """
        Convert cart data to JSON format,
        with minimized/split data to fit constraints
        for a single Stripe metadata field
        """
        # Model objects should be excluded from the JSON output
        excluded_fields = ['item']

        # Initialize lists to store serialized items
        cart_items = []
        rental_items = []

        for item in self:
            # Create a new dictionary for the serialized item
            serialized_item = {}

            # Add the ID from the item object
            serialized_item['id'] = str(item['item'].id)

            # Dynamically add all other fields except excluded ones
            for key, value in item.items():
                if key not in excluded_fields and key != 'item':
                    # Convert Decimal values to strings
                    if isinstance(value, Decimal):
                        serialized_item[key] = str(value)
                    else:
                        serialized_item[key] = value

            # Add to the appropriate list based on type
            if item['type'] == 'product':
                cart_items.append(serialized_item)
            elif item['type'] == 'rental':
                rental_items.append(serialized_item)

        return {
            'cart_items': cart_items,
            'rental_items': rental_items,
        }

    def has_invalid_items(self):
        """Check if any items in cart have invalid quantities
        or availability
        Returns a tuple with a boolean and an error dictionary
        """
        for item in self:
            # Validate product stock
            if item['type'] == 'product':
                product = item['item']
                quantity = item['quantity']
                # Check if the product has enough stock
                if not product.has_stock(quantity):
                    error = {
                        'error': 'insufficient_stock',
                        'product': product,
                        'requested': quantity
                    }
                    logger.error(
                        f"Insufficient stock for product {product.id}")
                    return (True, error)
            # Validate rental items
            elif item['type'] == 'rental':
                crashpad = item['item']
                check_in = datetime.strptime(item['check_in'],
                                             '%Y-%m-%d').date()
                check_out = datetime.strptime(item['check_out'],
                                              '%Y-%m-%d').date()

                # Check if the dates are still available
                if not crashpad.is_available(check_in, check_out):
                    error = {
                        'error': 'dates_unavailable',
                        'crashpad': crashpad,
                        'dates': f"{check_in} to {check_out}"
                    }
                    logger.error("Selected dates are no longer available for"
                                 f" crashpad id {crashpad.id}")
                    return (True, error)
                # Check if dates are in the past
                if check_in < datetime.now().date():
                    error = {
                        'error': 'dates_in_past',
                        'crashpad': crashpad,
                        'dates': f"{check_in} to {check_out}"
                    }
                    logger.error(
                        f"Selected dates are in the past for {crashpad.id}")
                    return (True, error)
        return (False, None)

    def validate_stock(self):
        """Return list of items with stock or availability issues"""
        invalid_items = []
        for item in self:
            if item['type'] == 'product':
                product = item['item']
                if not product.has_stock(item['quantity']):
                    invalid_items.append({
                        'name':
                        product.name,
                        'type':
                        'product',
                        'requested':
                        item['quantity'],
                        'available':
                        product.stock,
                        'error':
                        f'Only {product.stock} units available'
                    })
            elif item['type'] == 'rental':
                crashpad = item['item']
                check_in = datetime.strptime(item['check_in'],
                                             '%Y-%m-%d').date()
                check_out = datetime.strptime(item['check_out'],
                                              '%Y-%m-%d').date()

                if check_in < datetime.now().date():
                    invalid_items.append({
                        'name':
                        crashpad.name,
                        'type':
                        'rental',
                        'dates':
                        f'{check_in} to {check_out}',
                        'error':
                        'Selected dates are in the past'
                    })
                elif not crashpad.is_available(check_in, check_out):
                    invalid_items.append({
                        'name':
                        crashpad.name,
                        'type':
                        'rental',
                        'dates':
                        f'{check_in} to {check_out}',
                        'error':
                        'Selected dates are no longer available'
                    })
        return invalid_items

    def has_rentals(self):
        """Check if the cart has any rental items."""
        return any(item['type'] == 'rental' for item in self)

    def has_products(self):
        """Check if the cart has any product items."""
        return any(item['type'] == 'product' for item in self)

    def has_mixed_items(self):
        """Check if the cart has both rental and product items."""
        return self.has_rentals() and self.has_products()
