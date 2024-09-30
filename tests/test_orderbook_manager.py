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
    order_id, filled_orders, version = manager.process_order(order)
    assert order_id == "1"
    assert len(filled_orders) == 0
    assert version == 1

def test_process_market_order(manager):
    # Add a limit order to the book first
    limit_order = Order("1", "limit", "sell", Decimal("150.00"), 100, "AAPL")
    manager.process_order(limit_order)

    # Now process a market order
    market_order = Order("2", "market", "buy", None, 50, "AAPL")
    order_id, filled_orders, version = manager.process_order(market_order)
    assert order_id == "2"
    assert len(filled_orders) == 1
    assert filled_orders[0][1] == 50  # Quantity filled
    assert version == 3  # 1 for limit order, 1 for market order, 1 for partial fill

def test_get_order_book_snapshot(manager):
    order = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    manager.process_order(order)
    
    snapshot, version = manager.get_order_book_snapshot("AAPL", 10)
    assert snapshot is not None
    assert len(snapshot["bids"]) == 1
    assert len(snapshot["asks"]) == 0
    assert snapshot["bids"][0] == (Decimal("150.00"), 100)
    assert version == 1

def test_get_order_book_update(manager):
    order1 = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    order2 = Order("2", "limit", "sell", Decimal("151.00"), 50, "AAPL")
    manager.process_order(order1)
    manager.process_order(order2)

    updates, version = manager.get_order_book_update("AAPL")
    print(f"Updates: {updates}")  # Add this line for debugging
    assert len(updates) == 2
    assert updates[0]['action'] == 'add' and updates[0]['side'] == 'buy'
    assert updates[1]['action'] == 'add' and updates[1]['side'] == 'sell'
    assert version == 2

    # Check that subsequent calls don't return the same updates
    new_updates, new_version = manager.get_order_book_update("AAPL")
    assert len(new_updates) == 0
    assert new_version == 2

    # Process another order
    order3 = Order("3", "limit", "buy", Decimal("152.00"), 75, "AAPL")
    manager.process_order(order3)

    # Check that we get only the new update
    latest_updates, latest_version = manager.get_order_book_update("AAPL")
    assert len(latest_updates) == 1
    assert latest_updates[0]['action'] == 'add' and latest_updates[0]['side'] == 'buy'
    assert latest_version == 3

def test_get_order_book_snapshot_clears_changes(manager):
    order = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    manager.process_order(order)
    
    snapshot, version = manager.get_order_book_snapshot("AAPL")
    assert snapshot is not None
    assert len(snapshot["bids"]) == 1
    assert version == 1
    
    updates, new_version = manager.get_order_book_update("AAPL")
    assert len(updates) == 1  # Changes should not be cleared after snapshot
    assert new_version == 1

def test_multiple_symbols(manager):
    manager.create_order_book("GOOGL", Decimal("0.01"))
    
    order1 = Order("1", "limit", "buy", Decimal("150.00"), 100, "AAPL")
    order2 = Order("2", "limit", "buy", Decimal("2500.00"), 10, "GOOGL")
    
    manager.process_order(order1)
    manager.process_order(order2)
    
    aapl_snapshot, aapl_version = manager.get_order_book_snapshot("AAPL")
    googl_snapshot, googl_version = manager.get_order_book_snapshot("GOOGL")
    
    assert len(aapl_snapshot["bids"]) == 1
    assert aapl_snapshot["bids"][0] == (Decimal("150.00"), 100)
    assert aapl_version == 1
    
    assert len(googl_snapshot["bids"]) == 1
    assert googl_snapshot["bids"][0] == (Decimal("2500.00"), 10)
    assert googl_version == 1

if __name__ == '__main__':
    pytest.main()