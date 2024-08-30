import pytest
from datetime import datetime
from server.src.order import Order, OrderType, OrderSide
from server.src.order_book import OrderBook
from server.src.order_matcher import OrderMatcher, Trade

@pytest.fixture
def order_book():
    return OrderBook("AAPL")

@pytest.fixture
def order_matcher(order_book):
    return OrderMatcher(order_book)

def test_match_market_buy_order(order_matcher, order_book):
    # Add some sell orders to the book
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 50, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=151.0))
    
    # Create a market buy order
    market_order = Order("3", "AAPL", 120, OrderSide.BUY, OrderType.MARKET, datetime.now())
    
    # Match the order
    trades = order_matcher.match(market_order)
    
    # Check the resulting trades
    assert len(trades) == 2
    assert trades[0].quantity == 100
    assert trades[0].price == 150.0
    assert trades[1].quantity == 20
    assert trades[1].price == 151.0
    
    # Check the order book state after matching
    assert len(order_book.asks) == 1
    assert order_book.asks[151.0][0].quantity == 30

def test_match_limit_buy_order(order_matcher, order_book):
    # Add some sell orders to the book
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 50, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=151.0))
    
    # Create a limit buy order
    limit_order = Order("3", "AAPL", 120, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=151.0)
    
    # Match the order
    trades = order_matcher.match(limit_order)
    
    # Check the resulting trades
    assert len(trades) == 2
    assert trades[0].quantity == 100
    assert trades[0].price == 150.0
    assert trades[1].quantity == 20
    assert trades[1].price == 151.0
    
    # Check the order book state after matching
    assert len(order_book.asks) == 1
    assert order_book.asks[151.0][0].quantity == 30
    assert len(order_book.bids) == 0

def test_match_limit_sell_order(order_matcher, order_book):
    # Add some buy orders to the book
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 50, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=149.0))
    
    # Create a limit sell order
    limit_order = Order("3", "AAPL", 120, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=149.0)
    
    # Match the order
    trades = order_matcher.match(limit_order)
    
    # Check the resulting trades
    assert len(trades) == 2
    assert trades[0].quantity == 100
    assert trades[0].price == 150.0
    assert trades[1].quantity == 20
    assert trades[1].price == 149.0
    
    # Check the order book state after matching
    assert len(order_book.bids) == 1
    assert order_book.bids[149.0][0].quantity == 30
    assert len(order_book.asks) == 0

def test_no_match(order_matcher, order_book):
    # Add a sell order to the book
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=150.0))
    
    # Create a buy order that doesn't match
    limit_order = Order("2", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=149.0)
    
    # Try to match the order
    trades = order_matcher.match(limit_order)
    
    # Check that no trades were made
    assert len(trades) == 0
    
    # Check that the new order was added to the book
    assert len(order_book.bids) == 1
    assert order_book.bids[149.0][0] == limit_order