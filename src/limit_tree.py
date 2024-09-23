from decimal import Decimal
from .limit import Limit

class LimitTree:
    def __init__(self):
        self.root = None
        self.lowest_limit = None
        self.highest_limit = None

    def insert(self, limit: Limit):
        if not self.root:
            self.root = limit
            self.lowest_limit = self.highest_limit = limit
            return

        current = self.root
        while True:
            if limit.price < current.price:
                if current.left_child is None:
                    current.left_child = limit
                    limit.parent = current
                    break
                current = current.left_child
            else:
                if current.right_child is None:
                    current.right_child = limit
                    limit.parent = current
                    break
                current = current.right_child

        if limit.price < self.lowest_limit.price:
            self.lowest_limit = limit
        if limit.price > self.highest_limit.price:
            self.highest_limit = limit

    def delete(self, price):
        limit = self.find(price)
        if not limit:
            return

        if limit.left_child is None and limit.right_child is None:
            self._delete_leaf(limit)
        elif limit.left_child is None or limit.right_child is None:
            self._delete_single_child(limit)
        else:
            self._delete_two_children(limit)

        if self.root:
            if price == self.lowest_limit.price:
                self.lowest_limit = self._find_min(self.root)
            if price == self.highest_limit.price:
                self.highest_limit = self._find_max(self.root)
        else:
            self.lowest_limit = None
            self.highest_limit = None

    def find(self, price: Decimal) -> Limit:
        current = self.root
        while current:
            if price == current.price:
                return current
            elif price < current.price:
                current = current.left_child
            else:
                current = current.right_child
        return None

    def min(self) -> Limit:
        return self.lowest_limit

    def max(self) -> Limit:
        return self.highest_limit

    def _delete_leaf(self, limit: Limit):
        if limit.parent:
            if limit.parent.left_child == limit:
                limit.parent.left_child = None
            else:
                limit.parent.right_child = None
        else:
            self.root = None

    def _delete_single_child(self, limit: Limit):
        child = limit.left_child if limit.left_child else limit.right_child
        if limit.parent:
            if limit.parent.left_child == limit:
                limit.parent.left_child = child
            else:
                limit.parent.right_child = child
            child.parent = limit.parent
        else:
            self.root = child
            child.parent = None

    def _delete_two_children(self, limit: Limit):
        successor = self._find_min(limit.right_child)
        self.delete(successor.price)
        limit.price = successor.price
        limit.total_volume = successor.total_volume
        limit.order_count = successor.order_count
        limit.head_order = successor.head_order
        limit.tail_order = successor.tail_order

    def _find_min(self, node: Limit) -> Limit:
        if node is None:
            return None
        current = node
        while current.left_child:
            current = current.left_child
        return current
    def _find_max(self, node: Limit) -> Limit:
        if node is None:
            return None
        current = node
        while current.right_child:
            current = current.right_child
        return current