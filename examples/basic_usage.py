import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orderbook import Orderbook
from src.order import Order
from src.ticker import Ticker
import time
from src.exceptions import (
    InvalidOrderException,
    InsufficientLiquidityException,
    OrderNotFoundException,
    InvalidTickSizeException,
    InvalidQuantityException
)

def visualize_order_book(snapshot, depth=5):
    bids = snapshot['bids'][:depth]
    asks = snapshot['asks'][:depth]
    
    print("\nOrder Book Visualization:")
    print("-------------------------")
    print("     Price     |  Quantity")
    print("-------------------------")
    
    for price, quantity in reversed(asks):
        print(f"SELL {price:10.2f} | {quantity:10.2f}")
    
    print("-------------------------")
    
    for price, quantity in bids:
        print(f"BUY  {price:10.2f} | {quantity:10.2f}")
    
    print("-------------------------")

def add_order_safely(orderbook, order):
    try:
        orderbook.add_order(order)
        print(f"Order added successfully: {order.id}")
    except InvalidTickSizeException as e:
        print(f"Invalid tick size for order {order.id}: {e}")
    except InvalidQuantityException as e:
        print(f"Invalid quantity for order {order.id}: {e}")
    except InvalidOrderException as e:
        print(f"Invalid order {order.id}: {e}")

def main():
    spy_ticker = Ticker("SPY", "0.01")
    qqq_ticker = Ticker("QQQ", "0.01")

    spy_orderbook = Orderbook(spy_ticker)
    qqq_orderbook = Orderbook(qqq_ticker)

    # Add some limit orders for SPY
    spy_orders = [
        Order(1, "limit", "buy", "300.60", "10", "SPY"),
        Order(2, "limit", "buy", "300.40", "5", "SPY"),
        Order(3, "limit", "sell", "301.00", "7", "SPY"),
        Order(4, "limit", "sell", "301.25", "3", "SPY"),
        Order(5, "limit", "buy", "300.613", "5", "SPY")  # Invalid tick size
    ]

    for order in spy_orders:
        add_order_safely(spy_orderbook, order)

    # Add some limit orders for QQQ
    qqq_orders = [
        Order(1, "limit", "buy", "200.30", "10", "QQQ"),
        Order(2, "limit", "buy", "200.20", "5", "QQQ"),
        Order(3, "limit", "sell", "200.50", "7", "QQQ"),
        Order(4, "limit", "sell", "200.60", "3", "QQQ")
    ]

    for order in qqq_orders:
        add_order_safely(qqq_orderbook, order)

    print("SPY Order Book:")
    visualize_order_book(spy_orderbook.get_order_book_snapshot(5))

    print("\nQQQ Order Book:")
    visualize_order_book(qqq_orderbook.get_order_book_snapshot(5))

    # Demonstrate order modification
    try:
        spy_orderbook.modify_order(1, "300.65", "12")
        print("\nSPY Order Book after modification:")
        visualize_order_book(spy_orderbook.get_order_book_snapshot(5))
    except (OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException) as e:
        print(f"Error modifying order: {e}")

    # Demonstrate order cancellation
    try:
        spy_orderbook.cancel_order(2)
        print("\nSPY Order Book after cancellation:")
        visualize_order_book(spy_orderbook.get_order_book_snapshot(5))
    except OrderNotFoundException as e:
        print(f"Error cancelling order: {e}")

    # Demonstrate market order execution
    market_order = Order(6, "market", "buy", None, "5", "SPY")
    try:
        filled_orders = spy_orderbook.add_order(market_order)
        print("\nFilled orders:", filled_orders)
        print("\nSPY Order Book after market order execution:")
        visualize_order_book(spy_orderbook.get_order_book_snapshot(5))
    except InsufficientLiquidityException as e:
        print(f"Error executing market order: {e}")

if __name__ == "__main__":
    main()