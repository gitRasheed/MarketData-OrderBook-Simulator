from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from .order import Order
from .price_level import PriceLevel, PriceLevelTree
from .ticker import Ticker
from .exceptions import InvalidOrderException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException
from .orderbook_logger import OrderBookLogger

class Orderbook:
    def __init__(self, ticker: Ticker):
        self.ticker: Ticker = ticker
        self.bids: PriceLevelTree = PriceLevelTree()
        self.asks: PriceLevelTree = PriceLevelTree()
        self.orders: Dict[int, Order] = {}
        self.price_levels: Dict[Decimal, PriceLevel] = {}
        self.best_bid: Optional[Decimal] = None
        self.best_ask: Optional[Decimal] = None
        self.logger = OrderBookLogger(ticker.symbol)
        self.changes: List[Dict] = []
        self.version = 0

    def add_order(self, order: Order) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        if order.quantity <= 0:
            raise InvalidQuantityException("Order quantity must be positive")
    
        if order.type == "market":
            order_id, filled_orders = self._process_market_order(order)
        elif order.type == "limit":
            order_id, filled_orders = self._process_limit_order(order)
        else:
            raise InvalidOrderException("Invalid order type")
    
        self._log_change('add', order.side, order.price, order.quantity)
        return order_id, filled_orders

    def _process_market_order(self, order: Order) -> Tuple[int, List[Tuple[int, int, Decimal]]]:
        opposing_tree = self.asks if order.side == "buy" else self.bids
        if not opposing_tree.root:
            return order.id, []  # Return empty list if no opposing orders

        worst_price = opposing_tree.max().price if order.side == "buy" else opposing_tree.min().price
        order.to_good_till_cancel(worst_price)  # Convert to limit order at worst price

        return self._process_limit_order(order)  # Process as a limit order

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
                self._remove_price_level(best_level)
                best_opposing_price = opposing_tree.min().price if opposing_tree.root else None

        if remaining_quantity > 0:
            self._add_order_to_level(order, remaining_quantity)

        return order.id, filled_orders

    def _add_order_to_level(self, order: Order, quantity: int):
        tree = self.bids if order.side == "buy" else self.asks
        if order.price not in self.price_levels:
            level = PriceLevel(order.price)
            self.price_levels[order.price] = level
            tree.insert(level)
        else:
            level = self.price_levels[order.price]
        
        order.quantity = quantity
        level.add_order(order)
        self.orders[order.id] = order

        if order.side == "buy":
            if not self.best_bid or order.price > self.best_bid:
                self.best_bid = order.price
        else:
            if not self.best_ask or order.price < self.best_ask:
                self.best_ask = order.price

    def cancel_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise OrderNotFoundException("Order not found")
        order = self.orders[order_id]
        self._remove_order(order)
        self._log_change('delete', order.side, order.price, order.quantity)

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

        self._log_change('update', order.side, order.price, new_quantity)
        return order_id

    def get_order_book_snapshot(self, levels: int) -> Dict[str, List[Tuple[Decimal, int]]]:
        bids = []
        asks = []

        bid_node = self.bids.max()
        for _ in range(levels):
            if bid_node:
                bids.append((bid_node.price, bid_node.total_volume))
                bid_node = self._get_previous_level(bid_node)
            else:
                break

        ask_node = self.asks.min()
        for _ in range(levels):
            if ask_node:
                asks.append((ask_node.price, ask_node.total_volume))
                ask_node = self._get_next_level(ask_node)
            else:
                break

        return {"bids": bids, "asks": asks}

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
        level = order.parent_level
        level.remove_order(order)
        if level.order_count == 0:
            self._remove_price_level(level)
        del self.orders[order.id]

    def _remove_price_level(self, level: PriceLevel) -> None:
        tree = self.bids if level.price <= (self.best_bid or Decimal('-inf')) else self.asks
        tree.delete(level.price)
        self.price_levels.pop(level.price, None)
        if level.price == self.best_bid:
            self.best_bid = self.bids.max().price if self.bids.root else None
        elif level.price == self.best_ask:
            self.best_ask = self.asks.min().price if self.asks.root else None

    def _decrease_order_quantity(self, order: Order, new_quantity: int) -> None:
        level = order.parent_level
        level.update_volume(order.quantity, new_quantity)
        order.quantity = new_quantity

    def _increase_order_quantity(self, order: Order, new_quantity: int) -> None:
        self._remove_order(order)
        order.quantity = new_quantity
        self._add_order_to_level(order, new_quantity)

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

    def _log_change(self, action: str, side: str, price: Decimal, quantity: int):
        self.version += 1
        change = {
            'version': self.version,
            'action': action,
            'side': side,
            'price': price,
            'quantity': quantity
        }
        self.changes.append(change)
        self.logger.log_change(action, side, price, quantity)

    def get_updates_since(self, last_version: int) -> List[Dict]:
        return [change for change in self.changes if change['version'] > last_version]

    def clear_changes(self):
        self.changes.clear()

    @property
    def best_bid_ask(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        return self.best_bid, self.best_ask

    @property
    def current_version(self):
        return self.version