from typing import Dict, List, Tuple
from .orderbook import Orderbook
from .ticker import Ticker
from .order import Order
from decimal import Decimal

class OrderBookManager:
    def __init__(self):
        self.order_books: Dict[str, Orderbook] = {}
        self.subscriptions: Dict[str, List[str]] = {}
        self.last_update: Dict[str, int] = {}
        self.default_order_book_levels = 10

    def create_order_book(self, symbol: str, tick_size: Decimal):
        ticker = Ticker(symbol, tick_size)
        self.order_books[symbol] = Orderbook(ticker)
        self.last_update[symbol] = 0

    def get_order_book(self, symbol: str) -> Orderbook:
        return self.order_books.get(symbol)

    def subscribe(self, symbol: str, client_id: str):
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        self.subscriptions[symbol].append(client_id)

    def unsubscribe(self, symbol: str, client_id: str):
        if symbol in self.subscriptions:
            self.subscriptions[symbol].remove(client_id)

    def process_order(self, order: Order) -> Tuple[int, List, int]:
        order_book = self.get_order_book(order.symbol)
        if order_book:
            order_id, filled_orders = order_book.add_order(order)
            version = order_book.current_version
            return order_id, filled_orders, version
        return None, [], 0

    def get_order_book_snapshot(self, symbol: str, levels: int = None) -> Tuple[Dict, int]:
        order_book = self.get_order_book(symbol)
        if order_book:
            if levels is None:
                levels = self.default_order_book_levels
            snapshot = order_book.get_order_book_snapshot(levels)
            version = order_book.current_version
            return snapshot, version
        return None, 0

    def get_order_book_update(self, symbol: str) -> Tuple[List, int]:
        order_book = self.get_order_book(symbol)
        if order_book:
            current_version = order_book.current_version
            updates = order_book.get_updates_since(self.last_update.get(symbol, 0))
            if updates:
                self.last_update[symbol] = current_version
            return updates, current_version
        return [], self.last_update.get(symbol, 0)

    def get_subscribed_clients(self, symbol: str) -> List[str]:
        return self.subscriptions.get(symbol, [])