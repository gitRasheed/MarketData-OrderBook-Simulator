import pytest
from decimal import Decimal
import threading
import time
from src.orderbook import Orderbook
from src.order import Order
from src.exceptions import InsufficientLiquidityException, OrderNotFoundException

@pytest.fixture
def orderbook():
    return Orderbook()

def test_add_limit_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10")
    order_id = orderbook.add_order(order)
    assert order_id == 1
    assert orderbook.orders[order_id] == order
    assert orderbook.bids[Decimal("100.50")][0] == order

def test_cancel_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10")
    order_id = orderbook.add_order(order)
    orderbook.cancel_order(order_id)
    assert order_id not in orderbook.orders
    assert Decimal("100.50") not in orderbook.bids

def test_get_best_bid_ask(orderbook):
    orderbook.add_order(Order(1, "limit", "buy", "100.50", "10"))
    orderbook.add_order(Order(2, "limit", "sell", "100.60", "10"))
    best_bid, best_ask = orderbook.get_best_bid_ask()
    assert best_bid == Decimal("100.50")
    assert best_ask == Decimal("100.60")

def test_process_market_order(orderbook):
    orderbook.add_order(Order(1, "limit", "sell", "100.50", "10"))
    orderbook.add_order(Order(2, "limit", "sell", "100.60", "5"))
    market_order = Order(3, "market", "buy", None, "15")
    filled_orders = orderbook.add_order(market_order)
    assert len(filled_orders) == 2
    assert filled_orders[0] == (1, Decimal("10"), Decimal("100.50"))
    assert filled_orders[1] == (2, Decimal("5"), Decimal("100.60"))

def test_insufficient_liquidity(orderbook):
    orderbook.add_order(Order(1, "limit", "sell", "100.50", "10"))
    market_order = Order(2, "market", "buy", None, "15")
    with pytest.raises(InsufficientLiquidityException):
        orderbook.add_order(market_order)

def test_get_order_book_snapshot(orderbook):
    orderbook.add_order(Order(1, "limit", "buy", "100.50", "10"))
    orderbook.add_order(Order(2, "limit", "buy", "100.40", "5"))
    orderbook.add_order(Order(3, "limit", "sell", "100.60", "7"))
    orderbook.add_order(Order(4, "limit", "sell", "100.70", "3"))
    snapshot = orderbook.get_order_book_snapshot(2)
    assert snapshot == {
        "bids": [(Decimal("100.50"), Decimal("10")), (Decimal("100.40"), Decimal("5"))],
        "asks": [(Decimal("100.60"), Decimal("7")), (Decimal("100.70"), Decimal("3"))]
    }

def test_modify_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10")
    order_id = orderbook.add_order(order)
    
    orderbook.modify_order(order_id, "101.00", "15")
    
    modified_order = orderbook.orders[order_id]
    assert modified_order.price == Decimal("101.00")
    assert modified_order.quantity == Decimal("15")
    assert Decimal("100.50") not in orderbook.bids
    assert orderbook.bids[Decimal("101.00")][0] == modified_order

def test_modify_nonexistent_order(orderbook):
    with pytest.raises(OrderNotFoundException):
        orderbook.modify_order(999, "101.00", "15")

def test_concurrent_order_processing(orderbook):
    orderbook.start_processing()

    def add_orders(side, price_range, quantity):
        for i in range(100):
            price = Decimal(str(price_range[0] + i * (price_range[1] - price_range[0]) / 100))
            order = Order(1000 + i, "limit", side, price, quantity)
            orderbook.order_queue.put(order)

    t1 = threading.Thread(target=add_orders, args=("buy", (100, 105), "10"))
    t2 = threading.Thread(target=add_orders, args=("sell", (105, 110), "10"))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    time.sleep(1)  # Allow time for order processing

    assert len(orderbook.bids) == 100
    assert len(orderbook.asks) == 100

    orderbook.stop_processing()