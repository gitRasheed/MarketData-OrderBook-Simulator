import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orderbook import Orderbook
from src.order import Order
from src.ticker import Ticker
import time

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

def main():
    spy_ticker = Ticker("SPY", "0.01")
    qqq_ticker = Ticker("QQQ", "0.01")

    spy_orderbook = Orderbook(spy_ticker)
    qqq_orderbook = Orderbook(qqq_ticker)

    spy_orderbook.start_processing()
    qqq_orderbook.start_processing()

    # Add some limit orders for SPY
    spy_orderbook.order_queue.put(Order(1, "limit", "buy", "300.60", "10", "SPY"))
    spy_orderbook.order_queue.put(Order(2, "limit", "buy", "300.40", "5", "SPY"))
    spy_orderbook.order_queue.put(Order(3, "limit", "sell", "301.00", "7", "SPY"))
    spy_orderbook.order_queue.put(Order(4, "limit", "sell", "301.25", "3", "SPY"))

    # Add some limit orders for QQQ
    qqq_orderbook.order_queue.put(Order(1, "limit", "buy", "200.30", "10", "QQQ"))
    qqq_orderbook.order_queue.put(Order(2, "limit", "buy", "200.20", "5", "QQQ"))
    qqq_orderbook.order_queue.put(Order(3, "limit", "sell", "200.50", "7", "QQQ"))
    qqq_orderbook.order_queue.put(Order(4, "limit", "sell", "200.60", "3", "QQQ"))

    # Try to add an invalid order
    try:
        spy_orderbook.order_queue.put(Order(5, "limit", "buy", "300.613", "5", "SPY"))
    except InvalidOrderException as e:
        print(f"Invalid order: {e}")

    time.sleep(1)  # Allow time for order processing

    print("SPY Order Book:")
    visualize_order_book(spy_orderbook.get_order_book_snapshot(5))

    print("\nQQQ Order Book:")
    visualize_order_book(qqq_orderbook.get_order_book_snapshot(5))

    spy_orderbook.stop_processing()
    qqq_orderbook.stop_processing()

if __name__ == "__main__":
    main()