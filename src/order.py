from decimal import Decimal
import time

class Order:
    def __init__(self, id, type, side, price, quantity, symbol):
        self.id = id
        self.type = type
        self.side = side
        self.price = Decimal(str(price)) if price is not None else None
        self.quantity = int(quantity)
        self.symbol = symbol
        self.timestamp = time.time()
        self.filled_quantity = 0
        self.next_order = None
        self.prev_order = None
        self.parent_level = None

    def update_quantity(self, new_quantity):
        self.quantity = int(new_quantity)

    def is_filled(self):
        return self.filled_quantity == self.quantity

    def to_good_till_cancel(self, price):
        if self.type != "market":
            raise ValueError("Only market orders can be converted to good till cancel")
        self.type = "limit"
        self.price = Decimal(str(price))