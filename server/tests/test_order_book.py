import pytest
from datetime import datetime
from server.src.order import Order, OrderType, OrderSide
from server.src.order_book import OrderBook

@pytest.fixture
def order_book():
    return OrderBook("AAPL")

def test_order_book_creation(order_book):
    assert order_book.instrument_id == "AAPL"
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 0

def test_add_bid_order(order_book):
    order = Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0)
    order_book.add_order(order)
    assert len(order_book.bids) == 1
    assert order_book.bids[150.0][0] == order

def test_add_ask_order(order_book):
    order = Order("2", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=160.0)
    order_book.add_order(order)
    assert len(order_book.asks) == 1
    assert order_book.asks[160.0][0] == order

def test_best_bid_ask(order_book):
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=151.0))
    order_book.add_order(Order("3", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=160.0))
    order_book.add_order(Order("4", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=161.0))

    assert order_book.best_bid == 151.0
    assert order_book.best_ask == 160.0

def test_remove_order(order_book):
    order = Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0)
    order_book.add_order(order)
    assert len(order_book.bids) == 1

    order_book.remove_order(order)
    assert len(order_book.bids) == 0

def test_order_book_str(order_book):
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=160.0))
    
    expected_str = "OrderBook(AAPL)\nBids:\n150.0: 100\nAsks:\n160.0: 100\n"
    assert str(order_book) == expected_str
    
def test_get_price_levels(order_book):
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 50, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("3", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=151.0))
    order_book.add_order(Order("4", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=160.0))
    order_book.add_order(Order("5", "AAPL", 50, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=160.0))
    order_book.add_order(Order("6", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=161.0))

    bid_levels = order_book.get_price_levels(OrderSide.BUY, 5)
    ask_levels = order_book.get_price_levels(OrderSide.SELL, 5)

    assert bid_levels == [(151.0, 100), (150.0, 150)]
    assert ask_levels == [(160.0, 150), (161.0, 100)]