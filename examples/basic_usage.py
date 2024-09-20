import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orderbook import Orderbook
from src.order import Order
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
    orderbook = Orderbook()
    orderbook.start_processing()

    # Add initial limit orders
    orderbook.order_queue.put(Order(1, "limit", "buy", "100.50", "10"))
    orderbook.order_queue.put(Order(2, "limit", "buy", "100.40", "5"))
    orderbook.order_queue.put(Order(3, "limit", "sell", "100.60", "7"))
    orderbook.order_queue.put(Order(4, "limit", "sell", "100.70", "3"))

    time.sleep(1)  # Allow time for order processing

    print("Initial Order Book:")
    visualize_order_book(orderbook.get_order_book_snapshot(5))

    # Process a market order
    market_order = Order(5, "market", "buy", None, "6")
    orderbook.order_queue.put(market_order)

    time.sleep(1)  # Allow time for order processing

    print("\nAfter Market Buy Order:")
    visualize_order_book(orderbook.get_order_book_snapshot(5))

    # Add more limit orders
    orderbook.order_queue.put(Order(6, "limit", "buy", "100.55", "8"))
    orderbook.order_queue.put(Order(7, "limit", "sell", "100.65", "4"))

    time.sleep(1)  # Allow time for order processing

    print("\nAfter Adding More Limit Orders:")
    visualize_order_book(orderbook.get_order_book_snapshot(5))

    # Cancel an order
    orderbook.cancel_order(2)  # Cancel the buy order at 100.40

    time.sleep(1)  # Allow time for order processing

    print("\nAfter Cancelling Buy Order at 100.40:")
    visualize_order_book(orderbook.get_order_book_snapshot(5))

    # Modify an order
    orderbook.modify_order(1, "100.52", "12")  # Modify the buy order at 100.50

    time.sleep(1)  # Allow time for order processing

    print("\nAfter Modifying Buy Order:")
    visualize_order_book(orderbook.get_order_book_snapshot(5))

    # Calculate and display bid-ask spread
    best_bid, best_ask = orderbook.get_best_bid_ask()
    spread = best_ask - best_bid
    print(f"\nBest Bid: {best_bid}, Best Ask: {best_ask}")
    print(f"Bid-Ask Spread: {spread}")

    orderbook.stop_processing()

if __name__ == "__main__":
    main()