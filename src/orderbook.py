from decimal import Decimal
import threading
from typing import Dict, List, Tuple, Optional
from .order import Order
from .limit import Limit
from .limit_tree import LimitTree
from .ticker import Ticker
from .exceptions import InvalidOrderException, InsufficientLiquidityException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

class Orderbook:
    def __init__(self, ticker: Ticker):
        self.ticker: Ticker = ticker
        self.bids: LimitTree = LimitTree()
        self.asks: LimitTree = LimitTree()
        self.orders: Dict[int, Order] = {}
        self.lock: threading.Lock = threading.Lock()

    def add_order(self, order: Order) -> int:
        with self.lock:
            if order.quantity <= 0:
                raise InvalidQuantityException("Order quantity must be positive")
            if order.type == "market":
                return self.process_market_order(order)
            elif order.type == "limit":
                return self.add_limit_order(order)
            else:
                raise InvalidOrderException("Invalid order type")

    def add_limit_order(self, order: Order) -> int:
        if not self.ticker.is_valid_price(order.price):
            raise InvalidTickSizeException(f"Invalid price. Must be a multiple of {self.ticker.tick_size}")

        tree = self.bids if order.side == "buy" else self.asks
        limit = tree.find(order.price)
        if not limit:
            limit = Limit(order.price)
            tree.insert(limit)
        limit.add_order(order)
        self.orders[order.id] = order
        return order.id

    def cancel_order(self, order_id: int) -> None:
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
            order = self.orders[order_id]
            tree = self.bids if order.side == "buy" else self.asks
            limit = tree.find(order.price)
            if limit:
                limit.remove_order(order)
                if limit.order_count == 0:
                    tree.delete(order.price)
            del self.orders[order_id]

    def modify_order(self, order_id: int, new_price: Decimal, new_quantity: Decimal) -> int:
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")

            if not self.ticker.is_valid_price(new_price):
                raise InvalidTickSizeException(f"Invalid price. Must be a multiple of {self.ticker.tick_size}")

            new_quantity = Decimal(str(new_quantity))
            if new_quantity <= 0:
                raise InvalidQuantityException("Order quantity must be positive")

            order = self.orders[order_id]
            old_price = order.price
            old_quantity = order.quantity

            tree = self.bids if order.side == "buy" else self.asks
            old_limit = tree.find(old_price)
            old_limit.remove_order(order)

            if old_limit.order_count == 0:
                tree.delete(old_price)

            new_price = Decimal(str(new_price))
            order.price = new_price
            order.quantity = new_quantity

            new_limit = tree.find(new_price)
            if not new_limit:
                new_limit = Limit(new_price)
                tree.insert(new_limit)
            new_limit.add_order(order)

            return order_id

    @property
    def best_bid_ask(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        best_bid = self.bids.max().price if self.bids.root else None
        best_ask = self.asks.min().price if self.asks.root else None
        return best_bid, best_ask

    def process_market_order(self, order: Order) -> List[Tuple[int, Decimal, Decimal]]:
        opposing_tree = self.asks if order.side == "buy" else self.bids
        remaining_quantity = order.quantity
        filled_orders: List[Tuple[int, Decimal, Decimal]] = []
    
        while remaining_quantity > 0 and opposing_tree.root:
            best_limit = opposing_tree.min() if order.side == "buy" else opposing_tree.max()
            if not best_limit:
                break
            current_order = best_limit.head_order
    
            while current_order and remaining_quantity > 0:
                filled_quantity = min(remaining_quantity, current_order.quantity)
                current_order.quantity -= filled_quantity
                remaining_quantity -= filled_quantity
                best_limit.update_volume(current_order.quantity + filled_quantity, current_order.quantity)
    
                filled_orders.append((current_order.id, filled_quantity, best_limit.price))
    
                if current_order.quantity == 0:
                    next_order = current_order.next_order
                    best_limit.remove_order(current_order)
                    del self.orders[current_order.id]
                    current_order = next_order
                else:
                    current_order = current_order.next_order
    
            if best_limit.order_count == 0:
                opposing_tree.delete(best_limit.price)
    
        if remaining_quantity > 0:
            raise InsufficientLiquidityException("Not enough liquidity to fill market order")
    
        return filled_orders

    def get_order_book_snapshot(self, levels: int) -> Dict[str, List[Tuple[Decimal, Decimal]]]:
        with self.lock:
            bids = self._get_snapshot_for_tree(self.bids, levels, reverse=True)
            asks = self._get_snapshot_for_tree(self.asks, levels, reverse=False)
            return {"bids": bids, "asks": asks}

    def _get_snapshot_for_tree(self, tree: LimitTree, levels: int, reverse: bool) -> List[Tuple[Decimal, Decimal]]:
        snapshot = []
        current = tree.max() if reverse else tree.min()
        while current and len(snapshot) < levels:
            snapshot.append((current.price, current.total_volume))
            current = self._get_previous_limit(current) if reverse else self._get_next_limit(current)
        return snapshot

    def _get_next_limit(self, limit: Limit) -> Optional[Limit]:
        if limit.right_child:
            return self._find_min(limit.right_child)
        while limit.parent and limit.parent.right_child == limit:
            limit = limit.parent
        return limit.parent

    def _get_previous_limit(self, limit: Limit) -> Optional[Limit]:
        if limit.left_child:
            return self._find_max(limit.left_child)
        while limit.parent and limit.parent.left_child == limit:
            limit = limit.parent
        return limit.parent

    def _find_min(self, node: Limit) -> Limit:
        current = node
        while current.left_child:
            current = current.left_child
        return current

    def _find_max(self, node: Limit) -> Limit:
        current = node
        while current.right_child:
            current = current.right_child
        return current