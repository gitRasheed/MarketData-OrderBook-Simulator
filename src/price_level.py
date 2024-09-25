from decimal import Decimal
from typing import Optional
from .order import Order

class PriceLevel:
    def __init__(self, price: Decimal):
        self._price = Decimal(str(price))
        self._total_volume = Decimal('0')
        self._order_count = 0
        self._head_order: Optional[Order] = None
        self._tail_order: Optional[Order] = None

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def total_volume(self) -> Decimal:
        return self._total_volume

    @property
    def order_count(self) -> int:
        return self._order_count

    @property
    def head_order(self) -> Optional[Order]:
        return self._head_order

    @property
    def tail_order(self) -> Optional[Order]:
        return self._tail_order

    def add_order(self, order: Order) -> None:
        self._total_volume += order.quantity
        self._order_count += 1
        if not self._head_order:
            self._head_order = self._tail_order = order
        else:
            self._tail_order.next_order = order
            order.prev_order = self._tail_order
            self._tail_order = order
        order.parent_limit = self

    def remove_order(self, order: Order) -> None:
        self._total_volume -= order.quantity
        self._order_count -= 1
        if order.prev_order:
            order.prev_order.next_order = order.next_order
        else:
            self._head_order = order.next_order
        if order.next_order:
            order.next_order.prev_order = order.prev_order
        else:
            self._tail_order = order.prev_order
        order.parent_limit = None
        order.prev_order = None
        order.next_order = None

    def update_volume(self, old_quantity: Decimal, new_quantity: Decimal) -> None:
        self._total_volume += new_quantity - old_quantity