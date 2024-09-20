import pytest
from decimal import Decimal
from src.orderbook import Orderbook
from src.order import Order
from src.exceptions import InsufficientLiquidityException

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