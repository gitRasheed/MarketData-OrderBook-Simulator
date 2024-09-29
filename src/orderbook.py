from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from .order import Order
from .price_level import PriceLevel, PriceLevelTree
from .ticker import Ticker
from .exceptions import InvalidOrderException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

class Orderbook:
    def __init__(self, ticker: Ticker):
        self.ticker: Ticker = ticker
        self.bids: PriceLevelTree = PriceLevelTree()
        self.asks: PriceLevelTree = PriceLevelTree()
        self.orders: Dict[int, Order] = {}

    def add_order(self, order: Order) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        if order.quantity <= 0:
            raise InvalidQuantityException("Order quantity must be positive")

        if order.type == "market":
            order_id, filled_orders = self._process_market_order(order)
            total_filled = sum(fill[1] for fill in filled_orders)
            if total_filled < order.quantity:
                print(f"Market order partially filled. Filled: {total_filled}, Canceled: {order.quantity - total_filled}")
            return order_id, filled_orders
        elif order.type == "limit":
            return self._process_limit_order(order)
        else:
            raise InvalidOrderException("Invalid order type")

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise OrderNotFoundException("Order not found")
        order = self.orders[order_id]
        self._remove_order(order)

    def modify_order(self, order_id: int, new_quantity: int) -> int:
        if order_id not in self.orders:
            raise OrderNotFoundException("Order not found")

        new_quantity = int(new_quantity)
        if new_quantity <= 0:
            raise InvalidQuantityException("Order quantity must be positive")

        order = self.orders[order_id]
        old_quantity = order.quantity

        if new_quantity < old_quantity:
            self._decrease_order_quantity(order, new_quantity)
        elif new_quantity > old_quantity:
            self._increase_order_quantity(order, new_quantity)

        return order_id

    def get_order_book_snapshot(self, levels: int) -> Dict[str, List[Tuple[Decimal, int]]]:
        bids = self._get_snapshot_for_tree(self.bids, levels, reverse=True)
        asks = self._get_snapshot_for_tree(self.asks, levels, reverse=False)
        return {"bids": bids, "asks": asks}

    def _process_limit_order(self, order: Order) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        if not self.ticker.is_valid_price(order.price):
            raise InvalidTickSizeException(f"Invalid price. Must be a multiple of {self.ticker.tick_size}")

        filled_orders = []
        remaining_quantity = order.quantity

        opposing_tree = self.asks if order.side == "buy" else self.bids
        best_opposing_price = opposing_tree.min().price if opposing_tree.root else None

        while remaining_quantity > 0 and best_opposing_price and \
              ((order.side == "buy" and order.price >= best_opposing_price) or \
               (order.side == "sell" and order.price <= best_opposing_price)):
            best_level = opposing_tree.min() if order.side == "buy" else opposing_tree.max()
            filled_quantity, level_orders = self._match_orders_at_level(best_level, remaining_quantity)
            remaining_quantity -= filled_quantity
            filled_orders.extend(level_orders)

            if best_level.order_count == 0:
                opposing_tree.delete(best_level.price)
                best_opposing_price = opposing_tree.min().price if opposing_tree.root else None

        if remaining_quantity > 0:
            tree = self.bids if order.side == "buy" else self.asks
            level = tree.find(order.price)
            if not level:
                level = PriceLevel(order.price)
                tree.insert(level)
            order.quantity = remaining_quantity
            level.add_order(order)
            self.orders[order.id] = order

        return order.id, filled_orders

    def _process_market_order(self, order: Order) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        opposing_tree = self.asks if order.side == "buy" else self.bids
        remaining_quantity = order.quantity
        filled_orders = []

        while remaining_quantity > 0 and opposing_tree.root:
            best_level = opposing_tree.min() if order.side == "buy" else opposing_tree.max()
            if not best_level:
                break
            
            filled_quantity, level_orders = self._match_orders_at_level(best_level, remaining_quantity)
            remaining_quantity -= filled_quantity
            filled_orders.extend(level_orders)

            if best_level.order_count == 0:
                opposing_tree.delete(best_level.price)

        if remaining_quantity > 0:
            print(f"Market order partially filled. Remaining quantity: {remaining_quantity}")
        else:
            print(f"Market order fully filled")

        return order.id, filled_orders

    def _match_orders_at_level(self, level: PriceLevel, quantity: int) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        filled_quantity = 0
        filled_orders = []
        current_order = level.head_order

        while current_order and filled_quantity < quantity:
            order_fill = min(quantity - filled_quantity, current_order.quantity)
            current_order.quantity -= order_fill
            filled_quantity += order_fill
            level.update_volume(current_order.quantity + order_fill, current_order.quantity)

            filled_orders.append((current_order.id, order_fill, level.price))

            if current_order.quantity == 0:
                next_order = current_order.next_order
                level.remove_order(current_order)
                if current_order.id in self.orders:
                    del self.orders[current_order.id]
                else:
                    print(f"Warning: Order {current_order.id} not found in self.orders")
                current_order = next_order
            else:
                current_order = current_order.next_order

        return filled_quantity, filled_orders

    def _remove_order(self, order: Order) -> None:
        tree = self.bids if order.side == "buy" else self.asks
        level = tree.find(order.price)
        if level:
            level.remove_order(order)
            if level.order_count == 0:
                tree.delete(order.price)
        del self.orders[order.id]

    def _decrease_order_quantity(self, order: Order, new_quantity: int) -> None:
        level = order.parent_level
        level.update_volume(order.quantity, new_quantity)
        order.quantity = new_quantity

    def _increase_order_quantity(self, order: Order, new_quantity: int) -> None:
        self._remove_order(order)
        order.quantity = new_quantity
        self._process_limit_order(order)

    def _get_snapshot_for_tree(self, tree: PriceLevelTree, levels: int, reverse: bool) -> List[Tuple[Decimal, int]]:
        snapshot = []
        current = tree.max() if reverse else tree.min()
        while current and len(snapshot) < levels:
            snapshot.append((current.price, current.total_volume))
            if reverse:
                current = self._get_previous_level(current)
            else:
                current = self._get_next_level(current)
        return snapshot

    def _get_next_level(self, level: PriceLevel) -> Optional[PriceLevel]:
        if level.right_child:
            return self._find_min(level.right_child)
        while level.parent and level.parent.right_child == level:
            level = level.parent
        return level.parent

    def _get_previous_level(self, level: PriceLevel) -> Optional[PriceLevel]:
        if level.left_child:
            return self._find_max(level.left_child)
        while level.parent and level.parent.left_child == level:
            level = level.parent
        return level.parent

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

    @property
    def best_bid_ask(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        best_bid = self.bids.max().price if self.bids.root else None
        best_ask = self.asks.min().price if self.asks.root else None
        return best_bid, best_ask