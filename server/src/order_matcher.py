from typing import List
from dataclasses import dataclass
from server.src.order import Order, OrderType, OrderSide
from server.src.order_book import OrderBook

@dataclass
class Trade:
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: int

class OrderMatcher:
    def __init__(self, order_book: OrderBook):
        self.order_book = order_book

    def match(self, incoming_order: Order) -> List[Trade]:
        trades = []
        
        if incoming_order.side == OrderSide.BUY:
            trades = self._match_buy_order(incoming_order)
        else:
            trades = self._match_sell_order(incoming_order)
        
        return trades

    def _match_buy_order(self, buy_order: Order) -> List[Trade]:
        trades = []
        remaining_quantity = buy_order.quantity

        for ask_price, ask_orders in sorted(self.order_book.asks.items()):
            if buy_order.type == OrderType.LIMIT and ask_price > buy_order.price:
                break

            ask_orders_to_remove = []
            for ask_order in ask_orders:
                if remaining_quantity == 0:
                    break

                trade_quantity = min(remaining_quantity, ask_order.quantity)
                trades.append(Trade(buy_order.order_id, ask_order.order_id, ask_price, trade_quantity))

                remaining_quantity -= trade_quantity
                ask_order.quantity -= trade_quantity

                if ask_order.quantity == 0:
                    ask_orders_to_remove.append(ask_order)

            for order in ask_orders_to_remove:
                ask_orders.remove(order)

            if not ask_orders:
                del self.order_book.asks[ask_price]

            if remaining_quantity == 0:
                break

        if remaining_quantity > 0 and buy_order.type == OrderType.LIMIT:
            buy_order.quantity = remaining_quantity
            self.order_book.add_order(buy_order)

        return trades

    def _match_sell_order(self, sell_order: Order) -> List[Trade]:
        trades = []
        remaining_quantity = sell_order.quantity

        for bid_price, bid_orders in sorted(self.order_book.bids.items(), reverse=True):
            if sell_order.type == OrderType.LIMIT and bid_price < sell_order.price:
                break

            bid_orders_to_remove = []
            for bid_order in bid_orders:
                if remaining_quantity == 0:
                    break

                trade_quantity = min(remaining_quantity, bid_order.quantity)
                trades.append(Trade(bid_order.order_id, sell_order.order_id, bid_price, trade_quantity))

                remaining_quantity -= trade_quantity
                bid_order.quantity -= trade_quantity

                if bid_order.quantity == 0:
                    bid_orders_to_remove.append(bid_order)

            for order in bid_orders_to_remove:
                bid_orders.remove(order)

            if not bid_orders:
                del self.order_book.bids[bid_price]

            if remaining_quantity == 0:
                break

        if remaining_quantity > 0 and sell_order.type == OrderType.LIMIT:
            sell_order.quantity = remaining_quantity
            self.order_book.add_order(sell_order)

        return trades