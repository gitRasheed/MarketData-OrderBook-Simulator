from decimal import Decimal
from .order import Order

class Limit:
    def __init__(self, price):
        self.price = Decimal(str(price))
        self.total_volume = Decimal('0')
        self.order_count = 0
        self.head_order = None
        self.tail_order = None
        self.parent = None
        self.left_child = None
        self.right_child = None

    def add_order(self, order: Order):
        self.total_volume += order.quantity
        self.order_count += 1
        if not self.head_order:
            self.head_order = self.tail_order = order
        else:
            self.tail_order.next_order = order
            order.prev_order = self.tail_order
            self.tail_order = order
        order.parent_limit = self

    def remove_order(self, order: Order):
        self.total_volume -= order.quantity
        self.order_count -= 1
        if order.prev_order:
            order.prev_order.next_order = order.next_order
        else:
            self.head_order = order.next_order
        if order.next_order:
            order.next_order.prev_order = order.prev_order
        else:
            self.tail_order = order.prev_order
        order.parent_limit = None
        order.prev_order = None
        order.next_order = None

    def update_volume(self, old_quantity: Decimal, new_quantity: Decimal):
        self.total_volume -= old_quantity
        self.total_volume += new_quantity