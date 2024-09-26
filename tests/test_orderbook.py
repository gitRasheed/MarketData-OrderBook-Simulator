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

def test_best_bid_ask(orderbook):
    orderbook.add_order(Order(1, "limit", "buy", "100.50", "10", "SPY"))
    orderbook.add_order(Order(2, "limit", "sell", "100.60", "10", "SPY"))
    best_bid, best_ask = orderbook.best_bid_ask
    assert best_bid == Decimal("100.50")
    assert best_ask == Decimal("100.60")

def test_process_market_order(orderbook):
    orderbook.add_order(Order(1, "limit", "sell", "100.50", "10", "SPY"))
    orderbook.add_order(Order(2, "limit", "sell", "100.60", "5", "SPY"))
    market_order = Order(3, "market", "buy", None, "15", "SPY")
    order_id, filled_orders = orderbook.add_order(market_order)
    assert order_id == 3
    assert len(filled_orders) == 2
    assert filled_orders[0] == (1, Decimal("10"), Decimal("100.50"))
    assert filled_orders[1] == (2, Decimal("5"), Decimal("100.60"))

def test_insufficient_liquidity(orderbook):
    orderbook.add_order(Order(1, "limit", "sell", "100.50", "10", "SPY"))
    market_order = Order(2, "market", "buy", None, "15", "SPY")
    with pytest.raises(InsufficientLiquidityException):
        orderbook.add_order(market_order)

def test_get_order_book_snapshot(orderbook):
    orderbook.add_order(Order(1, "limit", "buy", "100.50", "10", "SPY"))
    orderbook.add_order(Order(2, "limit", "buy", "100.40", "5", "SPY"))
    orderbook.add_order(Order(3, "limit", "sell", "100.60", "7", "SPY"))
    orderbook.add_order(Order(4, "limit", "sell", "100.70", "3", "SPY"))
    snapshot = orderbook.get_order_book_snapshot(2)
    assert snapshot == {
        "bids": [(Decimal("100.50"), Decimal("10")), (Decimal("100.40"), Decimal("5"))],
        "asks": [(Decimal("100.60"), Decimal("7")), (Decimal("100.70"), Decimal("3"))]
    }

def test_modify_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, _ = orderbook.add_order(order)
    
    orderbook.modify_order(order_id, "100.52", "12")
    
    modified_order = orderbook.orders[order_id]
    assert modified_order.price == Decimal("100.52")
    assert modified_order.quantity == Decimal("12")
    assert orderbook.bids.find(Decimal("100.50")) is None
    assert orderbook.bids.find(Decimal("100.52")).head_order == modified_order

def test_modify_order_invalid_price(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, _ = orderbook.add_order(order)
    with pytest.raises(InvalidTickSizeException):
        orderbook.modify_order(order_id, "100.513", "15")

def test_modify_order_invalid_quantity(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, _ = orderbook.add_order(order)
    with pytest.raises(InvalidQuantityException):
        orderbook.modify_order(order_id, "100.52", "0")

def test_modify_nonexistent_order(orderbook):
    with pytest.raises(OrderNotFoundException):
        orderbook.modify_order(999, "101.00", "15")

def test_partial_fill_limit_order(orderbook):
    orderbook.add_order(Order(1, "limit", "sell", "10.00", "10", "SPY"))
    
    order_id, filled_orders = orderbook.add_order(Order(2, "limit", "buy", "10.00", "20", "SPY"))
    
    assert len(filled_orders) == 1
    assert filled_orders[0] == (1, Decimal("10"), Decimal("10.00"))
    
    assert order_id in orderbook.orders
    remaining_order = orderbook.orders[order_id]
    assert remaining_order.quantity == Decimal("10")
    assert remaining_order.price == Decimal("10.00")
    
    assert orderbook.bids.find(Decimal("10.00")).head_order == remaining_order