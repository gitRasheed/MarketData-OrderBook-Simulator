from typing import Dict, List
from .orderbook import Orderbook
from .ticker import Ticker
from .order import Order
from decimal import Decimal

class OrderBookManager:
    def __init__(self):
        self.order_books: Dict[str, Orderbook] = {}
        self.subscriptions: Dict[str, List[str]] = {}

    def create_order_book(self, symbol: str, tick_size: Decimal):
        ticker = Ticker(symbol, tick_size)
        self.order_books[symbol] = Orderbook(ticker)

    def get_order_book(self, symbol: str) -> Orderbook:
        return self.order_books.get(symbol)

    def subscribe(self, symbol: str, client_id: str):
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        self.subscriptions[symbol].append(client_id)

    def unsubscribe(self, symbol: str, client_id: str):
        if symbol in self.subscriptions:
            self.subscriptions[symbol].remove(client_id)

    def process_order(self, order: Order):
        order_book = self.get_order_book(order.symbol)
        if order_book:
            return order_book.add_order(order)
        return None, []

    def get_order_book_snapshot(self, symbol: str, levels: int = None):
        order_book = self.get_order_book(symbol)
        if order_book:
            if levels is None:
                levels = self.default_order_book_levels
            return order_book.get_order_book_snapshot(levels)
        return None

    def get_subscribed_clients(self, symbol: str) -> List[str]:
        return self.subscriptions.get(symbol, [])