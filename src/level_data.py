from decimal import Decimal

class LevelData:
    def __init__(self):
        self.quantity = Decimal('0')
        self.count = 0

    def add_order(self, order):
        self.quantity += order.quantity
        self.count += 1

    def remove_order(self, order):
        self.quantity -= order.quantity
        self.count -= 1

    def update_quantity(self, old_quantity, new_quantity):
        self.quantity -= old_quantity
        self.quantity += new_quantity