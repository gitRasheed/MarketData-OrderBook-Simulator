import pytest
from decimal import Decimal
from src.orderbook_manager import OrderBookManager
from src.order import Order

@pytest.fixture
def manager():
    manager = OrderBookManager()
    manager.create_order_book("AAPL", Decimal("0.01"))
    return manager

def test_subscribe_unsubscribe(manager):
    manager.subscribe("AAPL", "client1")
    assert manager.get_subscribed_clients("AAPL") == ["client1"]
    
    manager.subscribe("AAPL", "client2")
    assert manager.get_subscribed_clients("AAPL") == ["client1", "client2"]
    
    manager.unsubscribe("AAPL", "client1")
    assert manager.get_subscribed_clients("AAPL") == ["client2"]

def test_process_limit_order(manager):
    order = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    order_id, _ = manager.process_order(order)
    assert order_id is not None

def test_process_market_order(manager):
    # Add a limit order to the book first
    limit_order = Order("1", "limit", "sell", Decimal("150.00"), 100, "AAPL")
    manager.process_order(limit_order)

    # Now process a market order
    market_order = Order("2", "market", "buy", None, 50, "AAPL")
    order_id, filled_orders = manager.process_order(market_order)
    assert order_id is not None
    assert len(filled_orders) == 1
    assert filled_orders[0][1] == 50  # Quantity filled

def test_get_order_book_snapshot(manager):
    order = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    manager.process_order(order)
    
    snapshot = manager.get_order_book_snapshot("AAPL", 10)
    assert snapshot is not None
    assert len(snapshot["bids"]) == 1
    assert len(snapshot["asks"]) == 0
    assert snapshot["bids"][0] == (Decimal("150.00"), 100)

if __name__ == '__main__':
    pytest.main()