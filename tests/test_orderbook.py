import pytest
from decimal import Decimal
from src.orderbook import Orderbook
from src.order import Order
from src.ticker import Ticker
from src.exceptions import InvalidOrderException, OrderNotFoundException, InvalidTickSizeException, InvalidQuantityException

@pytest.fixture
def orderbook():
    ticker = Ticker("SPY", "0.01")
    return Orderbook(ticker)

def test_add_limit_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order_id, filled_orders = orderbook.add_order(order)
    assert order_id == 1
    assert orderbook.orders[order_id] == order
    assert orderbook.price_levels[Decimal("100.50")].head_order == order
    assert len(filled_orders) == 0
    assert orderbook.version == 1
    assert orderbook.best_bid == Decimal("100.50")
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 1
    assert changes[0]['action'] == 'add'
    assert changes[0]['side'] == 'buy'
    assert changes[0]['price'] == Decimal("100.50")
    assert changes[0]['quantity'] == 10

def test_add_multiple_orders_same_price(orderbook):
    order1 = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order2 = Order(2, "limit", "buy", "100.50", 5, "SPY")
    orderbook.add_order(order1)
    orderbook.add_order(order2)
    
    price_level = orderbook.price_levels[Decimal("100.50")]
    assert price_level.order_count == 2
    assert price_level.total_volume == 15
    assert price_level.head_order == order1
    assert price_level.tail_order == order2

def test_add_market_order_with_no_opposing_orders(orderbook):
    buy_order = Order(1, "market", "buy", None, 15, "SPY")
    order_id, filled_orders = orderbook.add_order(buy_order)
    
    assert order_id == 1
    assert len(filled_orders) == 0
    assert orderbook.version == 1
    assert len(orderbook.orders) == 0
    assert len(orderbook.price_levels) == 0
    assert orderbook.best_bid is None
    assert orderbook.best_ask is None

def test_add_market_order_with_partial_fill(orderbook):
    sell_order = Order(1, "limit", "sell", "100.50", 10, "SPY")
    orderbook.add_order(sell_order)
    
    buy_order = Order(2, "market", "buy", None, 15, "SPY")
    order_id, filled_orders = orderbook.add_order(buy_order)
    
    assert order_id == 2
    assert len(filled_orders) == 1
    assert filled_orders[0] == (1, 10, Decimal("100.50"))
    assert orderbook.version == 3  # 1 for sell order, 1 for buy order, 1 for partial fill
    assert Decimal("100.50") not in orderbook.price_levels
    assert orderbook.best_ask is None
    assert Decimal("100.50") in orderbook.price_levels  # Remaining buy order at 100.50
    assert orderbook.best_bid == Decimal("100.50")
    
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 3
    assert changes[2]['action'] == 'add'
    assert changes[2]['side'] == 'buy'
    assert changes[2]['price'] == Decimal("100.50")
    assert changes[2]['quantity'] == 5  # 15 (original) - 10 (filled) = 5 (remaining)

def test_cancel_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order_id, _ = orderbook.add_order(order)
    orderbook.cancel_order(order_id)
    assert order_id not in orderbook.orders
    assert Decimal("100.50") not in orderbook.price_levels
    assert orderbook.version == 2
    assert orderbook.best_bid is None
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 2
    assert changes[1]['action'] == 'delete'
    assert changes[1]['side'] == 'buy'
    assert changes[1]['price'] == Decimal("100.50")
    assert changes[1]['quantity'] == 10

def test_modify_order(orderbook):
    order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order_id, _ = orderbook.add_order(order)
    orderbook.modify_order(order_id, 15)
    assert orderbook.orders[order_id].quantity == 15
    assert orderbook.price_levels[Decimal("100.50")].total_volume == 15
    assert orderbook.version == 2
    changes = orderbook.get_updates_since(0)
    assert len(changes) == 2
    assert changes[1]['action'] == 'update'
    assert changes[1]['side'] == 'buy'
    assert changes[1]['price'] == Decimal("100.50")
    assert changes[1]['quantity'] == 15

def test_get_order_book_snapshot(orderbook):
    order1 = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order2 = Order(2, "limit", "sell", "100.60", 5, "SPY")
    orderbook.add_order(order1)
    orderbook.add_order(order2)
    
    snapshot = orderbook.get_order_book_snapshot(10)
    assert len(snapshot["bids"]) == 1
    assert len(snapshot["asks"]) == 1
    assert snapshot["bids"][0] == (Decimal("100.50"), 10)
    assert snapshot["asks"][0] == (Decimal("100.60"), 5)

def test_best_bid_ask(orderbook):
    assert orderbook.best_bid_ask == (None, None)
    
    buy_order = Order(1, "limit", "buy", "100.50", 10, "SPY")
    orderbook.add_order(buy_order)
    assert orderbook.best_bid_ask == (Decimal("100.50"), None)
    
    sell_order = Order(2, "limit", "sell", "100.60", 5, "SPY")
    orderbook.add_order(sell_order)
    assert orderbook.best_bid_ask == (Decimal("100.50"), Decimal("100.60"))

def test_remove_price_level(orderbook):
    order1 = Order(1, "limit", "buy", "100.50", 10, "SPY")
    order2 = Order(2, "limit", "buy", "100.50", 5, "SPY")
    orderbook.add_order(order1)
    orderbook.add_order(order2)
    
    orderbook.cancel_order(1)
    assert Decimal("100.50") in orderbook.price_levels
    assert orderbook.best_bid == Decimal("100.50")
    
    orderbook.cancel_order(2)
    assert Decimal("100.50") not in orderbook.price_levels
    assert orderbook.best_bid is None

def test_process_limit_order_with_matching(orderbook):
    sell_order = Order(1, "limit", "sell", "100.50", 10, "SPY")
    orderbook.add_order(sell_order)
    
    buy_order = Order(2, "limit", "buy", "100.50", 5, "SPY")
    order_id, filled_orders = orderbook.add_order(buy_order)
    
    assert order_id == 2
    assert len(filled_orders) == 1
    assert filled_orders[0] == (1, 5, Decimal("100.50"))
    assert orderbook.price_levels[Decimal("100.50")].total_volume == 5
    assert orderbook.best_ask == Decimal("100.50")
    assert orderbook.best_bid is None

def test_market_order_conversion(orderbook):
    sell_order = Order(1, "limit", "sell", "100.50", 10, "SPY")
    orderbook.add_order(sell_order)

    buy_order = Order(2, "market", "buy", None, 5, "SPY")
    order_id, filled_orders = orderbook.add_order(buy_order)

    assert order_id == 2
    assert len(filled_orders) == 1
    assert filled_orders[0] == (1, 5, Decimal("100.50"))
    assert orderbook.price_levels[Decimal("100.50")].total_volume == 5
    assert orderbook.best_ask == Decimal("100.50")
    assert orderbook.best_bid is None
    assert buy_order.type == "limit"
    assert buy_order.price == Decimal("100.50")

if __name__ == '__main__':
    pytest.main()