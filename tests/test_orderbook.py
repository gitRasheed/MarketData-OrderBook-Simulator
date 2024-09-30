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
    assert orderbook.version == 1
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 1
    assert changes[0]['action'] == 'add'
    assert changes[0]['side'] == 'buy'
    assert changes[0]['price'] == Decimal("100.50")
    assert changes[0]['quantity'] == 10

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
    assert orderbook.version == 2
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 2
    assert changes[1]['action'] == 'delete'
    assert changes[1]['side'] == 'buy'
    assert changes[1]['price'] == Decimal("100.50")
    assert changes[1]['quantity'] == 10

def test_cancel_nonexistent_order(orderbook):
    with pytest.raises(OrderNotFoundException):
        orderbook.cancel_order(999)

def test_modify_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order_id, _ = orderbook.add_order(order)
    orderbook.modify_order(order_id, 15)
    assert orderbook.orders[order_id].quantity == 15
    assert orderbook.version == 2
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 2
    assert changes[1]['action'] == 'update'
    assert changes[1]['side'] == 'buy'
    assert changes[1]['price'] == Decimal("100.50")
    assert changes[1]['quantity'] == 15

def test_get_order_book_snapshot(orderbook):
    order1 = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order2 = Order(2, "limit", "sell", "100.60", "5", "SPY")
    orderbook.add_order(order1)
    orderbook.add_order(order2)
    
    snapshot = orderbook.get_order_book_snapshot(10)
    assert len(snapshot["bids"]) == 1
    assert len(snapshot["asks"]) == 1
    assert snapshot["bids"][0] == (Decimal("100.50"), 10)
    assert snapshot["asks"][0] == (Decimal("100.60"), 5)

def test_clear_changes(orderbook):
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    orderbook.add_order(order)
    assert orderbook.version == 1
    orderbook.clear_changes()
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 0

def test_get_updates_since(orderbook):
    order1 = Order(1, "limit", "buy", "100.50", "10", "SPY")
    order2 = Order(2, "limit", "sell", "100.60", "5", "SPY")
    orderbook.add_order(order1)
    orderbook.add_order(order2)
    
    updates = orderbook.get_updates_since(0)
    assert len(updates) == 2
    assert updates[0]['action'] == 'add' and updates[0]['side'] == 'buy'
    assert updates[1]['action'] == 'add' and updates[1]['side'] == 'sell'
    
    updates = orderbook.get_updates_since(1)
    assert len(updates) == 1
    assert updates[0]['action'] == 'add' and updates[0]['side'] == 'sell'

def test_current_version(orderbook):
    assert orderbook.current_version == 0
    
    order = Order(1, "limit", "buy", "100.50", "10", "SPY")
    orderbook.add_order(order)
    assert orderbook.current_version == 1
    
    orderbook.cancel_order(1)
    assert orderbook.current_version == 2

def test_process_market_order(orderbook):
    # Add a limit sell order
    sell_order = Order(1, "limit", "sell", "100.50", "10", "SPY")
    orderbook.add_order(sell_order)
    
    # Process a market buy order
    buy_order = Order(2, "market", "buy", None, "5", "SPY")
    order_id, filled_orders = orderbook.add_order(buy_order)
    
    assert order_id == 2
    assert len(filled_orders) == 1
    assert filled_orders[0] == (1, 5, Decimal("100.50"))
    assert orderbook.current_version == 3  # 1 for sell order, 1 for buy order, 1 for partial fill

if __name__ == '__main__':
    pytest.main()