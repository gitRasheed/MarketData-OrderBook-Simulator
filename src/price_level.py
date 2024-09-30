from typing import Optional
from decimal import Decimal
from .order import Order

class PriceLevel:
    def __init__(self, price: Decimal):
        self._price = Decimal(str(price))
        self._total_volume = 0
        self._order_count = 0
        self._head_order: Optional[Order] = None
        self._tail_order: Optional[Order] = None
        self.parent: Optional['PriceLevel'] = None
        self.left_child: Optional['PriceLevel'] = None
        self.right_child: Optional['PriceLevel'] = None

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def total_volume(self) -> int:
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
        self.update_volume(0, order.quantity)
        self._order_count += 1
        if not self._head_order:
            self._head_order = self._tail_order = order
        else:
            self._tail_order.next_order = order
            order.prev_order = self._tail_order
            self._tail_order = order
        order.parent_level = self

    def remove_order(self, order: Order) -> None:
        self.update_volume(order.quantity, 0)
        self._order_count -= 1
        if order.prev_order:
            order.prev_order.next_order = order.next_order
        else:
            self._head_order = order.next_order
        if order.next_order:
            order.next_order.prev_order = order.prev_order
        else:
            self._tail_order = order.prev_order
        order.parent_level = None
        order.prev_order = None
        order.next_order = None

    def update_volume(self, old_quantity: int, new_quantity: int) -> None:
        self._total_volume += new_quantity - old_quantity

class PriceLevelTree:
    def __init__(self):
        self.root: Optional[PriceLevel] = None
        self._lowest_level: Optional[PriceLevel] = None
        self._highest_level: Optional[PriceLevel] = None

    @property
    def lowest_level(self) -> Optional[PriceLevel]:
        return self._lowest_level

    @property
    def highest_level(self) -> Optional[PriceLevel]:
        return self._highest_level

    def insert(self, level: PriceLevel) -> None:
        if not self.root:
            self.root = level
            self._lowest_level = self._highest_level = level
            return

        current = self.root
        while True:
            if level.price < current.price:
                if current.left_child is None:
                    current.left_child = level
                    level.parent = current
                    break
                current = current.left_child
            else:
                if current.right_child is None:
                    current.right_child = level
                    level.parent = current
                    break
                current = current.right_child

        if level.price < self._lowest_level.price:
            self._lowest_level = level
        if level.price > self._highest_level.price:
            self._highest_level = level

    def delete(self, price: Decimal) -> None:
        level = self.find(price)
        if not level:
            return

        if level.left_child is None and level.right_child is None:
            self._delete_leaf(level)
        elif level.left_child is None or level.right_child is None:
            self._delete_single_child(level)
        else:
            self._delete_two_children(level)

        if self.root:
            if price == self._lowest_level.price:
                self._lowest_level = self._find_min(self.root)
            if price == self._highest_level.price:
                self._highest_level = self._find_max(self.root)
        else:
            self._lowest_level = self._highest_level = None

    def find(self, price: Decimal) -> Optional[PriceLevel]:
        current = self.root
        while current:
            if price == current.price:
                return current
            elif price < current.price:
                current = current.left_child
            else:
                current = current.right_child
        return None

    def min(self) -> Optional[PriceLevel]:
        return self._lowest_level

    def max(self) -> Optional[PriceLevel]:
        return self._highest_level

    def _delete_leaf(self, level: PriceLevel) -> None:
        if level.parent:
            if level.parent.left_child == level:
                level.parent.left_child = None
            else:
                level.parent.right_child = None
        else:
            self.root = None

    def _delete_single_child(self, level: PriceLevel) -> None:
        child = level.left_child if level.left_child else level.right_child
        if level.parent:
            if level.parent.left_child == level:
                level.parent.left_child = child
            else:
                level.parent.right_child = child
            child.parent = level.parent
        else:
            self.root = child
            child.parent = None

    def _delete_two_children(self, level: PriceLevel) -> None:
        successor = self._find_min(level.right_child)
        self.delete(successor.price)
        level._price = successor.price
        level.update_volume(level.total_volume, successor.total_volume)
        level._order_count = successor.order_count
        level._head_order = successor.head_order
        level._tail_order = successor.tail_order

    def _find_min(self, node: PriceLevel) -> PriceLevel:
        current = node
        while current.left_child:
            current = current.left_child
        return current

    def _find_max(self, node: PriceLevel) -> PriceLevel:
        current = node
        while current.right_child:
            current = current.right_child
        return current