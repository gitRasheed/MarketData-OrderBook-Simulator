import pytest
from datetime import datetime
from server.src.order import Order, OrderType, OrderSide
from server.src.order_book import OrderBook
from server.src.order_matcher import OrderMatcher
from server.src.market_data_service import MarketDataService, MarketDataUpdate, UpdateType

class MockClient:
    def __init__(self):
        self.updates = []

    def send_update(self, update):
        self.updates.append(update)

@pytest.fixture
def order_book():
    return OrderBook("AAPL")

@pytest.fixture
def order_matcher(order_book):
    return OrderMatcher(order_book)

@pytest.fixture
def market_data_service(order_book, order_matcher):
    return MarketDataService(order_book, order_matcher)

def test_subscribe_client(market_data_service):
    client = MockClient()
    market_data_service.subscribe(client, "AAPL")
    assert client in market_data_service.clients["AAPL"]

def test_unsubscribe_client(market_data_service):
    client = MockClient()
    market_data_service.subscribe(client, "AAPL")
    market_data_service.unsubscribe(client, "AAPL")
    assert client not in market_data_service.clients["AAPL"]

def test_send_snapshot(market_data_service, order_book):
    client = MockClient()
    market_data_service.subscribe(client, "AAPL")
    
    order_book.add_order(Order("1", "AAPL", 100, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=150.0))
    order_book.add_order(Order("2", "AAPL", 50, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=151.0))
    
    market_data_service.send_snapshot(client, "AAPL")
    
    assert len(client.updates) == 1
    assert client.updates[0].update_type == UpdateType.SNAPSHOT
    assert client.updates[0].instrument_id == "AAPL"
    assert len(client.updates[0].bids) == 1
    assert len(client.updates[0].asks) == 1

def test_process_order(market_data_service, order_book):
    client = MockClient()
    market_data_service.subscribe(client, "AAPL")
    
    order = Order("3", "AAPL", 75, OrderSide.BUY, OrderType.LIMIT, datetime.now(), price=152.0)
    market_data_service.process_order(order)
    
    assert len(client.updates) == 1
    assert client.updates[0].update_type == UpdateType.INCREMENT
    assert client.updates[0].instrument_id == "AAPL"
    assert len(client.updates[0].bids) == 1
    assert client.updates[0].bids[0] == (152.0, 75)

def test_process_trade(market_data_service, order_book, order_matcher):
    client = MockClient()
    market_data_service.subscribe(client, "AAPL")
    
    sell_order = Order("1", "AAPL", 100, OrderSide.SELL, OrderType.LIMIT, datetime.now(), price=150.0)
    order_book.add_order(sell_order)
    
    buy_order = Order("2", "AAPL", 50, OrderSide.BUY, OrderType.MARKET, datetime.now())
    trades = order_matcher.match(buy_order)
    
    market_data_service.process_trades(trades)
    
    assert len(client.updates) == 1
    assert client.updates[0].update_type == UpdateType.TRADE
    assert client.updates[0].instrument_id == "AAPL"
    assert client.updates[0].trades[0].price == 150.0
    assert client.updates[0].trades[0].quantity == 50