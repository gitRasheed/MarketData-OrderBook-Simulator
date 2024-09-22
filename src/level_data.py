from decimal import Decimal

class LevelData:
    def __init__(self, price):
        self.price = Decimal(str(price))
        self.quantity = Decimal('0')
        self.count = 0
        self.head_order = None
        self.tail_order = None

    def add_order(self, order):
        self.quantity += order.quantity
        self.count += 1
        if not self.head_order:
            self.head_order = self.tail_order = order
        else:
            self.tail_order.next_order = order
            order.prev_order = self.tail_order
            self.tail_order = order
        order.parent_level = self

    def remove_order(self, order):
        self.quantity -= order.quantity
        self.count -= 1
        if order.prev_order:
            order.prev_order.next_order = order.next_order
        else:
            self.head_order = order.next_order
        if order.next_order:
            order.next_order.prev_order = order.prev_order
        else:
            self.tail_order = order.prev_order
        order.parent_level = None
        order.prev_order = None
        order.next_order = None

    def update_quantity(self, old_quantity, new_quantity):
        self.quantity -= old_quantity
        self.quantity += new_quantity