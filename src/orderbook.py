from bintrees import RBTree
from decimal import Decimal
import threading
import queue
from typing import Dict, List, Tuple, Optional
from .order import Order
from .level_data import LevelData
from .ticker import Ticker
from .exceptions import InvalidOrderException, InsufficientLiquidityException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

class Orderbook:
    def __init__(self, ticker: Ticker):
        self.ticker: Ticker = ticker
        self.bids: RBTree = RBTree()
        self.asks: RBTree = RBTree()
        self.orders: Dict[int, Order] = {}
        self.lock: threading.Lock = threading.Lock()
        self.order_queue: queue.Queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_processing_flag: bool = False

    def start_processing(self) -> None:
        self.stop_processing_flag = False
        self.processing_thread = threading.Thread(target=self._process_orders)
        self.processing_thread.start()

    def stop_processing(self) -> None:
        self.stop_processing_flag = True
        if self.processing_thread:
            self.processing_thread.join()

    def _process_orders(self) -> None:
        while not self.stop_processing_flag:
            try:
                order: Order = self.order_queue.get(timeout=1)
                self.add_order(order)
            except queue.Empty:
                continue

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

        book = self.bids if order.side == "buy" else self.asks
        if order.price not in book:
            book[order.price] = LevelData(order.price)
        book[order.price].add_order(order)
        self.orders[order.id] = order
        return order.id

    def cancel_order(self, order_id: int) -> None:
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
            order = self.orders[order_id]
            book = self.bids if order.side == "buy" else self.asks
            level_data = book[order.price]
            level_data.remove_order(order)
            if level_data.count == 0:
                del book[order.price]
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

            book = self.bids if order.side == "buy" else self.asks
            level_data = book[old_price]
            level_data.remove_order(order)

            if level_data.count == 0:
                del book[old_price]

            new_price = Decimal(str(new_price))
            order.price = new_price
            order.quantity = new_quantity

            if new_price not in book:
                book[new_price] = LevelData(new_price)
            book[new_price].add_order(order)

            return order_id

    @property
    def best_bid_ask(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        best_bid = self.bids.max_key() if self.bids else None
        best_ask = self.asks.min_key() if self.asks else None
        return best_bid, best_ask

    def process_market_order(self, order: Order) -> List[Tuple[int, Decimal, Decimal]]:
        opposing_book = self.asks if order.side == "buy" else self.bids
        remaining_quantity = order.quantity
        filled_orders: List[Tuple[int, Decimal, Decimal]] = []

        while remaining_quantity > 0 and opposing_book:
            best_price = opposing_book.min_key() if order.side == "buy" else opposing_book.max_key()
            level_data = opposing_book[best_price]
            current_order = level_data.head_order

            while current_order and remaining_quantity > 0:
                filled_quantity = min(remaining_quantity, current_order.quantity)
                current_order.quantity -= filled_quantity
                remaining_quantity -= filled_quantity
                level_data.update_quantity(current_order.quantity + filled_quantity, current_order.quantity)

                filled_orders.append((current_order.id, filled_quantity, best_price))

                if current_order.quantity == 0:
                    next_order = current_order.next_order
                    level_data.remove_order(current_order)
                    del self.orders[current_order.id]
                    current_order = next_order
                else:
                    current_order = current_order.next_order

            if level_data.count == 0:
                del opposing_book[best_price]

        if remaining_quantity > 0:
            raise InsufficientLiquidityException("Not enough liquidity to fill market order")

        return filled_orders

    def get_order_book_snapshot(self, levels: int) -> Dict[str, List[Tuple[Decimal, Decimal]]]:
        with self.lock:
            bids = [(price, level_data.quantity) for price, level_data in self.bids.items(reverse=True)][:levels]
            asks = [(price, level_data.quantity) for price, level_data in self.asks.items()][:levels]
            return {"bids": bids, "asks": asks}