import pytest
from decimal import Decimal
import threading
import time
from src.orderbook import Orderbook
from src.order import Order
from src.ticker import Ticker
from src.exceptions import InvalidOrderException, InsufficientLiquidityException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

@pytest.fixture
def orderbook():
    ticker = Ticker("SPY", "0.01")
    return Orderbook(ticker)

def test_add_limit_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, filled_orders = orderbook.add_order(order)
    assert order_id == 1
    assert orderbook.orders[order_id] == order
    assert orderbook.bids.find(Decimal("100.50")).head_order == order
    assert len(filled_orders) == 0

def test_add_invalid_limit_order(orderbook):
    order = Order(1, "limit", "buy", "100.513", "10", "SPY")
    with pytest.raises(InvalidTickSizeException):
        orderbook.add_order(order)

def test_add_invalid_quantity_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "0", "SPY")
    with pytest.raises(InvalidQuantityException):
        orderbook.add_order(order)

def test_add_invalid_order_type(orderbook):
    order = Order(1, "invalid_type", "buy", "100.50", "10", "SPY")
    with pytest.raises(InvalidOrderException):
        orderbook.add_order(order)

def test_cancel_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, _ = orderbook.add_order(order)
    orderbook.cancel_order(order_id)
    assert order_id not in orderbook.orders
    assert orderbook.bids.find(Decimal("100.50")) is None

def test_cancel_nonexistent_order(orderbook):
    with pytest.raises(OrderNotFoundException):
        orderbook.cancel_order(999)