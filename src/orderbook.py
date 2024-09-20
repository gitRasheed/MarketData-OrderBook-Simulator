from sortedcontainers import SortedDict
from collections import deque
from decimal import Decimal
import threading
import queue
from .order import Order
from .level_data import LevelData
from .exceptions import InvalidOrderException, InsufficientLiquidityException, OrderNotFoundException

class Orderbook:
    def __init__(self):
        self.bids = SortedDict()
        self.asks = SortedDict()
        self.orders = {}
        self.level_data = {}
        self.lock = threading.Lock()
        self.order_queue = queue.Queue()
        self.processing_thread = None
        self.stop_processing_flag = False

    def start_processing(self):
        self.stop_processing_flag = False
        self.processing_thread = threading.Thread(target=self._process_orders)
        self.processing_thread.start()

    def stop_processing(self):
        self.stop_processing_flag = True
        if self.processing_thread:
            self.processing_thread.join()

    def _process_orders(self):
        while not self.stop_processing_flag:
            try:
                order = self.order_queue.get(timeout=1)
                self.add_order(order)
            except queue.Empty:
                continue

    def add_order(self, order):
        with self.lock:
            if order.type == "market":
                return self.process_market_order(order)
            elif order.type == "limit":
                return self.add_limit_order(order)
            else:
                raise InvalidOrderException("Invalid order type")

    def add_limit_order(self, order):
        book = self.bids if order.side == "buy" else self.asks
        if order.price not in book:
            book[order.price] = deque()
            self.level_data[order.price] = LevelData()
        book[order.price].append(order)
        self.level_data[order.price].add_order(order)
        self.orders[order.id] = order
        return order.id

    def cancel_order(self, order_id):
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
            order = self.orders[order_id]
            book = self.bids if order.side == "buy" else self.asks
            book[order.price].remove(order)
            self.level_data[order.price].remove_order(order)
            if not book[order.price]:
                del book[order.price]
                del self.level_data[order.price]
            del self.orders[order_id]

    def modify_order(self, order_id, new_price, new_quantity):
        with self.lock:
            if order_id not in self.orders:
                raise OrderNotFoundException("Order not found")
            
            order = self.orders[order_id]
            old_price = order.price
            old_quantity = order.quantity
            
            book = self.bids if order.side == "buy" else self.asks
            book[old_price].remove(order)
            self.level_data[old_price].remove_order(order)
            
            if not book[old_price]:
                del book[old_price]
                del self.level_data[old_price]
            
            new_price = Decimal(str(new_price))
            new_quantity = Decimal(str(new_quantity))
            
            order.price = new_price
            order.quantity = new_quantity
            
            if new_price not in book:
                book[new_price] = deque()
                self.level_data[new_price] = LevelData()
            
            book[new_price].append(order)
            self.level_data[new_price].add_order(order)
            
            return order_id

    def get_best_bid_ask(self):
        best_bid = max(self.bids.keys()) if self.bids else None
        best_ask = min(self.asks.keys()) if self.asks else None
        return best_bid, best_ask

    def process_market_order(self, order):
        opposing_book = self.asks if order.side == "buy" else self.bids
        remaining_quantity = order.quantity
        filled_orders = []

        while remaining_quantity > 0 and opposing_book:
            best_price = min(opposing_book.keys()) if order.side == "buy" else max(opposing_book.keys())
            level_orders = opposing_book[best_price]
            level_data = self.level_data[best_price]

            while level_orders and remaining_quantity > 0:
                matched_order = level_orders[0]
                filled_quantity = min(remaining_quantity, matched_order.quantity)
                matched_order.quantity -= filled_quantity
                remaining_quantity -= filled_quantity
                level_data.update_quantity(matched_order.quantity + filled_quantity, matched_order.quantity)

                filled_orders.append((matched_order.id, filled_quantity, best_price))

                if matched_order.quantity == 0:
                    level_orders.popleft()
                    level_data.remove_order(matched_order)
                    del self.orders[matched_order.id]

            if not level_orders:
                del opposing_book[best_price]
                del self.level_data[best_price]

        if remaining_quantity > 0:
            raise InsufficientLiquidityException("Not enough liquidity to fill market order")

        return filled_orders

    def get_order_book_snapshot(self, levels):
        with self.lock:
            bids = [(price, self.level_data[price].quantity) for price in list(reversed(self.bids.keys()))[:levels]]
            asks = [(price, self.level_data[price].quantity) for price in list(self.asks.keys())[:levels]]
            return {"bids": bids, "asks": asks}