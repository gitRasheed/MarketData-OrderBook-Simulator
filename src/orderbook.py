from decimal import Decimal
import threading
from typing import Dict, List, Tuple, Optional
from .order import Order
from .price_level import PriceLevel
from .ticker import Ticker
from .exceptions import InvalidOrderException, InsufficientLiquidityException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

class Orderbook:
    def __init__(self, ticker: Ticker, initial_min_price: Decimal, initial_max_price: Decimal):
        self.ticker: Ticker = ticker
        self.tick_size: Decimal = ticker.tick_size
        self.min_price: Decimal = initial_min_price
        self.max_price: Decimal = initial_max_price
        self.price_range: int = int((self.max_price - self.min_price) / self.tick_size) + 1
        self.bid_levels: List[Optional[PriceLevel]] = [None] * self.price_range
        self.ask_levels: List[Optional[PriceLevel]] = [None] * self.price_range
        self.orders: Dict[int, Order] = {}
        self.best_bid_index: Optional[int] = None
        self.best_ask_index: Optional[int] = None
        self.lock: threading.Lock = threading.Lock()

    def _price_to_index(self, price: Decimal) -> int:
        return int((price - self.min_price) / self.tick_size)

    def _index_to_price(self, index: int) -> Decimal:
        return self.min_price + Decimal(index) * self.tick_size

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

        if order.price < self.min_price or order.price > self.max_price:
            raise InvalidOrderException(f"Price {order.price} is outside the current range [{self.min_price}, {self.max_price}]")

        index = self._price_to_index(order.price)
        levels = self.bid_levels if order.side == "buy" else self.ask_levels

        if levels[index] is None:
            levels[index] = PriceLevel(order.price)
        levels[index].add_order(order)
        self.orders[order.id] = order

        if order.side == "buy":
            if self.best_bid_index is None or index > self.best_bid_index:
                self.best_bid_index = index
        else:
            if self.best_ask_index is None or index < self.best_ask_index:
                self.best_ask_index = index

        return order.id

    def cancel_order(self, order_id: int) -> None:
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
            order = self.orders[order_id]
            index = self._price_to_index(order.price)
            levels = self.bid_levels if order.side == "buy" else self.ask_levels
            level = levels[index]
            if level:
                level.remove_order(order)
                if level.order_count == 0:
                    levels[index] = None
                    self._update_best_prices(order.side)
            del self.orders[order_id]

    def modify_order(self, order_id: int, new_price: str, new_quantity: str) -> int:
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
    
            new_price = Decimal(str(new_price))
            new_quantity = Decimal(str(new_quantity))
    
            if not self.ticker.is_valid_price(new_price):
                raise InvalidTickSizeException(f"Invalid price. Must be a multiple of {self.ticker.tick_size}")
    
            if new_price < self.min_price or new_price > self.max_price:
                raise InvalidOrderException(f"New price {new_price} is outside the current range [{self.min_price}, {self.max_price}]")
    
            if new_quantity <= 0:
                raise InvalidQuantityException("Order quantity must be positive")
    
            order = self.orders[order_id]
            old_price = order.price
            old_quantity = order.quantity
    
            old_index = self._price_to_index(old_price)
            new_index = self._price_to_index(new_price)
    
            levels = self.bid_levels if order.side == "buy" else self.ask_levels
    
            levels[old_index].remove_order(order)
            if levels[old_index].order_count == 0:
                levels[old_index] = None
    
            order.price = new_price
            order.quantity = new_quantity
    
            if levels[new_index] is None:
                levels[new_index] = PriceLevel(new_price)
            levels[new_index].add_order(order)
    
            self._update_best_prices(order.side)
    
            return order_id

    def _update_best_prices(self, side: str) -> None:
        levels = self.bid_levels if side == "buy" else self.ask_levels
        if side == "buy":
            self.best_bid_index = next((i for i in range(len(levels)-1, -1, -1) if levels[i] is not None), None)
        else:
            self.best_ask_index = next((i for i in range(len(levels)) if levels[i] is not None), None)

    @property
    def best_bid_ask(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        best_bid = self._index_to_price(self.best_bid_index) if self.best_bid_index is not None else None
        best_ask = self._index_to_price(self.best_ask_index) if self.best_ask_index is not None else None
        return best_bid, best_ask

    def process_market_order(self, order: Order) -> List[Tuple[int, Decimal, Decimal]]:
        opposing_levels = self.ask_levels if order.side == "buy" else self.bid_levels
        remaining_quantity = order.quantity
        filled_orders: List[Tuple[int, Decimal, Decimal]] = []
    
        start_index = self.best_ask_index if order.side == "buy" else self.best_bid_index
        end_index = len(opposing_levels) if order.side == "buy" else -1
        step = 1 if order.side == "buy" else -1
    
        for i in range(start_index, end_index, step):
            level = opposing_levels[i]
            if level is None:
                continue
    
            current_order = level.head_order
            while current_order and remaining_quantity > 0:
                filled_quantity = min(remaining_quantity, current_order.quantity)
                current_order.quantity -= filled_quantity
                remaining_quantity -= filled_quantity
                level.update_volume(current_order.quantity + filled_quantity, current_order.quantity)
    
                filled_orders.append((current_order.id, filled_quantity, level.price))
    
                if current_order.quantity == 0:
                    next_order = current_order.next_order
                    level.remove_order(current_order)
                    del self.orders[current_order.id]
                    current_order = next_order
                else:
                    current_order = current_order.next_order
    
            if level.order_count == 0:
                opposing_levels[i] = None
    
        if remaining_quantity > 0:
            raise InsufficientLiquidityException("Not enough liquidity to fill market order")
    
        self._update_best_prices("sell" if order.side == "buy" else "buy")
        return filled_orders

    def get_order_book_snapshot(self, levels: int) -> Dict[str, List[Tuple[Decimal, Decimal]]]:
        with self.lock:
            bids = self._get_snapshot_for_side("buy", levels)
            asks = self._get_snapshot_for_side("sell", levels)
            return {"bids": bids, "asks": asks}

    def _get_snapshot_for_side(self, side: str, levels: int) -> List[Tuple[Decimal, Decimal]]:
        snapshot = []
        price_levels = self.bid_levels if side == "buy" else self.ask_levels
        start_index = self.best_bid_index if side == "buy" else self.best_ask_index
        end_index = -1 if side == "buy" else len(price_levels)
        step = -1 if side == "buy" else 1
    
        for i in range(start_index, end_index, step):
            if len(snapshot) >= levels:
                break
            level = price_levels[i]
            if level:
                snapshot.append((level.price, level.total_volume))
    
        return snapshot