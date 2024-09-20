from decimal import Decimal
import time

class Order:
    def __init__(self, id, type, side, price, quantity):
        self.id = id
        self.type = type
        self.side = side
        self.price = Decimal(str(price))
        self.quantity = Decimal(str(quantity))
        self.timestamp = time.time()
        self.filled_quantity = Decimal('0')

    def update_quantity(self, new_quantity):
        self.quantity = Decimal(str(new_quantity))

    def is_filled(self):
        return self.filled_quantity == self.quantity