from decimal import Decimal
from src.order import Order

def test_order_creation():
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    assert order.id == 1
    assert order.type == "limit"
    assert order.side == "buy"
    assert order.price == Decimal("100.50")
    assert order.quantity == Decimal("10")
    assert order.symbol == "SPY"
    assert order.filled_quantity == Decimal("0")
    assert order.timestamp > 0
    assert order.next_order is None
    assert order.prev_order is None
    assert order.parent_limit is None

def test_update_quantity():
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order.update_quantity("15")
    assert order.quantity == Decimal("15")

def test_is_filled():
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    assert not order.is_filled()
    order.filled_quantity = Decimal("10")
    assert order.is_filled()

def test_decimal_precision():
    order = Order(1, "limit", "buy", "100.12345", "10.98765", "SPY")
    assert order.price == Decimal("100.12345")
    assert order.quantity == Decimal("10.98765")