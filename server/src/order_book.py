from sortedcontainers import SortedDict
from typing import List, Tuple
from server.src.order import Order, OrderSide

class OrderBook:
    def __init__(self, instrument_id: str):
        self.instrument_id = instrument_id
        self.bids = SortedDict(lambda x: -x)
        self.asks = SortedDict()

    def add_order(self, order: Order):
        book = self.bids if order.side == OrderSide.BUY else self.asks
        if order.price not in book:
            book[order.price] = []
        book[order.price].append(order)
    
    def remove_order(self, order: Order):
        book = self.bids if order.side == OrderSide.BUY else self.asks
        book[order.price].remove(order)
        if not book[order.price]:
            del book[order.price]

    @property
    def best_bid(self) -> float:
        return next(iter(self.bids), None)

    @property
    def best_ask(self) -> float:
        return next(iter(self.asks), None)

    def get_price_levels(self, side: OrderSide, depth: int) -> List[Tuple[float, int]]:
        book = self.bids if side == OrderSide.BUY else self.asks
        levels = []
        for i, (price, orders) in enumerate(book.items()):
            if i >= depth:
                break
            total_quantity = sum(order.quantity for order in orders)
            levels.append((price, total_quantity))
        return levels

    def __str__(self) -> str:
        bid_str = "\n".join(f"{price}: {sum(order.quantity for order in orders)}" for price, orders in sorted(self.bids.items(), reverse=True))
        ask_str = "\n".join(f"{price}: {sum(order.quantity for order in orders)}" for price, orders in sorted(self.asks.items()))
        return f"OrderBook({self.instrument_id})\nBids:\n{bid_str}\nAsks:\n{ask_str}\n"