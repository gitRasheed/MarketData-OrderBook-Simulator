from decimal import Decimal
from src.order import Order

def test_order_creation():
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    assert order.id == 1
    assert order.type == "limit"
    assert order.side == "buy"
    assert order.price == Decimal("100.50")
    assert order.quantity == 10
    assert order.symbol == "SPY"
    assert order.filled_quantity == 0
    assert order.timestamp > 0
    assert order.next_order is None
    assert order.prev_order is None
    assert order.parent_level is None

def test_update_quantity():
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order.update_quantity(15)
    assert order.quantity == 15

def test_is_filled():
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    assert not order.is_filled()
    order.filled_quantity = 10
    assert order.is_filled()

def test_market_order():
    order = Order(1, "market", "buy", None, 10, "SPY")
    assert order.price is None
    assert order.quantity == 10